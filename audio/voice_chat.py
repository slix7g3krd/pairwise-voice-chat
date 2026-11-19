"""第 53 批：组队语音里队友声音忽大忽小、电流麦、多人同时说话..."""


def adaptive_vad(level, noise_floor, threshold):
    """按噪声底返回自适应语音检测。

    VAD 门限不再是一个固定 dB 值，而是在当前噪声底之上叠加一段
    余量（``threshold``），噪声抬升时门限随之抬升，避免底噪被误判
    成说话或说话声被底噪淹没。
    """
    # 恰好落在门限上也算语音；带容差比较，避免 0.1 + 0.2 之类的
    # 二进制浮点误差把边界样本误判为静音。
    return level + 1e-9 >= noise_floor + threshold


def mix_gain(energies):
    """按能量归一化多人混音增益。

    每个讲话人的增益按其能量占总能量的比例分配，所有增益之和恒为
    1，因此无论有多少人同时说话，混音后的峰值都不会线性叠加而炸麦。
    能量全为 0 时退化为均分，保证不会除零。
    """
    gains = [max(0.0, float(e)) for e in energies]
    if not gains:
        return []
    total = sum(gains)
    if total <= 0.0:
        return [1.0 / len(gains)] * len(gains)
    return [g / total for g in gains]


def spatial_gain(distance, max_distance):
    """返回 3D 距离增益。

    ``distance`` 应是三维空间中的欧氏距离（而不是只算水平面的 2D
    距离），``max_distance`` 之外完全听不到。增益随距离线性衰减。
    """
    if max_distance <= 0.0:
        return 1.0 if distance <= 0.0 else 0.0
    remaining = 1.0 - max(0.0, float(distance)) / float(max_distance)
    return min(1.0, max(0.0, remaining))


def denoise_before_decode(enabled):
    """判断降噪是否在解码前执行。

    噪声抑制必须作用在解码前的编码域/比特流侧，解码后再降噪会把
    已经混入量化噪声的信号一起放大，产生电流麦。
    """
    return bool(enabled)


def plc_interpolate(last_frame, current_frame):
    """丢包时插值隐藏帧。

    用上一帧与当前帧之间的线性插值生成隐藏帧，而不是简单重复上一
    帧，避免丢包时出现机械的卡顿和能量跳变。标量与序列（list /
    tuple）都支持。
    """
    if last_frame is None:
        return current_frame
    try:
        last = list(last_frame)
        current = list(current_frame)
    except TypeError:
        return (float(last_frame) + float(current_frame)) / 2.0
    if len(last) != len(current):
        raise ValueError("frame sizes differ: %d != %d" % (len(last), len(current)))
    return [(float(a) + float(b)) / 2.0 for a, b in zip(last, current)]


def resample_ratio(source_rate, target_rate):
    """返回统一采样率比例。

    混音前把所有流统一到同一采样率：``target_rate / source_rate`` 即
    重采样器需要使用的比例。
    """
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("sample rates must be positive")
    return float(target_rate) / float(source_rate)


def talker_priority(energy, join_order):
    """按活跃度而非加入顺序排序讲话人。

    返回一个排序键，元组越大优先级越高：先比当前能量（越大越优先），
    能量相同时再比加入顺序（越早加入越优先，故取 ``-join_order``）。
    调用方按该键降序排序即可。
    """
    return (float(energy), -int(join_order))


def aec_reference(speaker, microphone):
    """返回回声消除参考信号。

    AEC 的参考信号必须是远端送来、由扬声器播放的信号，而不是麦克风
    采集到的近端信号；用麦克风做参考会把近端人声一起抵消掉。
    """
    return speaker


def split_voice_music(has_voice, has_music):
    """分流语音与音乐检测。

    语音活动与音乐能量分别判定，不能再把“没有语音”等同于“静音”；
    两者同时存在时按语音处理（音乐作为背景），两者都没有才视为静音。
    """
    if has_voice:
        return "voice"
    if has_music:
        return "music"
    return "silence"


def fixed_monitor_delay(buffer_size, sample_rate):
    """返回固定耳返延迟。

    耳返走固定的一整个缓冲区，延迟恒为 ``buffer_size / sample_rate``
    秒，不随网络抖动或动态缓冲调整而变化，避免耳返延迟忽长忽短。
    """
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if buffer_size < 0:
        raise ValueError("buffer_size must be non-negative")
    return float(buffer_size) / float(sample_rate)
