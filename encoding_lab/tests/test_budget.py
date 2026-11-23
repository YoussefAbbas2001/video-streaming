"""Bandwidth-budget planner: the rules of thumb behave the way the workshop teaches them."""
import math

from lab import budget as G

PI5 = G.COMPUTERS["Raspberry Pi 5 (software x264)"]
NANO = G.COMPUTERS["Jetson Nano 2GB (hardware NVENC)"]


def cam(pipeline="MJPEG → H.264 on ROV", res="1280×720", fps=30, **kw):
    return G.Camera("c", pipeline, res, fps, **kw)


def test_mjpeg_costs_several_times_more_bits_than_h264():
    assert G.video_mbps(cam("MJPEG passthrough")) > 5 * G.video_mbps(cam())


def test_off_camera_costs_nothing():
    c = cam(on=False)
    assert G.video_mbps(c) == 0 and G.encoder_cost(c, PI5)["cores"] == 0


def test_passthrough_needs_no_encoder_but_resize_trap_does():
    assert G.encoder_cost(cam("MJPEG passthrough"), PI5)["cores"] == 0
    trap = G.encoder_cost(cam("MJPEG resized on ROV", "640×360", camera_res="1920×1080"), PI5)
    assert trap["cores"] > 0.1                      # decode of the full 1080p picture dominates


def test_jetson_hardware_budget_matches_nvidia_figures():
    four_1080 = [cam(res="1920×1080") for _ in range(4)]
    p = G.plan(four_1080, NANO, 94, 0.7, 1, "RTP/UDP", 0)
    assert 0.95 < p.loads["Video encoder"] <= 1.0   # 4 × 1080p30 ≈ the whole encoder
    assert p.loads["CPU"] == 0


def test_pi5_two_720p_streams_fit_but_four_1080p_do_not():
    assert G.plan([cam(), cam()], PI5, 94, 0.7, 1, "RTP/UDP", 0).loads["CPU"] < 1
    assert G.plan([cam(res="1920×1080")] * 4, PI5, 94, 0.7, 1, "RTP/UDP", 0).status == "bad"


def test_h265_costs_more_cpu_and_fewer_bits():
    h264, h265 = cam(), cam("MJPEG → H.265 on ROV")
    assert G.encoder_cost(h265, PI5)["cores"] > 2 * G.encoder_cost(h264, PI5)["cores"]
    assert G.video_mbps(h265) < G.video_mbps(h264) * 1.4   # more bpp per pixel in our table, still close


def test_loss_hurts_long_gop_more_than_short_gop_and_mjpeg_least():
    short, long_, mj = cam(gop_s=0.5), cam(gop_s=5), cam("MJPEG passthrough")
    b = lambda c: G.loss_impact(c, G.video_mbps(c), 0.05, "RTP/UDP")["broken_pct"]
    assert b(long_) > b(short) > 0
    assert b(mj) < b(short)
    assert G.loss_impact(cam(), 2.0, 0, "RTP/UDP")["glitch_every_s"] == math.inf
    assert G.loss_impact(cam(), 2.0, 0.1, "HTTP/TCP")["broken_pct"] == 0


def test_keyframe_pileup_adds_delay_on_a_thin_tether():
    cams = [cam(res="1920×1080") for _ in range(6)]
    wire = [G.video_mbps(c) for c in cams]
    assert G.keyframe_pileup(cams, wire, 10, 1)["extra_ms"] > 0
    assert G.keyframe_pileup(cams, wire, 940, 1)["extra_ms"] == 0


def test_verdicts_follow_the_tether():
    cams = G.SCENARIOS["What we fly now: mjpg-streamer, USB cameras"][1]
    assert G.plan(cams, PI5, 94, 0.7, 1, "RTP/UDP", 0).status == "good"
    assert G.plan(cams, PI5, 10, 0.7, 1, "RTP/UDP", 0).status == "bad"


def test_suggestions_save_bits_and_prefer_fixes_the_encoder_can_take():
    cams = G.SCENARIOS["What we fly now: mjpg-streamer, USB cameras"][1]
    fixes = G.suggestions(cams, PI5, 20, 0.7, 1, "RTP/UDP", 0)
    assert fixes and all(f["Saves Mb/s"] > 0 for f in fixes)
    assert fixes[0]["fits_encoder"]
    assert any("H.264" in f["Change"] for f in fixes)


def test_every_scenario_plans_and_exports():
    for name, (pc, cams) in G.SCENARIOS.items():
        p = G.plan(cams, G.COMPUTERS[pc], 94, 0.7, 1, "MPEG-TS/UDP", 0.01)
        md = G.plan_markdown(p, cams, G.COMPUTERS[pc], 94, 0.7, 1, "MPEG-TS/UDP", 0.01, [])
        assert p.total > 0 and "| Camera |" in md, name
