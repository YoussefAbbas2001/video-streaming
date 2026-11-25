"""Pictures for the ROV experiments doc and slides (docs/experiments/img/).

  * g2g-photo.jpg  – what the E1 latency photo looks like: the ms clock and the video of the clock side by side
  * eye-test.jpg   – E24: an eye chart on a drifting, noisy underwater view, REALLY encoded with x264 at 4, 1 and 0.2 Mb/s

    python3 build/make_experiment_images.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "encoding_lab"))
sys.path.insert(0, str(ROOT / "build"))
from lab import engine as E  # noqa: E402
from make_diagnostic_images import FONT, MONO, label, read_frames, write_raw  # noqa: E402

OUT = ROOT / "docs" / "experiments" / "img"
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="exp_"))
W, H = 1280, 720


def g2g_photo() -> None:
    """The ms clock on the laptop, and the ROV's video of that clock, 126 ms older."""
    im = Image.new("RGB", (1600, 900), (12, 14, 18))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 40, 1560, 780), 26, fill=(28, 32, 40), outline=(70, 80, 95), width=6)    # laptop screen
    d.rectangle((70, 70, 790, 750), fill=(0, 0, 0))                                                    # the clock window
    big = ImageFont.truetype(MONO, 118)
    d.text((105, 330), "34:12.", font=big, fill=(255, 255, 255)); d.text((560, 330), "567", font=big, fill=(34, 211, 238))
    d.text((110, 110), "ms_clock.html", font=ImageFont.truetype(FONT, 30), fill=(150, 160, 175))
    # the video window: the same clock, seen by the camera through water, 126 ms earlier
    cam = Image.new("RGB", (720, 680), (8, 40, 48)); cd = ImageDraw.Draw(cam)
    cd.rectangle((60, 170, 660, 470), fill=(10, 12, 14))
    f2 = ImageFont.truetype(MONO, 96)
    cd.text((80, 270), "34:12.", font=f2, fill=(215, 225, 225)); cd.text((442, 270), "441", font=f2, fill=(60, 190, 210))
    cam = cam.rotate(-3, resample=Image.BICUBIC, fillcolor=(8, 40, 48)).filter(ImageFilter.GaussianBlur(2.2))
    arr = np.asarray(cam).astype(np.float32)
    arr = arr * 0.82 + np.array([10, 45, 55]) + np.random.default_rng(1).normal(0, 6, arr.shape)
    im.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), (810, 70))
    d.text((830, 85), "ROV pilot camera (video window)", font=ImageFont.truetype(FONT, 28), fill=(220, 230, 235))
    d.text((100, 805), "photo of both:   567 − 441  =  126 ms glass-to-glass", font=ImageFont.truetype(FONT, 46), fill=(245, 158, 11))
    im.resize((800, 450), Image.LANCZOS).save(OUT / "g2g-photo.jpg", quality=88)
    print("  g2g-photo")


def eye_test() -> None:
    """A laminated eye chart in murky water, encoded at three bitrates (real x264 encodes, same frame)."""
    src = TMP / "u.mkv"; E.synth_underwater(src, W, H, 30, 40)
    F = read_frames(src)
    card = Image.new("RGB", (560, 470), (238, 236, 226)); cd = ImageDraw.Draw(card)
    rows = [("E 7 F", 84), ("T 3 Z H", 44), ("P 8 K D 4", 24), ("V 5 N C 9 R", 14), ("A 2 M 6 S U", 10)]
    y = 18
    for txt, size in rows:
        f = ImageFont.truetype(FONT, size)
        w = cd.textlength(txt, font=f); cd.text(((560 - w) / 2, y), txt, font=f, fill=(15, 15, 15)); y += size + 26
    card = card.rotate(2, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
    mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rectangle((6, 6, card.size[0] - 6, card.size[1] - 6), fill=255)
    mask = mask.rotate(0)
    water = np.array([18, 92, 110]) / 255.0

    rng = np.random.default_rng(4)

    def frame(i):                                                       # an ROV never holds still: drift + sensor noise
        im = Image.fromarray((np.clip(F[i], 0, 1) * 255).astype(np.uint8))
        im.paste(card, (int(360 + 6 * np.sin(i / 4)), int(120 + 4 * np.cos(i / 5))), mask)
        a = np.asarray(im).astype(np.float32) / 255
        return a * 0.78 + water * 0.22 + rng.normal(0, 0.025, a.shape)  # a little turbidity and gain noise
    clip = TMP / "eye.mkv"; write_raw((frame(i) for i in range(40)), clip)
    panels = []
    for mbps in (4, 1, 0.2):
        out = TMP / f"eye_{mbps}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
                        "-b:v", f"{int(mbps * 1000)}k", "-maxrate", f"{int(mbps * 1000)}k", "-bufsize", f"{int(mbps * 500)}k", str(out)], check=True)
        fr = read_frames(out)[30]
        crop = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)).crop((340, 100, 960, 640)).resize((400, 348), Image.LANCZOS)
        panels.append((crop, mbps))
    sheet = Image.new("RGB", (1200, 348), (10, 22, 40))
    for k, (p, mbps) in enumerate(panels):
        sheet.paste(p, (k * 400, 0)); label(sheet, f"{mbps:g} Mb/s", (k * 400 + 14, 300), size=24)
    ImageDraw.Draw(sheet).line((400, 0, 400, 348), fill=(10, 22, 40), width=4); ImageDraw.Draw(sheet).line((800, 0, 800, 348), fill=(10, 22, 40), width=4)
    sheet.save(OUT / "eye-test.jpg", quality=88)
    print("  eye-test")


if __name__ == "__main__":
    g2g_photo()
    eye_test()
