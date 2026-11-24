"""Make the example pictures for the video-diagnostics field guide (docs/streaming/img/diagnostics/).

Every picture is made here from the Encoding Lab's synthetic underwater clip, so nothing is copied from the web:
  * compression artifacts are REAL encodes (x264, MPEG-2, JPEG) at bad settings;
  * packet loss and decoder corruption are REAL damaged streams decoded by FFmpeg;
  * camera, motion and display effects are simulated from their physics (row timing, fields, gain, range);
  * timing problems are charts.
It also prints a few measurements the doc quotes (bitrate cost of sensor noise, keyframe size, healing time).

    python3 build/make_diagnostic_images.py            # ≈ 1–2 min, writes ≈ 45 JPEGs + measurements.json
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, shift as nd_shift

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "encoding_lab"))
from lab import engine as E  # noqa: E402

OUT = ROOT / "docs" / "streaming" / "img" / "diagnostics"
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="diag_"))
W, H, FPS, N = 1280, 720, 30, 75
OW, OH = 800, 450                                # every output picture
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
NAVY, CARD, CYAN, AMBER, ROSE, TEAL, MUTED, GRID = "#0A1628", "#13294A", "#22D3EE", "#F59E0B", "#F43F5E", "#14B8A6", "#9FB3C8", "#24406A"
MEAS: dict[str, float | str] = {}


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def read_frames(path: Path, w: int = W, h: int = H, n: int | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-"]
    if n:
        cmd[3:3] = ["-frames:v", str(n)]
        cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32) / 255


def write_raw(frames, path: Path) -> None:
    """Write an iterable of float RGB frames (one at a time, to keep memory low) as a lossless FFV1 clip."""
    p = None
    for fr in frames:
        if p is None:
            h, w, _ = fr.shape
            p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                                  "-r", str(FPS), "-i", "-", "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
        p.stdin.write((np.clip(fr, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


def to_img(a: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def label(im: Image.Image, text: str, xy=(14, 12), color=(255, 255, 255), bg=(10, 22, 40, 190), size=22) -> None:
    d = ImageDraw.Draw(im, "RGBA"); f = ImageFont.truetype(FONT, size)
    l, t, r, b = d.textbbox(xy, text, font=f)
    d.rectangle((l - 8, t - 6, r + 8, b + 6), fill=bg); d.text(xy, text, font=f, fill=color)


def save(name: str, im: Image.Image | np.ndarray, tag: str | None = None) -> None:
    if isinstance(im, np.ndarray):
        im = to_img(im)
    im = im.convert("RGB").resize((OW, OH), Image.LANCZOS) if im.size != (OW, OH) else im.convert("RGB")
    if tag:
        label(im, tag)
    im.save(OUT / f"{name}.jpg", quality=86, optimize=True)
    print("  ", name)


def split(a: np.ndarray, b: np.ndarray, la: str = "OK", lb: str = "PROBLEM", boost_a=None) -> Image.Image:
    """Left half of picture a next to the right half of picture b, both labelled."""
    h, w, _ = a.shape
    m = np.concatenate([a[:, : w // 2], b[:, w // 2:]], axis=1)
    im = to_img(m).resize((OW, OH), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.line((OW // 2, 0, OW // 2, OH), fill=(255, 255, 255), width=3)
    label(im, la, (14, 12), (20, 230, 160)); label(im, lb, (OW // 2 + 14, 12), (255, 120, 120))
    return im


def pair(a: np.ndarray, b: np.ndarray, x: float, y: float, frac: float, la: str = "OK", lb: str = "PROBLEM") -> Image.Image:
    """The same zoomed window of picture a and picture b, side by side, labelled."""
    h, w, _ = a.shape
    ch = int(h * frac); cw = int(ch * (OW / 2) / OH)
    x0 = int(np.clip(x * w - cw / 2, 0, w - cw)); y0 = int(np.clip(y * h - ch / 2, 0, h - ch))
    im = Image.new("RGB", (OW, OH))
    for k, arr in enumerate((a, b)):
        im.paste(to_img(arr[y0:y0 + ch, x0:x0 + cw]).resize((OW // 2, OH), Image.LANCZOS), (k * OW // 2, 0))
    d = ImageDraw.Draw(im); d.line((OW // 2, 0, OW // 2, OH), fill=(255, 255, 255), width=3)
    label(im, la, (14, 12), (20, 230, 160)); label(im, lb, (OW // 2 + 14, 12), (255, 120, 120))
    return im


def crop(a: np.ndarray, x: float, y: float, frac: float = 0.5) -> np.ndarray:
    """Zoom: the frac-sized window centred at (x, y) in 0..1 coordinates."""
    h, w, _ = a.shape
    cw, ch = int(w * frac), int(h * frac)
    x0 = int(np.clip(x * w - cw / 2, 0, w - cw)); y0 = int(np.clip(y * h - ch / 2, 0, h - ch))
    return a[y0:y0 + ch, x0:x0 + cw]


# ---------------------------------------------------------------------------------------------- charts
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"figure.facecolor": NAVY, "axes.facecolor": NAVY, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                     "ytick.color": MUTED, "text.color": "white", "font.size": 15, "axes.titleweight": "bold", "axes.titlesize": 17,
                     "axes.spines.top": False, "axes.spines.right": False, "grid.color": GRID, "font.family": "DejaVu Sans"})


def chart(name: str, draw) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    draw(ax)
    ax.grid(True, axis="y", lw=0.6)
    fig.tight_layout(); fig.savefig(OUT / f"{name}.jpg", dpi=100, pil_kwargs={"quality": 88}); plt.close(fig)
    print("  ", name)


def main() -> None:
    print("source clip …")
    src = TMP / "src.mkv"
    E.synth_underwater(src, W, H, FPS, N)
    F = read_frames(src)
    f0 = F[10]

    # a scene with hard edges for ringing / aspect / tearing: a gauge plate and a label on the pipe
    def with_gauge(a: np.ndarray, cx=0.73, cy=0.33, r=0.17, txt="M.I.A  ROV-07") -> np.ndarray:
        im = to_img(a); d = ImageDraw.Draw(im)
        X, Y, R = int(cx * W), int(cy * H), int(r * H)
        d.ellipse((X - R, Y - R, X + R, Y + R), fill=(235, 235, 225), outline=(20, 20, 20), width=6)
        for k in range(0, 360, 30):
            t = math.radians(k); d.line((X + 0.8 * R * math.cos(t), Y + 0.8 * R * math.sin(t), X + 0.95 * R * math.cos(t), Y + 0.95 * R * math.sin(t)), fill=(20, 20, 20), width=4)
        d.line((X, Y, X + 0.7 * R * math.cos(-0.9), Y + 0.7 * R * math.sin(-0.9)), fill=(200, 30, 30), width=7)
        d.text((int(0.08 * W), int(0.68 * H)), txt, font=ImageFont.truetype(FONT, 54), fill=(250, 250, 250))
        return np.asarray(im).astype(np.float32) / 255
    g0 = with_gauge(f0)

    # ======================================================================= compression (real encodes)
    print("compression …")
    gsrc = TMP / "g.mkv"; write_raw((with_gauge(F[i]) for i in range(0, 30)), gsrc)
    # 6 blocking: MPEG-2 at a starved bitrate, no deblocking filter in MPEG-2
    ff("-i", str(gsrc), "-c:v", "libx264", "-qp", "46", "-x264-params", "no-deblock=1", "-g", "15", str(TMP / "blk.mp4"))
    blk = read_frames(TMP / "blk.mp4")[20]
    save("blocking", pair(with_gauge(F[20]), blk, 0.6, 0.5, 0.75, "source", "x264 QP 46, deblocking off"))
    # 7 ringing / mosquito: JPEG quality 8 around the white label and gauge edges, zoomed
    ff("-i", str(gsrc), "-frames:v", "1", "-q:v", "28", str(TMP / "ring.jpg"))
    ring = np.asarray(Image.open(TMP / "ring.jpg").convert("RGB")).astype(np.float32) / 255
    save("ringing", pair(g0, ring, 0.15, 0.71, 0.26, "original (zoom)", "JPEG q=28 (zoom)"))
    # 9 pixelation: what a 1/8-resolution substream looks like scaled up to full screen
    small = np.asarray(to_img(F[30]).resize((W // 10, H // 10), Image.BILINEAR).resize((W, H), Image.NEAREST)).astype(np.float32) / 255
    save("pixelation", split(F[30], small, "1280×720", "128×72 shown full screen"))
    # 10 banding: smooth water gradient, 8-bit + heavy quantization; contrast boosted to make steps visible
    grad = np.linspace(0.18, 0.42, W)[None, :, None] * np.ones((H, 1, 1)) * np.array([0.35, 0.85, 0.95]) + np.linspace(0, 0.08, H)[:, None, None]
    gpath = TMP / "grad.mkv"; write_raw((grad + np.random.default_rng(i).normal(0, 0.002, grad.shape) for i in range(10)), gpath)
    ff("-i", str(gpath), "-c:v", "libx264", "-qp", "40", str(TMP / "band.mp4"))
    band = read_frames(TMP / "band.mp4")[5]
    boost = lambda a: np.clip((a - 0.1) * 3.0, 0, 1)
    save("banding", split(boost(grad), boost(band), "gradient (×3 contrast)", "x264 qp 40 (×3 contrast)"))
    # keyframe pile-up: real frame sizes of a 1 s GOP live encode
    ff("-i", str(src), "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-b:v", "2000k", "-g", "30", "-sc_threshold", "0", str(TMP / "gop.mp4"))
    sizes = [int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size", "-of", "csv=p=0",
                                             str(TMP / "gop.mp4")], capture_output=True, text=True).stdout.split()]
    kb = np.array(sizes) / 1000
    MEAS["iframe_ratio"] = round(float(kb[::30].mean() / np.median(kb)), 1)
    def kf(ax):
        cols = [ROSE if i % 30 == 0 else CYAN for i in range(len(kb))]
        ax.bar(range(len(kb)), kb, color=cols, width=0.85)
        ax.set_xlabel("frame"); ax.set_ylabel("kB per frame"); ax.set_title(f"Keyframes ≈ {MEAS['iframe_ratio']}× other frames (measured)")
    chart("keyframe-burst", kf)

    # ======================================================================= network (real damaged streams)
    print("network …")
    def moving(i: int) -> np.ndarray:                                    # gauge + text sliding 6 px per frame
        im = to_img(F[i]); d = ImageDraw.Draw(im); X, Y, R = int(0.35 * W + 6 * i), 240, 120
        d.ellipse((X - R, Y - R, X + R, Y + R), fill=(235, 235, 225), outline=(20, 20, 20), width=6)
        for k in range(0, 360, 30):
            t_ = math.radians(k); d.line((X + 0.8 * R * math.cos(t_), Y + 0.8 * R * math.sin(t_), X + 0.95 * R * math.cos(t_), Y + 0.95 * R * math.sin(t_)), fill=(20, 20, 20), width=4)
        d.text((100 + 6 * i, 480), "M.I.A  ROV-07  DEPTH 3.2 m", font=ImageFont.truetype(FONT, 52), fill=(250, 250, 250))
        return np.asarray(im).astype(np.float32) / 255
    mv = TMP / "moving.mkv"; write_raw((moving(i) for i in range(40)), mv)
    ff("-i", str(mv), "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-b:v", "2000k", "-g", "150", "-sc_threshold", "0",
       "-f", "mpegts", str(TMP / "live.ts"))
    data = (TMP / "live.ts").read_bytes()
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,pos", "-of", "csv=p=0", str(TMP / "live.ts")],
                         capture_output=True, text=True).stdout
    pk = [(float(a_), int(b_)) for a_, b_, *_ in (l.split(",") for l in out.split()) if a_ not in ("", "N/A") and b_ not in ("", "N/A")]
    pos = pk[1][1]; pos -= pos % 188; cut = 188 * 40                  # 7.5 kB ≈ 5 UDP datagrams from the first P-frame
    (TMP / "lost.ts").write_bytes(data[:pos + 188 * 3] + data[pos + 188 * 3 + cut:])
    lost, clean = read_frames(TMP / "lost.ts"), read_frames(TMP / "live.ts")
    n_ = min(len(lost), len(clean)); worst = int(np.argmax([np.abs(lost[i] - clean[i]).mean() for i in range(n_)]))
    ff("-i", str(mv), "-c:v", "libx264", "-preset", "veryfast", "-b:v", "150k", "-maxrate", "150k", "-bufsize", "75k", "-g", "60", str(TMP / "blur.mp4"))
    bl, mvf = read_frames(TMP / "blur.mp4"), read_frames(mv)
    save("blur", pair(mvf[30], bl[30], 0.4, 0.62, 0.55, "source (zoom)", "x264 at 0.15 Mb/s, moving (zoom)"))
    save("packet-loss", pair(clean[worst], lost[worst], 0.55, 0.55, 0.9, "clean stream", "7.5 kB lost: the smear spreads"))
    # 12 decoder corruption: random bit errors in the H.264 bitstream (FFmpeg noise filter), like a corrupting link or bad memory
    ff("-i", str(src), "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2000k", "-g", "150", "-bsf:v", "noise=amount=2500", "-f", "h264", str(TMP / "corrupt.h264"))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "quiet", "-err_detect", "ignore_err", "-i", str(TMP / "corrupt.h264"),
                    "-c:v", "ffv1", str(TMP / "corrupt.mkv")])
    cor = read_frames(TMP / "corrupt.mkv")
    save("decoder-corruption", split(F[40], cor[min(40, len(cor) - 1)], "clean", "bit errors in the H.264 stream"))
    # 13 buffering + 14 dropouts + 16 bursts: charts
    t = np.arange(0, 20, 0.05)
    def buf(ax):
        thr = np.where((t > 6) & (t < 11), 1.2, 2.6)
        lvl = np.zeros_like(t); b = 0.5
        for i in range(1, len(t)):
            b = min(2.0, max(0.0, b + (thr[i] - 2.0) * 0.05)); lvl[i] = b
        ax.plot(t, lvl, color=CYAN, lw=3, label="receiver buffer (s of video)")
        ax.fill_between(t, 0, 1, where=lvl <= 0.01, color=ROSE, alpha=0.35, transform=ax.get_xaxis_transform(), label="playback paused")
        ax.axvspan(6, 11, color=AMBER, alpha=0.12); ax.text(8.5, 2.25, "tether gives 1.2 Mb/s\nstream needs 2.0", ha="center", color=AMBER, fontsize=13)
        ax.set_ylim(0, 2.8); ax.set_xlabel("time (s)"); ax.set_ylabel("buffered (s)"); ax.set_title("Buffering: the buffer drains, then playback stops"); ax.legend(loc="lower right", fontsize=11, frameon=False)
    chart("buffering", buf)
    def drop(ax):
        thr = np.full_like(t, 2.0) + np.random.default_rng(3).normal(0, 0.08, len(t))
        for a, b in [(4, 6.2), (12, 12.6), (15.5, 17.8)]:
            thr[(t > a) & (t < b)] = 0
        ax.plot(t, thr, color=CYAN, lw=2.5); ax.fill_between(t, 0, 2.6, where=thr == 0, color=ROSE, alpha=0.3)
        ax.set_ylim(0, 2.8); ax.set_xlabel("time (s)"); ax.set_ylabel("received Mb/s"); ax.set_title("Dropouts: the stream stops, then reconnects")
        ax.text(5.1, 2.35, "no picture\n+ reconnect\n+ wait for I-frame", ha="center", color=ROSE, fontsize=12)
    chart("dropouts", drop)
    def burst(ax):
        arr = np.cumsum(np.full(40, 33.3)); arr[14:20] = arr[13] + 230 + np.arange(6) * 2
        arr[20:] = arr[19] + 33.3 * np.arange(1, 21)
        ax.eventplot([arr], colors=CYAN, lineoffsets=1, linelengths=0.8, linewidths=3)
        ax.annotate("230 ms of nothing…", (arr[13] + 115, 1.5), ha="center", color=ROSE, fontsize=14)
        ax.annotate("…then 6 frames at once", (arr[17], 0.42), ha="center", color=AMBER, fontsize=14)
        ax.set_yticks([]); ax.set_ylim(0.3, 1.8); ax.set_xlabel("frame arrival time at the pilot laptop (ms)"); ax.set_title("Frame burst: a freeze, then a fast-forward")
    chart("frame-burst", burst)

    # ======================================================================= timing charts
    print("timing …")
    def g2g(ax):
        st = [("capture", 33, CYAN), ("encode", 12, TEAL), ("network", 4, "#3B82F6"), ("jitter buffer", 50, AMBER), ("decode", 8, "#8B5CF6"), ("display", 25, ROSE)]
        x = 0
        for n_, v, c in st:
            ax.barh([0], [v], left=x, color=c, edgecolor=NAVY, height=0.5)
            ax.text(x + v / 2, 0.42 if len(ax.texts) % 2 == 0 else -0.42, f"{n_}\n{v} ms", ha="center", va="bottom" if len(ax.texts) % 2 == 0 else "top", fontsize=11, color=c)
            x += v
        ax.text(x / 2, -1.05, f"glass-to-glass ≈ {x} ms = what the pilot feels", ha="center", fontsize=15, color="white", weight="bold")
        ax.set_xlim(0, x * 1.02); ax.set_ylim(-1.3, 1.2); ax.set_yticks([]); ax.set_xlabel("ms after the light hit the sensor"); ax.set_title("Latency is the sum of every stage")
    chart("glass-to-glass", g2g)
    def drift(ax):
        tt = np.arange(0, 120, 1.0)
        ax.plot(tt, 140 + tt * 10, color=ROSE, lw=3, label="receiver plays 29.7 fps, camera sends 30 fps → queue grows")
        ax.plot(tt, 140 + np.random.default_rng(1).normal(0, 4, len(tt)), color=TEAL, lw=3, label="queue kept at 1 frame (drop old frames)")
        ax.set_xlabel("time (s)"); ax.set_ylabel("latency (ms)"); ax.set_title("Latency drift: a queue that only grows")
        ax.legend(loc="upper left", fontsize=11, frameon=False)
    chart("latency-drift", drift)
    def jit(ax):
        rng = np.random.default_rng(5)
        a = 33.3 + rng.normal(0, 2, 90); b = 33.3 + rng.gamma(1.2, 9, 90) - 10
        ax.plot(a, color=TEAL, lw=2, label="wired tether: ±2 ms"); ax.plot(b, color=AMBER, lw=2, label="busy link: ±15 ms")
        ax.axhline(33.3, color=MUTED, ls=":"); ax.set_xlabel("frame"); ax.set_ylabel("gap since previous frame (ms)"); ax.set_title("Jitter: same average, uneven arrival")
        ax.legend(loc="upper right", fontsize=11, frameon=False)
    chart("jitter", jit)
    def pacing(ax):
        iv = np.array([16.7, 50] * 15)
        ax.bar(range(len(iv)), iv, color=[AMBER if v > 40 else CYAN for v in iv]); ax.axhline(33.3, color="white", ls=":", lw=2)
        ax.text(29, 35.5, "average 33.3 ms = \"30 fps\"", ha="right", fontsize=13)
        ax.set_xlabel("presented frame"); ax.set_ylabel("time on screen (ms)"); ax.set_title("Uneven pacing: 30 fps on paper, jerky on screen")
    chart("frame-pacing", pacing)
    def stale(ax):
        tt = np.arange(0, 6, 1 / 30)
        age = (tt % (1 / 30)) * 1000 + 120
        age[(tt > 2.5)] = (tt[tt > 2.5] - 2.5) * 1000 + 120
        age[tt > 4.6] = (tt[tt > 4.6] % (1 / 30)) * 1000 + 120
        ax.plot(tt, age, color=CYAN, lw=2.5); ax.axhline(500, color=ROSE, ls="--"); ax.text(0.1, 520, "STALE threshold 500 ms", color=ROSE, fontsize=12)
        ax.fill_between(tt, 0, 1, where=(tt > 2.5) & (tt < 4.6), color=ROSE, alpha=0.15, transform=ax.get_xaxis_transform())
        ax.text(3.55, 1700, "same picture on screen,\nUI still says \"30 fps\"", ha="center", fontsize=13, color=ROSE)
        ax.set_xlabel("time (s)"); ax.set_ylabel("age of shown frame (ms)"); ax.set_title("Stale frame: the picture stops, the app does not")
    chart("stale-frame", stale)
    def hold(ax):
        ax.bar(["x264 defaults", "-tune zerolatency"], [1047, 0], color=[ROSE, TEAL], width=0.55)
        ax.text(0, 1070, "31 frames held\n≈ 1047 ms", ha="center", fontsize=14); ax.text(1, 40, "0 frames held", ha="center", fontsize=14)
        ax.set_ylim(0, 1300); ax.set_ylabel("delay added by the encoder (ms)"); ax.set_title("Encoder hold-back (measured in the Lab, 720p30)")
    chart("encoder-hold", hold)
    def thermal(ax):
        tt = np.linspace(0, 20, 200)
        temp = 45 + 40 * (1 - np.exp(-tt / 6)); fps = np.where(temp > 80, 30 - (temp - 80) * 2.4, 30)
        ax.plot(tt, fps, color=CYAN, lw=3, label="encode fps"); ax.set_ylim(0, 35); ax.set_ylabel("fps"); ax.set_xlabel("minutes, enclosure closed")
        ax2 = ax.twinx(); ax2.plot(tt, temp, color=ROSE, lw=2, ls="--", label="SoC °C"); ax2.set_ylabel("°C", color=ROSE); ax2.tick_params(colors=ROSE)
        ax2.spines["right"].set_visible(True); ax2.axhline(80, color=ROSE, ls=":", lw=1); ax2.text(0.3, 81.5, "throttle point (Pi 5: 80 °C)", color=ROSE, fontsize=11)
        ax.set_title("Thermal throttling (illustration)")
    chart("thermal", thermal)
    def judder(ax):
        rep = [2, 3] * 6
        x = 0
        for i, r in enumerate(rep):
            ax.barh([0], [r * 16.7], left=x, color=CYAN if i % 2 == 0 else AMBER, edgecolor=NAVY, height=0.5)
            ax.text(x + r * 8.3, 0, f"F{i + 1}\n{r * 16.7:.0f} ms", ha="center", va="center", fontsize=10, color=NAVY, weight="bold")
            x += r * 16.7
        ax.set_yticks([]); ax.set_xlabel("ms on a 60 Hz screen"); ax.set_title("Judder: 24 fps on 60 Hz shows frames for 33, 50, 33, 50 ms")
    chart("judder", judder)
    def desync(ax):
        tt = np.arange(0, 30, 0.5)
        ax.plot(tt, np.full_like(tt, 40), color=TEAL, lw=3, label="telemetry age (depth, heading)")
        ax.plot(tt, 180 + tt * 6, color=ROSE, lw=3, label="video age (growing queue)")
        ax.fill_between(tt, 40, 180 + tt * 6, color=ROSE, alpha=0.12)
        ax.text(20, 200, "the HUD shows where the ROV IS,\nthe video shows where it WAS", ha="center", fontsize=13)
        ax.set_xlabel("time (s)"); ax.set_ylabel("age when shown (ms)"); ax.set_title("Desync: data and picture disagree"); ax.legend(loc="upper left", fontsize=11, frameon=False)
    chart("desync", desync)
    def dlag(ax):
        st = [("decode", 8, "#8B5CF6"), ("app render queue", 33, AMBER), ("compositor / vsync", 17, CYAN), ("TV picture processing", 60, ROSE), ("panel", 8, TEAL)]
        x = 0
        for n_, v, c in st:
            ax.barh([0], [v], left=x, color=c, edgecolor=NAVY, height=0.5); ax.text(x + v / 2, 0.38, f"{n_}\n{v} ms", ha="center", va="bottom", fontsize=10.5, color=c)
            x += v
        ax.text(x / 2, -0.55, "TV \"game mode\" alone can remove ≈ 30–60 ms", ha="center", fontsize=14)
        ax.set_xlim(0, x * 1.02); ax.set_ylim(-0.8, 1.2); ax.set_yticks([]); ax.set_xlabel("ms after decode (typical values)"); ax.set_title("Display lag: delay after the frame is decoded")
    chart("display-lag", dlag)
    def strobe(ax):
        ax.set_aspect("equal"); ax.axis("off")
        for k, ang in enumerate([0, 348, 336, 324]):
            cx = k * 2.6
            ax.add_patch(plt.Circle((cx, 0), 1.05, fill=False, color=GRID, lw=1.5))
            for b in range(3):
                a = math.radians(ang + b * 120)
                ax.plot([cx, cx + math.cos(a)], [0, math.sin(a)], color=AMBER if b == 0 else CYAN, lw=6, solid_capstyle="round")
            ax.text(cx, -1.45, f"frame {k + 1}", ha="center", color=MUTED, fontsize=13)
        ax.set_xlim(-1.4, 9.2); ax.set_ylim(-1.8, 1.5)
        ax.set_title("Strobing: a 3-blade thruster at 540 rpm filmed at 30 fps turns 108° per frame,\nwhich looks like −12° per frame: slowly backwards", fontsize=13)
    chart("strobing", strobe)
    def reswitch(ax):
        ax.axis("off")
        for i, (w_, lab) in enumerate([(1.0, "1280×720"), (1.0, "1280×720"), (0.0, "blank: decoder\nre-initialises"), (0.5, "640×360\nscaled wrong"), (1.0, "1280×720")]):
            x = i * 1.9
            ax.add_patch(plt.Rectangle((x, 0), 1.6, 0.9, color=CARD, ec=GRID))
            if w_:
                ax.add_patch(plt.Rectangle((x + 0.1, 0.1), 1.4 * w_, 0.7 * w_, color="#2A6F86"))
            ax.text(x + 0.8, -0.32, lab, ha="center", va="top", fontsize=12, color=ROSE if w_ != 1.0 else MUTED)
        ax.set_xlim(-0.2, 9.5); ax.set_ylim(-1.2, 1.2); ax.set_title("Resolution switch: blank, then wrongly sized")
    chart("resolution-switch", reswitch)
    def black(ax):
        ax.axis("off")
        for i in range(7):
            x = i * 1.35
            ax.add_patch(plt.Rectangle((x, 0), 1.2, 0.7, color="black" if i in (3, 4) else "#2A6F86", ec=GRID))
            ax.text(x + 0.6, -0.15, f"{i + 1}", ha="center", va="top", fontsize=12, color=ROSE if i in (3, 4) else MUTED)
        ax.text(4.7, 1.0, "two black frames: capture timeout, decoder reset or wrong surface format", ha="center", fontsize=13, color=ROSE)
        ax.set_xlim(-0.2, 9.6); ax.set_ylim(-0.6, 1.3); ax.set_title("Black frames in an otherwise normal stream")
    chart("black-frames", black)
    def usb(ax):
        cams = [("cam 1 MJPEG 720p30", 60), ("cam 2 MJPEG 720p30", 60), ("cam 3 YUYV 640×480@30", 147)]
        x = 0
        for n_, v in cams:
            ax.barh([0], [v], left=x, color=CYAN if v < 100 else ROSE, edgecolor=NAVY, height=0.5)
            ax.text(x + v / 2, -0.32 if v < 100 and x > 0 else 0.32, f"{n_}\n≈ {v} Mb/s", ha="center", va="top" if v < 100 and x > 0 else "bottom", fontsize=10.5, color=CYAN if v < 100 else ROSE)
            x += v
        ax.axvline(384, color=AMBER, lw=3, ls="--"); ax.text(386, 0.42, "USB 2.0 periodic limit\n≈ 80 % of 480 Mb/s", color=AMBER, fontsize=12)
        ax.set_xlim(0, 480); ax.set_ylim(-0.8, 0.95); ax.set_yticks([]); ax.set_xlabel("Mb/s reserved on ONE USB 2.0 bus")
        ax.set_title("USB 2.0: the 3rd camera does not start")
    chart("usb-bandwidth", usb)

    # ======================================================================= motion (simulated from timing)
    print("motion …")
    # posts (pier piles) in front of the water for rolling shutter / combing / tearing / blur
    def posts(x_off: float) -> np.ndarray:
        a = F[10].copy()
        xs = np.arange(W)[None, :]
        for k in range(6):
            c = (k * 230 + x_off) % (W + 200) - 100
            m = np.abs(xs - c) < 26
            a[:, m[0]] = a[:, m[0]] * 0.25 + np.array([0.55, 0.5, 0.4]) * 0.75
        return a
    speed = 2400 / FPS                                     # px per frame: a fast yaw
    rs = np.zeros_like(F[10])
    for y in range(H):                                     # each row read 1/30 s × y/H later
        rs[y] = posts(speed * y / H * 1.0)[y]
    save("rolling-shutter", split(posts(0), rs, "global shutter", "rolling shutter, fast yaw"))
    ghost = 0.55 * posts(0) + 0.45 * posts(-90)
    save("ghosting", split(posts(0), ghost, "one frame", "blended with the previous frame"))
    mb = np.mean([posts(-k * 12) for k in range(10)], axis=0)
    save("motion-blur", split(posts(0), mb, "1/1000 s exposure", "1/30 s exposure while panning"))
    comb = posts(0).copy(); comb[1::2] = posts(-40)[1::2]
    save("combing", split(crop(posts(0), 0.4, 0.4, 0.35), crop(comb, 0.4, 0.4, 0.35), "progressive (zoom)", "interlaced fields woven (zoom)"))
    tear = posts(0).copy(); tear[int(0.45 * H):] = posts(-70)[int(0.45 * H):]
    im = to_img(tear).resize((OW, OH)); ImageDraw.Draw(im).line((0, int(0.45 * OH), 40, int(0.45 * OH)), fill=(255, 80, 80), width=5)
    save("tearing", im, "top = new frame, bottom = old frame")

    # ======================================================================= camera & optics
    print("camera …")
    x = F[20]
    water = np.array([18, 92, 110]) / 255.0
    haze = x * 0.35 + water * 0.65 + 0.05
    save("haze", split(x, haze, "clear water", "turbid water / haze"))
    rng = np.random.default_rng(11)
    bs = x.copy(); spots = np.zeros((H, W))
    yy, xx = np.mgrid[0:H, 0:W]
    cone = np.exp(-(((xx - 0.5 * W) / (0.45 * W)) ** 2 + ((yy - 0.45 * H) / (0.5 * H)) ** 2))
    for _ in range(900):
        px, py = rng.integers(0, W), rng.integers(0, H)
        if rng.random() < cone[py, px]:
            spots[py, px] = rng.uniform(0.6, 1.4)
    spots = gaussian_filter(spots, 2.2) * 30
    bs = np.clip(bs + spots[..., None] * np.array([0.9, 1, 1]), 0, 1)
    save("backscatter", split(x, bs, "lights to the side", "lights next to the lens"))
    noisy = np.clip(x + rng.normal(0, 0.05, x.shape), 0, 1)
    save("sensor-noise", split(x, noisy, "low gain", "high gain (+noise)"))
    # measure the bitrate cost of noise: same CRF, clean vs noisy clip
    clean_p, noisy_p = TMP / "clean.mkv", TMP / "noisy.mkv"
    nrng = np.random.default_rng(2)
    write_raw((F[i] for i in range(60)), clean_p)
    write_raw((F[i] + nrng.normal(0, 0.03, F[i].shape).astype(np.float32) for i in range(60)), noisy_p)
    def mbps(p):
        ff("-i", str(p), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(p.with_suffix(".mp4")))
        return p.with_suffix(".mp4").stat().st_size * 8 / (60 / FPS) / 1e6
    MEAS["noise_clean_mbps"], MEAS["noise_noisy_mbps"] = round(mbps(clean_p), 2), round(mbps(noisy_p), 2)
    MEAS["noise_factor"] = round(MEAS["noise_noisy_mbps"] / MEAS["noise_clean_mbps"], 1)
    focus = gaussian_filter(x, (6, 6, 0))
    save("focus", split(x, focus, "in focus", "out of focus"))
    save("exposure", split(np.clip(x * 0.25, 0, 1), np.clip(x * 3.2, 0, 1), "under-exposed", "over-exposed"))
    gw = 0.35 * x + 0.65 * (x / x.reshape(-1, 3).mean(0) * x.mean())             # grey-world white balance
    save("white-balance", split(np.clip(gw, 0, 1), x, "white balance corrected", "auto WB under water: blue-green cast"))
    fogc = gaussian_filter(x, (9, 9, 0)) * 0.55 + 0.42 * (1 - 0.6 * np.exp(-(((xx - W / 2) / (0.6 * W)) ** 2 + ((yy - H / 2) / (0.6 * H)) ** 2)))[..., None]
    save("condensation", split(x, fogc, "dry dome", "condensation inside the housing"))
    pwm = x * (0.65 + 0.35 * (np.sin(np.arange(H) / H * 2 * np.pi * 5.5) > -0.2))[:, None, None]
    save("light-banding", split(x, pwm, "constant-current lights", "PWM-dimmed lights + rolling shutter"))

    # ======================================================================= display & colour
    print("display …")
    ga = with_gauge(F[20])
    st = np.asarray(to_img(ga).resize((int(W * 0.75), H)).resize((W, H))).astype(np.float32) / 255   # 4:3 assumptions: squeezed and back
    sq = np.asarray(to_img(ga).resize((W, int(H * 1.33))).crop((0, int(H * 0.165), W, int(H * 0.165) + H))).astype(np.float32) / 255
    save("aspect-ratio", pair(ga, sq, 0.73, 0.4, 0.8, "correct 16:9", "stretched: the gauge is an oval"))
    limited_as_full = 16 / 255 + x * 219 / 255                 # limited-range video shown as full range: washed out
    save("color-range", split(x, limited_as_full, "range flags match", "limited range shown as full: grey blacks"))
    flick = np.concatenate([np.clip(F[20][:, i * W // 5:(i + 1) * W // 5] * g, 0, 1) for i, g in enumerate([1.0, 1.35, 0.8, 1.3, 0.85])], axis=1)
    im = to_img(flick).resize((OW, OH)); d = ImageDraw.Draw(im)
    for i in range(1, 5):
        d.line((i * OW // 5, 0, i * OW // 5, OH), fill=(10, 22, 40), width=4)
    save("flicker", im, "5 consecutive frames: auto-exposure hunting")

    (OUT / "measurements.json").write_text(json.dumps(MEAS, indent=1))
    print("measurements:", MEAS)


if __name__ == "__main__":
    main()
