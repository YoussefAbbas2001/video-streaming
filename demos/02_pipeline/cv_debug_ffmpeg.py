#!/usr/bin/env python3
"""CV debug stream: draw on frames in OpenCV, let FFmpeg encode and send them.

Replaces the PyPI `mjpeg-streamer` library. FFmpeg encodes each frame ONCE (that
library encodes once per viewer), sends exactly the frames you give it (no timer
duplicates), and can output RTP, a browser stream or a file.

    python3 cv_debug_ffmpeg.py                         # fake detections on a test pattern -> RTP 127.0.0.1:5610
    python3 cv_debug_ffmpeg.py --camera 0              # a real camera
    python3 cv_debug_ffmpeg.py --http 8090             # browser: http://<rov-ip>:8090/det.mjpg (one viewer)
    python3 cv_debug_ffmpeg.py --dest 192.168.1.100    # send to the topside PC

Topside (RTP): ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -flags low_delay det.sdp
Reading: docs/mjpeg-and-ffmpeg.md
"""
import argparse
import os
import subprocess
import time

import cv2
import numpy as np

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def ffmpeg_cmd(w: int, h: int, fps: float, quality: int, dest: str, port: int, http_port: int | None) -> list[str]:
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
           "-c:v", "mjpeg", "-q:v", str(quality), "-huffman", "default", "-pix_fmt", "yuvj420p"]
    if http_port:
        return cmd + ["-f", "mpjpeg", "-content_type", "multipart/x-mixed-replace;boundary=ffmpeg",
                      "-listen", "1", f"http://0.0.0.0:{http_port}/det.mjpg"]
    return cmd + ["-f", "rtp", "-sdp_file", "det.sdp", f"rtp://{dest}:{port}"]


def fake_frame(i: int, w: int, h: int) -> np.ndarray:
    """A moving 'pipe' on a blue-green background, standing in for a camera."""
    f = np.full((h, w, 3), (90, 70, 20), np.uint8)
    x = 40 + (i * 4) % (w - 240)
    cv2.rectangle(f, (x, h // 2 - 30), (x + 200, h // 2 + 30), (150, 150, 150), -1)
    return f


def detect(frame: np.ndarray, i: int) -> list[tuple[int, int, int, int, str, float]]:
    """Placeholder detector: replace with the team's model (YOLO etc.)."""
    h, w = frame.shape[:2]
    x = 40 + (i * 4) % (w - 240)
    return [(x - 6, h // 2 - 38, x + 206, h // 2 + 38, "pipe", 0.91)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--camera", type=int, default=None, help="OpenCV camera index (default: synthetic frames)")
    ap.add_argument("--size", default="640x360", help="debug stream size, WxH")
    ap.add_argument("--fps", type=float, default=10, help="the detector's REAL rate; FFmpeg sends exactly these frames")
    ap.add_argument("--quality", type=int, default=7, help="JPEG q 2..31 (lower = better, bigger)")
    ap.add_argument("--dest", default="127.0.0.1"); ap.add_argument("--port", type=int, default=5610)
    ap.add_argument("--http", type=int, default=None, metavar="PORT", help="serve to a browser instead of RTP")
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = forever)")
    a = ap.parse_args()
    w, h = map(int, a.size.split("x"))

    cap = cv2.VideoCapture(a.camera) if a.camera is not None else None
    ff = subprocess.Popen(ffmpeg_cmd(w, h, a.fps, a.quality, a.dest, a.port, a.http), stdin=subprocess.PIPE)
    target = f"http://0.0.0.0:{a.http}/det.mjpg" if a.http else f"rtp://{a.dest}:{a.port} (det.sdp)"
    print(f"CV debug stream {w}x{h} @ {a.fps} fps -> {target}")

    t0, i = time.time(), 0
    try:
        while not a.seconds or time.time() - t0 < a.seconds:
            if cap is not None:
                ok, frame = cap.read()
                if not ok:
                    break
                frame = cv2.resize(frame, (w, h))
            else:
                frame = fake_frame(i, w, h)
                time.sleep(1 / a.fps)            # a real detector sets the pace itself
            for x1, y1, x2, y2, label, conf in detect(frame, i):
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            ff.stdin.write(frame.tobytes())       # one encode per frame, whatever the number of viewers
            i += 1
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        try:
            ff.stdin.close()
        except BrokenPipeError:
            pass
        ff.wait()
        if cap is not None:
            cap.release()
        print(f"sent {i} frames")


if __name__ == "__main__":
    main()
