"""Pictures for the encoder slides: what each step and each knob does to a real picture.

Every panel is a REAL encode with FFmpeg (x264, x265, SVT-AV1, MJPEG), decoded and cropped, with its measured
bitrate and SSIM printed on it. By default the source is the Encoding Lab's synthetic underwater clip; give real
footage to make the same pictures from it (real ROV footage is better):

    python3 build/make_encoder_images.py                          # synthetic underwater clip
    python3 build/make_encoder_images.py --source assets/dive.mp4 --start 12   # 3 s of your own footage

Writes docs/streaming/img/encoder/*.jpg and measurements.json (≈ 1–2 min).
"""
from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "encoding_lab"))
from lab import engine as E  # noqa: E402

OUT = ROOT / "docs" / "streaming" / "img" / "encoder"
W, H, FPS, SECONDS = 1280, 720, 30, 3.0
PANEL_W = 400                                   # every crop is shown at this width
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MEAS: dict[str, dict] = {}
SYNTHETIC = True
ENCODERS = subprocess.run([E.FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout


def ff(*args: str) -> float:
    """Run FFmpeg and return the CPU seconds it used."""
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    subprocess.run([E.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)


def frame(path: Path, t: float) -> np.ndarray:
    raw = subprocess.run([E.FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", "-vf", f"scale={W}:{H}:flags=bicubic",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def frame_n(path: Path, n: int) -> np.ndarray:
    """Decoded frame number n (counted from the first decoded frame, whatever the stream's start time)."""
    raw = subprocess.run([E.FFMPEG, "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{n}),scale={W}:{H}:flags=bicubic", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def measure(path: Path, src) -> dict:
    q = E.quality(path, src)
    return {"mbps": path.stat().st_size * 8 / SECONDS / 1e6, "ssim": q.get("ssim"), "psnr": q.get("psnr")}


def crop(a: np.ndarray, box) -> Image.Image:
    x, y, w, h = box
    im = Image.fromarray(a[y:y + h, x:x + w])
    return im.resize((PANEL_W, round(PANEL_W * h / w)), Image.NEAREST if w < 200 else Image.LANCZOS)


PANELS = ROOT / "out" / "encoder_panels"          # the same crops without text, for the deck (labels are native slide text)


def strip(name: str, panels: list[tuple[Image.Image, str, str]], gap: int = 12) -> None:
    """Panels side by side; each gets a title on top and a measurement line below.
    Also saves each crop and its labels to out/encoder_panels/ for build/new_slides_encoder.js."""
    PANELS.mkdir(parents=True, exist_ok=True)
    index = json.loads((PANELS / "panels.json").read_text()) if (PANELS / "panels.json").exists() else {}
    index[name] = []
    for k, (im, title, sub) in enumerate(panels):
        im.save(PANELS / f"{name}-{k}.jpg", quality=92)
        index[name].append({"file": f"{name}-{k}.jpg", "title": title, "sub": sub, "w": im.width, "h": im.height})
    (PANELS / "panels.json").write_text(json.dumps(index, indent=1))
    title_f, sub_f = ImageFont.truetype(FONT, 22), ImageFont.truetype(FONT_R, 19)
    ph = max(p.height for p, _, _ in panels)
    out = Image.new("RGB", (len(panels) * PANEL_W + (len(panels) - 1) * gap, ph + 76), "white")
    d = ImageDraw.Draw(out)
    for k, (im, title, sub) in enumerate(panels):
        x = k * (PANEL_W + gap)
        d.text((x + PANEL_W / 2, 4), title, font=title_f, fill="#1d1d1f", anchor="ma")
        out.paste(im, (x, 34))
        d.text((x + PANEL_W / 2, 34 + ph + 8), sub, font=sub_f, fill="#52514e", anchor="ma")
    out.save(OUT / f"{name}.jpg", quality=90)
    print("wrote", name)


def fmt(m: dict) -> str:
    return f"{m['mbps']:.2f} Mb/s · SSIM {m['ssim']:.3f}"


# ------------------------------------------------------------------------------------------------ explanation pictures
def hud_draw(d: ImageDraw.ImageDraw, x0: int, y0: int) -> None:
    """A pilot HUD of 1-px lines on odd rows and columns (so each line shares its 2×2 colour block with water)."""
    d.line([(x0, y0 + 61), (x0 + 240, y0 + 61)], fill=(255, 0, 0), width=1)
    d.line([(x0 + 121, y0), (x0 + 121, y0 + 120)], fill=(255, 0, 0), width=1)
    d.text((x0 + 8, y0 + 70), "DEPTH 12.4 m", font=ImageFont.truetype(FONT_R, 13), fill=(255, 40, 40))


def chroma_bleed(src, tmp: Path) -> None:
    """A 1-pixel HUD drawn INTO the video, encoded 4:4:4 vs 4:2:0, and the same HUD drawn after decoding."""
    base = frame(src.mkv, 1.5)
    hud = Image.fromarray(base.copy()); d = ImageDraw.Draw(hud)
    x0, y0 = 520, 250
    hud_draw(d, x0, y0)
    still = tmp / "hud.png"; hud.save(still)
    out = {}
    for mode, args in (("444", ["-profile:v", "high444", "-pix_fmt", "yuv444p"]), ("420", ["-pix_fmt", "yuv420p"])):
        p = tmp / f"hud_{mode}.mp4"
        ff("-i", str(still), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", *args, str(p))
        out[mode] = frame(p, 0)
    clean = tmp / "clean_420.mp4"
    ff("-ss", "1.5", "-i", str(src.mkv), "-frames:v", "1", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(clean))
    after = Image.fromarray(frame(clean, 0)); d2 = ImageDraw.Draw(after)       # overlay drawn on the pilot laptop, after decoding
    hud_draw(d2, x0, y0)
    box = (x0 + 100, y0 + 46, 40, 28)              # where the 1-px cross meets: ×10 zoom
    strip("chroma-bleed", [(crop(out["444"], box), "4:4:4 (full colour)", "each 1-px line stays pure red"),
                           (crop(out["420"], box), "4:2:0 (what everyone sends)", "red spread over 2 px, half as strong"),
                           (crop(np.asarray(after), box), "4:2:0 + overlay after decoding", "draw the HUD on the laptop instead")])


def motion_search(src) -> None:
    """Block matching between two consecutive frames: vectors, and what is left to send with and without them."""
    g = lambda a: a.astype(float) @ np.array([0.299, 0.587, 0.114])
    prev, cur = g(frame(src.mkv, 1.0)), g(frame(src.mkv, 1.0 + 1 / FPS))
    y0, x0, h, w, b, r = 280, 420, 192, 320, 16, 6
    c = cur[y0:y0 + h, x0:x0 + w]
    nby, nbx = h // b, w // b
    best = np.full((nby, nbx), np.inf); vy = np.zeros((nby, nbx), int); vx = np.zeros((nby, nbx), int)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            p = prev[y0 + dy:y0 + dy + h, x0 + dx:x0 + dx + w]
            err = np.abs(c - p).reshape(nby, b, nbx, b).sum(axis=(1, 3))
            better = err < best; best[better], vy[better], vx[better] = err[better], dy, dx
    pred = np.zeros_like(c)
    for by in range(nby):
        for bx in range(nbx):
            yy, xx = y0 + by * b + vy[by, bx], x0 + bx * b + vx[by, bx]
            pred[by * b:(by + 1) * b, bx * b:(bx + 1) * b] = prev[yy:yy + b, xx:xx + b]
    plain, resid = np.abs(c - prev[y0:y0 + h, x0:x0 + w]), np.abs(c - pred)
    heat = lambda a: (np.stack([np.clip(a * 8, 0, 255), np.clip(a * 3, 0, 255), np.clip(a * 1.2, 0, 255)], -1)).astype(np.uint8)
    arrows = Image.fromarray(np.stack([c] * 3, -1).astype(np.uint8)).resize((PANEL_W, round(PANEL_W * h / w)), Image.LANCZOS)
    d = ImageDraw.Draw(arrows); s = PANEL_W / w
    for by in range(nby):
        for bx in range(nbx):
            cx, cy = (bx * b + b / 2) * s, (by * b + b / 2) * s
            d.line([(cx, cy), (cx + vx[by, bx] * s * 2.5, cy + vy[by, bx] * s * 2.5)], fill=(255, 40, 40), width=2)
            d.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=(255, 40, 40))
    MEAS["motion"] = {"error_without": float(plain.mean()), "error_with": float(resid.mean())}
    strip("motion-search", [(arrows, "current frame + motion vectors", f"{b}×{b} blocks, search ±{r} px"),
                            (Image.fromarray(heat(plain)).resize(arrows.size), "left to send: no search", f"mean error {plain.mean():.1f}"),
                            (Image.fromarray(heat(resid)).resize(arrows.size), "left to send: after search", f"mean error {resid.mean():.1f} ({1 - resid.mean() / plain.mean():.0%} less)")])


# ------------------------------------------------------------------------------------------------ one knob at a time
BOX = (470, 290, 340, 230)                       # pipe edge, seams and marine snow


def encode(src, tmp: Path, tag: str, args: list[str], ext: str = "mp4", pix: str = "yuv420p", vf: str | None = None) -> tuple[Path, float]:
    p = tmp / f"{tag}.{ext}"
    cpu = ff("-i", str(src.mkv), *(["-vf", vf] if vf else []), *args, "-pix_fmt", pix, "-an", str(p))
    return p, cpu


def crf_ladder(src, tmp: Path) -> None:
    panels = []
    for crf in (18, 28, 38, 46):
        p, _ = encode(src, tmp, f"crf{crf}", ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf)])
        m = measure(p, src); MEAS[f"crf{crf}"] = m
        panels.append((crop(frame(p, 1.5), BOX), f"CRF {crf}", fmt(m)))
    strip("knob-crf", panels)


def codecs_same_bitrate(src, tmp: Path, kbps: int = 150) -> None:
    cap = [f"-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps}k"]
    jobs = [("H.264", "libx264", ["-c:v", "libx264", "-preset", "veryfast", *cap], "mp4", "yuv420p"),
            ("H.265", "libx265", ["-c:v", "libx265", "-preset", "veryfast", *cap, "-x265-params", "log-level=error"], "mp4", "yuv420p"),
            ("AV1", "libsvtav1", ["-c:v", "libsvtav1", "-preset", "10", "-b:v", f"{kbps}k"], "mkv", "yuv420p"),
            ("MJPEG, lowest quality", "mjpeg", ["-c:v", "mjpeg", "-q:v", "31"], "mkv", "yuvj420p")]
    panels = []
    for name, enc, args, ext, pix in jobs:
        if enc not in ENCODERS:
            continue
        p, _ = encode(src, tmp, f"codec_{enc}", args, ext, pix)
        m = measure(p, src); MEAS[f"codec_{enc}"] = m
        panels.append((crop(frame(p, 1.5), BOX), name, fmt(m)))
    strip("knob-codec", panels)


def presets_same_bitrate(src, tmp: Path, kbps: int = 500) -> None:
    panels = []
    for preset in ("ultrafast", "veryfast", "medium", "slow"):
        p, cpu = encode(src, tmp, f"preset_{preset}", ["-c:v", "libx264", "-preset", preset, "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps}k"])
        m = measure(p, src); m["cpu_ms_per_frame"] = cpu * 1000 / (SECONDS * FPS); MEAS[f"preset_{preset}"] = m
        panels.append((crop(frame(p, 1.5), BOX), preset, fmt(m)))
    strip("knob-preset", panels)


def resolution_same_bitrate(src, tmp: Path, kbps: int = 150) -> None:
    panels = []
    for w, h in ((1280, 720), (640, 360), (320, 180)):
        p, _ = encode(src, tmp, f"res_{w}", ["-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps}k"],
                      vf=f"scale={w}:{h}")
        m = measure(p, src); MEAS[f"res_{w}"] = m
        panels.append((crop(frame(p, 1.5), BOX), f"sent at {w}×{h}", f"shown at 1280×720 · SSIM {m['ssim']:.3f}"))
    strip("knob-resolution", panels)


def gray_frames(path: Path) -> np.ndarray:
    raw = subprocess.run([E.FFMPEG, "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def gop_after_loss(src, tmp: Path, lost_packets: int = 130, lost_frame: int = 10, look_frame: int = 40) -> None:
    """Drop the same burst of TS packets from three streams. Compare with the same stream decoded WITHOUT loss,
    so only the damage counts (not normal compression error). Red = pixels still wrong one second later."""
    variants = [("keyframe every 1 s", ["-g", "30", "-keyint_min", "30", "-sc_threshold", "0"]),
                ("keyframe every 5 s", ["-g", "150", "-keyint_min", "150", "-sc_threshold", "0"]),
                ("intra refresh (no keyframes)", ["-x264-params", "intra-refresh=1:keyint=30"])]
    panels, curves = [], {}
    lost_kb = lost_packets * 188 / 1024
    for k, (name, extra) in enumerate(variants):
        ts = tmp / f"loss_{k}.ts"
        ff("-i", str(src.mkv), "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-b:v", "2M", "-maxrate", "2M", "-bufsize", "1M",
           *extra, "-pix_fmt", "yuv420p", "-f", "mpegts", str(ts))
        pkts = json.loads(subprocess.run([E.FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pos", "-of", "json", str(ts)],
                                         capture_output=True, text=True).stdout)["packets"]
        start = (int(pkts[lost_frame]["pos"]) // 188) * 188
        data = bytearray(ts.read_bytes())
        del data[start:start + lost_packets * 188]                         # a burst of lost UDP packets
        bad = tmp / f"loss_{k}_bad.ts"; bad.write_bytes(bytes(data))
        good_f, bad_f = gray_frames(ts), gray_frames(bad)
        n = min(len(good_f), len(bad_f))
        diff = np.abs(good_f[:n] - bad_f[:n])
        curves[name] = [float((d > 6).mean() * 100) for d in diff]          # % of pixels visibly wrong
        pic = frame_n(bad, look_frame).astype(np.float32)
        mask = gaussian_filter((diff[look_frame] > 6).astype(np.float32), 2)[..., None]
        pic = pic * (1 - 0.65 * mask) + np.array([255, 40, 40], np.float32) * 0.65 * mask
        MEAS[f"loss_{k}"] = {"name": name, "pct_wrong_1s_later": curves[name][look_frame]}
        panels.append((crop(pic.clip(0, 255).astype(np.uint8), (0, 0, W, H)), name,
                       f"1 s after the loss: {curves[name][look_frame]:.0f} % of picture wrong"))
    strip("knob-gop-loss", panels)
    loss_chart(curves, lost_frame, lost_kb)


def loss_chart(curves: dict, lost_frame: int, lost_kb: float) -> None:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=150)
    colors = ["#2a78d6", "#d03a3a", "#1f9e6e"]
    for (name, ys), c in zip(curves.items(), colors):
        t = np.arange(len(ys)) / FPS
        ax.plot(t, ys, color=c, lw=2, label=name)
    ax.axvline(lost_frame / FPS, color="#888", lw=1, ls=":")
    top = max(40, max(max(v) for v in curves.values()) * 1.6)
    ax.text(lost_frame / FPS + 0.03, top * 0.95, f"{lost_kb:.0f} kB lost here", fontsize=9, color="#52514e", va="top")
    if SYNTHETIC:
        cut = int(0.66 * SECONDS * FPS) / FPS                                # the synthetic clip changes camera here
        ax.axvline(cut, color="#bbb", lw=1, ls="--")
        ax.text(cut + 0.03, top * 0.55, "camera cut in the clip\nrepaints the picture", fontsize=8, color="#52514e")
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.set_ylim(0, top); ax.set_xlim(0, len(ys) / FPS)
    ax.set_xlabel("seconds"); ax.set_ylabel("% of picture wrong")
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    fig.subplots_adjust(right=0.97, left=0.09, bottom=0.17, top=0.95)
    fig.savefig(OUT / "knob-gop-loss-chart.jpg", dpi=150, pil_kwargs={"quality": 90})
    plt.close(fig)
    print("wrote knob-gop-loss-chart")


def deblocking(src, tmp: Path) -> None:
    """The loop filter at a starved bitrate: same encode with the deblocking filter off and on."""
    panels = []
    for name, extra in (("deblocking off", ["-x264-params", "no-deblock=1"]), ("deblocking on (default)", [])):
        p, _ = encode(src, tmp, f"deblock_{bool(extra)}", ["-c:v", "libx264", "-preset", "veryfast", "-crf", "40", *extra])
        m = measure(p, src); MEAS[f"deblock_{name.split()[1]}"] = m
        panels.append((crop(frame(p, 1.5), BOX), name, "CRF 40 · " + fmt(m)))
    strip("deblocking", panels)


def noise_cost(src, tmp: Path) -> None:
    panels = []
    for name, vf in (("as filmed", None), ("+ sensor noise (high gain)", "noise=alls=9:allf=t")):
        p, _ = encode(src, tmp, f"noise_{bool(vf)}", ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"], vf=vf)
        m = measure(p, src); MEAS[f"noise_{bool(vf)}"] = m
        panels.append((crop(frame(p, 1.5), BOX), name, f"CRF 23 · {m['mbps']:.2f} Mb/s"))
    ratio = MEAS["noise_True"]["mbps"] / MEAS["noise_False"]["mbps"]
    panels[1] = (panels[1][0], panels[1][1], panels[1][2] + f" ({ratio:.1f}×)")
    strip("knob-noise", panels)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, help="real footage to use instead of the synthetic clip")
    ap.add_argument("--start", type=float, default=0.0, help="seconds into --source to start")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="encimg_"))
    global SYNTHETIC
    SYNTHETIC = a.source is None
    src = E.prepare_source(tmp, a.source, SECONDS, H, FPS, a.start)
    MEAS["source"] = {"name": src.name}
    for step in (chroma_bleed, deblocking, crf_ladder, codecs_same_bitrate, presets_same_bitrate, resolution_same_bitrate, gop_after_loss, noise_cost):
        step(src, tmp)
    motion_search(src)
    (OUT / "measurements.json").write_text(json.dumps(MEAS, indent=1))
    print(json.dumps(MEAS, indent=1))


if __name__ == "__main__":
    main()
