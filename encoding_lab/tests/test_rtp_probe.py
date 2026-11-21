"""Tests for tools/rtp_probe.py (pure Python, no FFmpeg needed)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rtp_probe import RtpStats  # noqa: E402


def pkt(seq, ts=0, ssrc=0x1234, size=1200, pt=96):
    return struct.pack("!BBHII", 0x80, pt, seq & 0xFFFF, ts, ssrc) + bytes(size - 12)


def test_counts_gaps_as_loss():
    s = RtpStats()
    for i, seq in enumerate([10, 11, 12, 15, 16]):          # 13 and 14 missing
        s.feed(pkt(seq), now=i * 0.01)
    snap = s.snapshot(now=0.05)
    assert snap["lost_packets"] == 2 and snap["received_packets"] == 5
    assert abs(snap["loss_pct_total"] - 100 * 2 / 7) < 0.01


def test_sequence_wraparound_is_not_loss():
    s = RtpStats()
    for i, seq in enumerate([65533, 65534, 65535, 0, 1, 2]):
        s.feed(pkt(seq), now=i * 0.01)
    assert s.lost == 0


def test_late_packet_is_not_double_counted():
    s = RtpStats()
    for i, seq in enumerate([1, 2, 4, 3, 5]):               # 3 arrives late
        s.feed(pkt(seq), now=i * 0.01)
    assert s.lost == 0 and s.snapshot(now=0.05)["reordered"] == 1


def test_rtcp_and_other_streams_are_ignored():
    s = RtpStats()
    s.feed(pkt(100), now=0)
    assert not s.feed(pkt(5000, pt=200), now=0.01)          # RTCP sender report
    assert not s.feed(pkt(9000, ssrc=0x9999), now=0.02)     # another camera on the same port
    s.feed(pkt(101), now=0.03)
    assert s.lost == 0 and s.received == 2


def test_throughput_over_window():
    s = RtpStats(window_s=1.0)
    for i in range(100):                                    # 100 × 1250 B in 1 s = 1 Mb/s
        s.feed(pkt(i, size=1250), now=i * 0.01)
    assert abs(s.snapshot(now=0.99)["throughput_mbps"] - 1.0) < 0.02
