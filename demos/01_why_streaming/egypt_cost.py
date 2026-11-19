#!/usr/bin/env python3
"""What would video cost on an Egyptian home internet line, with and without compression?

Default price: WE entry-level home package, 100 GB for EGP 150 + 14 % VAT (from 1 Nov 2026) ≈ EGP 1.71 per GB.
Prices change often: pass --price with today's EGP-per-GB value (package price incl. VAT ÷ GB).

Examples:
    python egypt_cost.py
    python egypt_cost.py --width 1280 --height 720 --fps 30 --minutes 15 --cameras 8
    python egypt_cost.py --price 1.98 --line-mbps 70
"""
from __future__ import annotations

import argparse

DEFAULT_PRICE_EGP_PER_GB = 150 * 1.14 / 100   # WE entry package incl. 14 % VAT, Nov 2026
DEFAULT_QUOTA_GB = 100
BITS_PER_BYTE = 8
BYTES_PER_GB = 1e9


def gigabytes(bits_per_second: float, seconds: float) -> float:
    return bits_per_second * seconds / BITS_PER_BYTE / BYTES_PER_GB


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--minutes", type=float, default=60, help="duration of video")
    ap.add_argument("--cameras", type=int, default=1, help="number of identical cameras")
    ap.add_argument("--price", type=float, default=DEFAULT_PRICE_EGP_PER_GB, help="EGP per GB (default %(default).2f)")
    ap.add_argument("--quota", type=float, default=DEFAULT_QUOTA_GB, help="monthly package size in GB")
    ap.add_argument("--line-mbps", type=float, default=30, help="home line speed in Mb/s, for the 'can it even fit' check")
    a = ap.parse_args()

    pixels_per_s = a.width * a.height * a.fps * a.cameras
    seconds = a.minutes * 60
    rows = [
        ("Raw RGB, 24 bits/pixel", pixels_per_s * 24),
        ("Raw YUV 4:2:0, 12 bits/pixel", pixels_per_s * 12),
        ("MJPEG ≈ 1.4 bits/pixel (typical)", pixels_per_s * 1.4),
        ("H.264 at 5 Mb/s per camera", 5e6 * a.cameras),
        ("H.264 at 2 Mb/s per camera (ROV pilot)", 2e6 * a.cameras),
    ]
    print(f"\n{a.cameras} × {a.width}×{a.height} @ {a.fps:g} fps for {a.minutes:g} min · price EGP {a.price:.2f}/GB · "
          f"package {a.quota:g} GB · line {a.line_mbps:g} Mb/s\n")
    print(f"{'Format':42} {'Mb/s':>9} {'GB':>10} {'EGP':>11} {'package lasts':>15} {'× line speed':>13}")
    print("-" * 104)
    raw_cost = None
    for name, bps in rows:
        gb = gigabytes(bps, seconds)
        egp = gb * a.price
        lasts_min = a.quota / gigabytes(bps, 60)
        lasts = f"{lasts_min:,.1f} min" if lasts_min < 120 else f"{lasts_min / 60:,.1f} h"
        raw_cost = raw_cost or egp
        print(f"{name:42} {bps / 1e6:9,.1f} {gb:10,.2f} {egp:11,.2f} {lasts:>15} {bps / (a.line_mbps * 1e6):12,.1f}×")
    h264 = gigabytes(5e6 * a.cameras, seconds) * a.price
    print(f"\nRaw RGB costs {raw_cost / h264:,.0f}× more than H.264 at 5 Mb/s. Anything above 1.0× line speed cannot even be sent live.\n")


if __name__ == "__main__":
    main()
