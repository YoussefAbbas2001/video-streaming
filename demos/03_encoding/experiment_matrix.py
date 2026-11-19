#!/usr/bin/env python3
"""Demo 3: the encoding laboratory matrix (Video 3).

Encodes one clip five ways and measures size, bitrate, encode time, CPU, PSNR and SSIM:

    A  8 Mb/s · 30 fps · GOP 30      B  4 Mb/s · 30 fps · GOP 30      C  2 Mb/s · 30 fps · GOP 30
    D  2 Mb/s · 60 fps · GOP 60      E  2 Mb/s · 30 fps · GOP 120

Every run uses the low-latency recipe from the video: libx264 -preset ultrafast -tune zerolatency -bf 0, bitrate-capped.

    python experiment_matrix.py                        # synthetic underwater clip, 720p, 4 s
    python experiment_matrix.py --input dive.mp4 --height 1080 --seconds 6 --start 30
    python experiment_matrix.py --csv results.csv

Reuses the Encoding Lab engine (../../encoding_lab/lab/engine.py); needs FFmpeg with libx264.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "encoding_lab"))
from lab import engine as E  # noqa: E402

MATRIX = [  # name, Mb/s, fps, GOP in frames
    ("A", 8, 30, 30), ("B", 4, 30, 30), ("C", 2, 30, 30), ("D", 2, 60, 60), ("E", 2, 30, 120),
]
NOTICE = """
What to point at:
  A → B → C : halving the bitrate costs much less quality at first than you expect; look at fine texture and edges.
  C vs D    : the same 2 Mb/s spread over twice as many frames → each frame gets half the bits → lower quality,
              and about 1.5–2× the encoding work. High FPS is not free and does not mean low latency.
  C vs E    : does the long GOP buy any quality at the same capped bitrate? (On the synthetic clip: no, 43.2 vs 43.6 dB.)
              It does cost recovery time: after packet loss the picture can stay broken for up to 4 s
              (Encoding Lab → Packet loss tab).
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="your ROV footage (default: synthetic underwater clip)")
    ap.add_argument("--height", type=int, default=720, help="working height (16:9), e.g. 540, 720, 1080")
    ap.add_argument("--seconds", type=float, default=4)
    ap.add_argument("--start", type=float, default=0, help="start time in the input (s)")
    ap.add_argument("--workdir", type=Path, default=HERE / "out")
    ap.add_argument("--csv", type=Path)
    a = ap.parse_args()

    sources = {}
    rows = []
    print(f"FFmpeg: {E.ffmpeg_version()}")
    for name, mbps, fps, gop in MATRIX:
        if fps not in sources:
            print(f"preparing lossless {a.height}p{fps} reference …", flush=True)
            sources[fps] = E.prepare_source(a.workdir, a.input, a.seconds, a.height, fps, a.start)
        src = sources[fps]
        s = E.EncodeSettings(rate_mode="bitrate", bitrate_kbps=mbps * 1000, buffer_s=0.5, preset="ultrafast",
                             gop_s=gop / fps, bframes=0, zerolatency=True)
        r = E.encode(src, s)
        rows.append({"exp": name, "target_mbps": mbps, "fps": fps, "gop_frames": gop, "size_kB": round(r.size_bytes / 1e3),
                     "bitrate_mbps": round(r.bitrate_mbps, 2), "encode_s": round(r.encode_s, 2), "cpu_cores": round(r.cores, 2),
                     "encode_fps": round(r.encode_fps), "psnr_db": round(r.psnr, 2), "ssim": round(r.ssim, 4)})
        print(f"  {name} done", flush=True)

    head = f"\n{'exp':>3} {'target':>8} {'fps':>4} {'GOP':>4} {'size':>9} {'actual':>9} {'encode':>8} {'cores':>6} {'enc fps':>8} {'PSNR':>8} {'SSIM':>7}"
    print(head); print("-" * len(head))
    for r in rows:
        print(f"{r['exp']:>3} {r['target_mbps']:>6} M {r['fps']:>4} {r['gop_frames']:>4} {r['size_kB']:>6} kB {r['bitrate_mbps']:>6.2f} M "
              f"{r['encode_s']:>6.2f} s {r['cpu_cores']:>6.2f} {r['encode_fps']:>8} {r['psnr_db']:>6.2f} dB {r['ssim']:>7.4f}")
    print(NOTICE)
    print("Encode time and CPU describe THIS computer. Run it on the ROV's SBC for the numbers that matter.")
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        print(f"saved {a.csv}")


if __name__ == "__main__":
    main()
