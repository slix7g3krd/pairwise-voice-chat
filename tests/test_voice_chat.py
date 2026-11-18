import pytest
from audio import voice_chat as mod

CASES = [
    ("vad_true", "m.adaptive_vad(0.5, 0.1, 0.2) is True"),
    ("vad_false", "m.adaptive_vad(0.2, 0.1, 0.2) is False"),
    ("mix_sum", "sum(m.mix_gain([2.0, 2.0])) == approx(1.0)"),
    ("mix_half", "m.mix_gain([2.0, 2.0])[0] == approx(0.5)"),
    ("spatial_near", "m.spatial_gain(0.0, 10.0) == approx(1.0)"),
    ("spatial_far", "m.spatial_gain(10.0, 10.0) == approx(0.0)"),
    ("denoise_true", "m.denoise_before_decode(True) is True"),
    ("plc_mid", "m.plc_interpolate(0.0, 2.0) == approx(1.0)"),
    ("ratio_double", "m.resample_ratio(16000, 32000) == approx(2.0)"),
    ("priority_energy", "m.talker_priority(1.0, 2)[0] < m.talker_priority(2.0, 2)[0]"),
    ("aec_speaker", "m.aec_reference('speaker', 'mic') == 'speaker'"),
    ("split_voice", "m.split_voice_music(True, False) == 'voice'"),
    ("split_music", "m.split_voice_music(False, True) == 'music'"),
    ("monitor_half", "m.fixed_monitor_delay(480, 48000) == approx(0.01)"),
    ("vad_equal", "m.adaptive_vad(0.3, 0.1, 0.2) is True")
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})
