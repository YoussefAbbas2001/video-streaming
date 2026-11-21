#!/usr/bin/env python3
"""RTP stream probe: the two numbers every pilot GUI should show, per camera.

* Throughput  — bits received per second on this stream (what the tether is really carrying).
* Loss        — RTP packets that never arrived, from gaps in the 16-bit sequence numbers
                (Ethernet drops corrupted frames whole, so "bit loss" shows up as packet loss).
Plus interarrival jitter (RFC 3550 §6.4.1), which tells you how big the receiver's jitter buffer must be.

Standalone:   python3 rtp_probe.py --port 5600              # one line per second
              python3 rtp_probe.py --port 5600 --forward 5700  # probe AND pass the stream on to the player
Import:       from rtp_probe import RtpStats   →   stats.feed(datagram, now); stats.snapshot()

Pure standard library, no dependencies.
"""
from __future__ import annotations

import argparse
import json
import socket
import struct
import time
from collections import deque
from dataclasses import dataclass, field

RTP_CLOCK = {96: 90000, 26: 90000, 33: 90000}     # video payloads use a 90 kHz clock
SEQ_MOD = 1 << 16


@dataclass
class RtpStats:
    """Thread-unsafe accumulator: feed it every UDP datagram of one RTP stream (one SSRC)."""
    window_s: float = 1.0
    clock_hz: int = 90000
    received: int = 0
    lost: int = 0
    bytes_total: int = 0
    jitter_ts: float = 0.0                 # RFC 3550 jitter in RTP timestamp units
    _ext_max: int | None = None            # highest extended sequence number seen
    _base: int | None = None
    _seen_late: int = 0
    _transit: float | None = None
    ssrc: int | None = None                # the first stream seen; other streams on the port are ignored
    _win: deque = field(default_factory=deque)     # (arrival time, bytes, lost so far, received so far)

    def feed(self, datagram: bytes, now: float | None = None) -> bool:
        """Account for one datagram. Returns False if it is not RTP (or is another stream / RTCP)."""
        if len(datagram) < 12 or datagram[0] >> 6 != 2:
            return False
        if 200 <= datagram[1] <= 207:             # RTCP (sender/receiver reports) shares the version bits
            return False
        seq, ts, ssrc = struct.unpack_from("!HII", datagram, 2)
        if self.ssrc is None:
            self.ssrc = ssrc
        elif ssrc != self.ssrc:
            return False
        now = time.monotonic() if now is None else now
        if self._ext_max is None:
            self._ext_max = self._base = seq
        else:
            # extend the 16-bit sequence number across wrap-around
            delta = (seq - (self._ext_max & 0xFFFF)) % SEQ_MOD
            if delta < SEQ_MOD // 2:              # newer packet
                if delta > 1:
                    self.lost += delta - 1        # the gap: packets that should have come in between
                self._ext_max += delta
            else:                                 # older packet arriving late (reordered): it was counted as lost
                self.lost = max(0, self.lost - 1)
                self._seen_late += 1
        self.received += 1
        self.bytes_total += len(datagram)
        # interarrival jitter, RFC 3550: J += (|D| - J) / 16
        arrival_ts = now * self.clock_hz
        transit = arrival_ts - ts
        if self._transit is not None:
            d = abs(transit - self._transit)
            self.jitter_ts += (d - self.jitter_ts) / 16
        self._transit = transit
        self._win.append((now, len(datagram), self.lost, self.received))
        while self._win and now - self._win[0][0] > self.window_s:
            self._win.popleft()
        return True

    def snapshot(self, now: float | None = None) -> dict:
        now = time.monotonic() if now is None else now
        while self._win and now - self._win[0][0] > self.window_s:
            self._win.popleft()
        w = list(self._win)
        bits = sum(b for _, b, _, _ in w) * 8
        if len(w) >= 2:
            lost_w = w[-1][2] - w[0][2]
            recv_w = w[-1][3] - w[0][3] + 1
        else:
            lost_w, recv_w = 0, len(w)
        expected = self.received + self.lost
        return {
            "throughput_mbps": round(bits / self.window_s / 1e6, 3),
            "loss_pct_window": round(100 * lost_w / max(lost_w + recv_w, 1), 3),
            "loss_pct_total": round(100 * self.lost / max(expected, 1), 3),
            "lost_packets": self.lost, "received_packets": self.received,
            "jitter_ms": round(1000 * self.jitter_ts / self.clock_hz, 2),
            "reordered": self._seen_late,
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=5600, help="UDP port the RTP stream arrives on")
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--forward", type=int, help="also re-send every datagram to 127.0.0.1:PORT (for the real player)")
    ap.add_argument("--json", action="store_true", help="one JSON object per second (for a GUI or a log)")
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = run until Ctrl+C)")
    a = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
    sock.bind((a.bind, a.port)); sock.settimeout(0.2)
    fwd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if a.forward else None
    st = RtpStats()
    t0 = last = time.monotonic()
    try:
        while not a.seconds or time.monotonic() - t0 < a.seconds:
            try:
                data = sock.recv(65536)
                st.feed(data)
                if fwd:
                    fwd.sendto(data, ("127.0.0.1", a.forward))
            except socket.timeout:
                pass
            now = time.monotonic()
            if now - last >= 1.0:
                last = now
                s = st.snapshot(now)
                if a.json:
                    print(json.dumps(s), flush=True)
                else:
                    print(f"{s['throughput_mbps']:7.2f} Mb/s · loss {s['loss_pct_window']:5.2f} % (total {s['loss_pct_total']:.2f} %, "
                          f"{s['lost_packets']} pkts) · jitter {s['jitter_ms']:.1f} ms", flush=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
