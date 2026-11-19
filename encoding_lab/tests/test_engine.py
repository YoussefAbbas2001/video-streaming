"""Quick self-test of the Encoding Lab engine (needs ffmpeg with libx264). Run: pytest -q tests"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import engine as E  # noqa: E402


@pytest.fixture(scope="module")
def src(tmp_path_factory):
    return E.prepare_source(tmp_path_factory.mktemp("lab"), None, seconds=2, height=360, fps=30)


def test_source_is_prepared(src):
    assert (src.width, src.height, src.frames) == (640, 360, 60)


def test_lower_crf_means_bigger_and_better(src):
    hi = E.encode(src, E.EncodeSettings(quality=20))
    lo = E.encode(src, E.EncodeSettings(quality=32))
    assert hi.size_bytes > lo.size_bytes
    assert hi.ssim > lo.ssim and hi.psnr > lo.psnr


def test_bitrate_cap_is_respected(src):
    r = E.encode(src, E.EncodeSettings(rate_mode="bitrate", bitrate_kbps=500, buffer_s=0.5))
    assert r.bitrate_mbps < 0.5 * 1.25


def test_gop_controls_keyframes(src):
    r = E.encode(src, E.EncodeSettings(gop_s=0.5, zerolatency=True))
    types = E.frame_table(r.path).type.value_counts()
    assert types.get("I", 0) >= 4 and types.get("B", 0) == 0


def test_packet_loss_recovers_faster_with_short_gop(src):
    short = E.packet_loss_experiment(src, "GOP 0.5 s", loss_kb=6, loss_at_s=0.6, bitrate_kbps=1000)
    long_ = E.packet_loss_experiment(src, "GOP 5 s", loss_kb=6, loss_at_s=0.6, bitrate_kbps=1000)
    assert short["damaged_s"] <= long_["damaged_s"]


# ----------------------------------------------------------------------------- benchmarking (lab/bench.py)
from lab import bench as B  # noqa: E402


def test_capacity_is_consistent(src):
    c = B.encoder_capacity(src, E.EncodeSettings(preset="ultrafast", zerolatency=True))
    assert c.one_core_fps > 0 and c.ms_per_frame > 0
    assert abs(c.streams_per_core - (1000 / c.ms_per_frame) / c.fps) < 1e-6
    assert c.streams_machine > 0


def test_low_latency_holds_no_frames(src):
    assert B.encoder_hold(src, E.EncodeSettings(preset="veryfast", zerolatency=True))["frames"] == 0
    assert B.encoder_hold(src, E.EncodeSettings(preset="medium", bframes=3))["frames"] > 5


def test_latency_budget_adds_up():
    b = B.latency_budget(30, 0, 5, 10_000, 40_000, 100, 1, 50, 2, 60)
    tot = sum(x["typical_ms"] for x in b)
    assert 80 < tot < 130 and all(x["worst_ms"] >= x["typical_ms"] for x in b)


def test_decode_and_report(src):
    r = E.encode(src, E.EncodeSettings(preset="veryfast", zerolatency=True))
    d = B.decode_speed(r.path)
    assert d["frames"] == src.frames and d["fps"] > 0
    md = B.report_markdown(B.system_info(), [], [], None, None, d, None)
    assert "## This computer" in md and "Decode speed" in md


def test_sysmon_sample():
    m = B.SysMon()
    s = m.sample()
    assert 0 <= s["cpu_total"] <= 100 and len(s["cores"]) >= 1
