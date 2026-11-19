# Notebook builder — part 1: intro, setup, source clip, Experiments 1–4.
# The cell texts are collected in CELLS and assembled by make_notebook.py.

CELLS = []


def md(text):
    CELLS.append(("markdown", text.strip("\n")))


def code(text):
    CELLS.append(("code", text.strip("\n")))


# ---------------------------------------------------------------------------
md(r"""
# ROV Video Streaming Workshop — Hands-on Notebook
### M.I.A Robotics · *Engineering Better ROV Systems*

This notebook is the practical half of the workshop. Every experiment follows the same pattern:

1. **Question.** What are we trying to find out?
2. **Theory.** Just enough to predict the answer *before* we run anything.
3. **Experiment.** A real measurement using FFmpeg and Python.
4. **Result.** A table and/or chart.
5. **Interpretation.** What this means for *your* ROV.
6. **Exercises.** For you to do, alone or in your team.

> **The rule of this notebook:** *we never trust a number we did not measure.* Where a value is an estimate (for example, a latency budget), it is labelled **ESTIMATE** and the notebook tells you how to measure it on the real vehicle.

| # | Experiment | Runs on a normal laptop? |
|---|---|---|
| 0 | Setup and the test clip | ✅ |
| 1 | Raw video bandwidth | ✅ |
| 2 | First FFmpeg encodes (H.264, H.265, MJPEG, AV1) | ✅ |
| 3 | CRF vs bitrate targets | ✅ |
| 4 | Encoder presets | ✅ |
| 5 | GOP, keyframes and packet loss | ✅ |
| 6 | Objective quality: PSNR, SSIM, VMAF | ✅ (VMAF only if your FFmpeg has `libvmaf`) |
| 7 | Eight-camera ROV simulator | ✅ |
| 8 | Main streams, substreams, priorities | ✅ |
| 9 | Latency | ✅ (PyAV part optional) |
| 10 | Hardware encoding | ⚠️ Jetson Nano / Raspberry Pi 5 / GPU-specific parts are clearly marked |
| 11 | Final optimization challenge | ✅ |

**Expected run time** on a 4-core laptop: about 5–10 minutes for the whole notebook. Results are cached in `work/`, so re-running is fast.
""")

md(r"""
## Installation

You need **Python 3.10+** and **FFmpeg 5 or newer** (with `libx264`; `libx265` and `libsvtav1` are optional).

```bash
# Ubuntu / Debian / Raspberry Pi OS / Jetson (JetPack)
sudo apt install ffmpeg python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # numpy pandas matplotlib scipy jupyterlab ipywidgets av
jupyter lab ROV_Video_Streaming_Workshop.ipynb
```

On **Windows**, install FFmpeg from <https://ffmpeg.org/download.html> (a "full" build includes x264/x265/SVT-AV1) and make sure `ffmpeg` is on your `PATH`. On **macOS**: `brew install ffmpeg`.

`av` (PyAV) and `ipywidgets` are optional: Experiment 9 uses PyAV to measure encoder delay frame-by-frame, and Experiment 7 uses ipywidgets for sliders. Everything else works without them.
""")

md(r"""
## 0. Setup

The first cell defines small helper functions so the experiments stay readable:

| Helper | What it does |
|---|---|
| `run(cmd)` | Runs a command and measures **wall-clock time** *and* **CPU time** (so we can compute how many cores an encoder used). |
| `probe(path)` | Calls `ffprobe` and returns codec, resolution, frame rate, duration, bitrate. |
| `packets(path)` | Returns every compressed packet's size, timestamp and keyframe flag. |
| `frame_types(path)` | Returns I/P/B picture types for every frame. |
| `quality(dist, ref)` | Computes PSNR and SSIM of a distorted video against the reference. |
""")

code(r'''
import os, sys, json, time, shutil, subprocess, resource, re, math, platform, random
from pathlib import Path
from fractions import Fraction

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

FFMPEG, FFPROBE = shutil.which("ffmpeg"), shutil.which("ffprobe")
assert FFMPEG and FFPROBE, "FFmpeg/ffprobe not found on PATH — see the installation section."

WORK = Path("work"); WORK.mkdir(exist_ok=True)
CPU_CORES = os.cpu_count()

# ---- chart style: one consistent, colour-blind-checked palette -------------
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CRITICAL = "#c62828"   # reserved for "over the limit" — never used as a series colour
plt.rcParams.update({
    "figure.dpi": 110, "figure.figsize": (9, 4.2), "axes.prop_cycle": plt.cycler(color=PALETTE),
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e3e2de", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.titleweight": "bold", "axes.titlesize": 12, "font.size": 10, "legend.frameon": False,
    "lines.linewidth": 2, "lines.markersize": 7,
})
pd.set_option("display.precision", 2)

def run(cmd, check=True):
    """Run a command; return wall time, CPU time (user+sys of the child) and stderr."""
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.perf_counter() - t0; r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(map(str, cmd))}\n{p.stderr[-1500:]}")
    return {"wall_s": wall, "cpu_s": cpu, "rc": p.returncode, "stderr": p.stderr, "stdout": p.stdout}

def probe(path):
    out = run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])["stdout"]
    j = json.loads(out); v = next(s for s in j["streams"] if s["codec_type"] == "video")
    dur = float(j["format"].get("duration", v.get("duration", 0)) or 0)
    size = Path(path).stat().st_size
    return {"codec": v["codec_name"], "profile": v.get("profile"), "pix_fmt": v.get("pix_fmt"),
            "width": v["width"], "height": v["height"], "fps": float(Fraction(v["avg_frame_rate"])) if v["avg_frame_rate"] != "0/0" else None,
            "duration_s": dur, "size_bytes": size, "bitrate_mbps": size * 8 / dur / 1e6 if dur else None}

def packets(path):
    """Per-packet table: pts (s), size (bytes), keyframe flag."""
    out = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,size,flags,pos",
               "-of", "csv=p=0", str(path)])["stdout"]
    rows = []
    for line in out.strip().splitlines():
        parts = line.split(",")
        if len(parts) < 4 or parts[0] in ("", "N/A"): continue
        rows.append((float(parts[0]), int(parts[1]), int(parts[2]) if parts[2] not in ("", "N/A") else -1, "K" in parts[3]))
    return pd.DataFrame(rows, columns=["pts", "size", "pos", "key"]).sort_values("pts").reset_index(drop=True)

def frame_types(path):
    out = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pict_type,pkt_size",
               "-of", "json", str(path)])["stdout"]
    frames = json.loads(out).get("frames", [])
    return pd.DataFrame([(f.get("pict_type", "?"), int(f.get("pkt_size", 0))) for f in frames], columns=["type", "size"])

def quality(dist, ref, width=None, height=None, per_frame=False):
    """PSNR (dB, luma+chroma average) and SSIM (0..1) of `dist` against `ref`.
    The distorted video is scaled back to the reference size first, so substreams can be compared too."""
    info = probe(ref); w, h = width or info["width"], height or info["height"]
    plog, slog = WORK / "psnr.log", WORK / "ssim.log"
    # Timestamps are snapped to the reference frame grid (settb): containers such as MKV store ms-rounded
    # timestamps, and without this every third frame would be compared with the wrong reference frame.
    sync = f"setpts=PTS-STARTPTS,settb=1/{FPS}"
    graph = (f"[0:v]scale={w}:{h}:flags=bicubic,format=yuv420p,{sync},split[d1][d2];"
             f"[1:v]format=yuv420p,{sync},split[r1][r2];"
             f"[d1][r1]psnr=stats_file={plog}[o1];[d2][r2]ssim=stats_file={slog}[o2]")
    ref_in = SRC_IN if Path(ref) == SRC else ["-i", str(ref)]
    r = run([FFMPEG, "-hide_banner", "-i", str(dist), *ref_in, "-lavfi", graph,
             "-map", "[o1]", "-f", "null", "-", "-map", "[o2]", "-f", "null", "-"])
    psnr = float(re.search(r"PSNR .*average:([\d.]+|inf)", r["stderr"]).group(1).replace("inf", "99"))
    ssim = float(re.search(r"SSIM .*All:([\d.]+)", r["stderr"]).group(1))
    if not per_frame:
        return psnr, ssim
    pf = [min(float(m.group(1).replace("inf", "99")), 99) for m in re.finditer(r"psnr_avg:([\d.]+|inf)", plog.read_text())]
    return psnr, ssim, np.array(pf)

def mbps_fmt(x, _=None):
    return f"{x:,.0f}" if x >= 10 else (f"{x:.1f}" if x >= 1 else f"{x:.2f}")

ENCODERS = run([FFMPEG, "-hide_banner", "-encoders"])["stdout"]
FILTERS = run([FFMPEG, "-hide_banner", "-filters"])["stdout"]
HAS = {name: (f" {name} " in ENCODERS) for name in ["libx264", "libx265", "libsvtav1", "libaom-av1", "mjpeg",
                                                   "h264_nvenc", "h264_vaapi", "h264_qsv", "h264_v4l2m2m"]}
HAS["libvmaf"] = " libvmaf " in FILTERS
print(run([FFMPEG, "-hide_banner", "-version"])["stdout"].splitlines()[0])
print(f"Python {platform.python_version()} on {platform.machine()} · {CPU_CORES} CPU cores")
print("Available:", ", ".join(k for k, v in HAS.items() if v))
print("Missing:  ", ", ".join(k for k, v in HAS.items() if not v) or "—")
''')

md(r"""
### 0.1 The test clip

We need a reference video. Ideally this is **real footage from your ROV** — set `ROV_SOURCE` below to a file path and the notebook will cut a 6-second, 1280×720, 30 FPS segment from it.

If no footage is available, the notebook **generates a synthetic "underwater inspection" clip** that has the properties that make underwater video hard to compress:

* **Blue-green colour cast and depth-dependent attenuation** (red light is absorbed first).
* **Moving caustics** — the rippling light patterns near the surface. They change every frame, which defeats temporal prediction.
* **Marine snow** — hundreds of small drifting particles, each one a tiny "surprise" for the motion estimator.
* **Sensor noise** — low light means high camera gain, which means noise that changes every frame.
* **Camera motion** — the ROV pans along a pipeline, then **cuts** to a second camera view at t = 4 s (this lets us see scene-cut detection later).

The reference is stored losslessly (FFV1 codec) so that every quality measurement compares against a perfect original. The encoders read an *uncompressed* copy (`source.yuv`), so the CPU time we measure is encoding work, not decoding of the reference.

> ⚠️ Compression results depend strongly on content. A synthetic clip is a teaching tool; **your final engineering decisions must be based on your own footage.**
""")

code(r'''
ROV_SOURCE = os.environ.get("ROV_SOURCE")   # e.g. "my_dive.mp4" — leave None for the synthetic clip
W, H, FPS, SECONDS = 1280, 720, 30, 6
N_FRAMES = FPS * SECONDS
SRC = WORK / "source.mkv"

def synth_underwater_clip(path, w=W, h=H, fps=FPS, n=N_FRAMES, seed=7):
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    pan = 3                                             # pixels per frame of camera pan
    tex_w = w + 1200
    # Seabed / pipeline texture: low-frequency "rock" + high-frequency detail
    lo = gaussian_filter(rng.standard_normal((h, tex_w)), 18); lo /= np.abs(lo).max()
    hi = gaussian_filter(rng.standard_normal((h, tex_w)), 1.5); hi /= np.abs(hi).max()
    tex = 0.55 + 0.25 * lo + 0.12 * hi
    yy = np.arange(h)[:, None]
    pipe = np.exp(-((yy - 0.58 * h) / (0.11 * h)) ** 2)                # a horizontal pipeline
    seams = (np.sin(np.arange(tex_w) / 55.0) > 0.985).astype(float)    # weld seams
    tex = tex * (1 - 0.6 * pipe) + pipe * (0.75 + 0.15 * hi + 0.4 * seams[None, :])
    growth = gaussian_filter((rng.random((h, tex_w)) > 0.996).astype(float), 3) * 25
    tex = np.clip(tex + growth * pipe, 0, 1.4)
    depth = np.linspace(0, 1, h)[:, None]
    water = np.array([18, 92, 110]) / 255.0                            # blue-green water colour
    tint = np.array([0.35, 0.85, 0.95])                                # red absorbed first
    xs = np.arange(w)[None, :]
    p_n = 350; px = rng.uniform(0, w, p_n); py = rng.uniform(0, h, p_n)
    vx = rng.normal(0.4, 0.5, p_n); vy = rng.normal(-0.6, 0.4, p_n)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        if i < int(0.66 * n):                                          # camera 1: pan along the pipe
            view = tex[:, i * pan:i * pan + w]; turb = 0.35
        else:                                                          # camera 2: closer, darker view
            off = 600 + (i - int(0.66 * n)) * 2
            view = np.roll(tex[:, off:off + w], h // 4, axis=0) * 0.85; turb = 0.5
        caustic = (np.sin(xs / 37.0 + 2.1 * t) * np.sin(yy / 23.0 - 1.7 * t + xs / 90.0)) ** 2
        light = 0.75 + 0.35 * caustic * np.exp(-3 * depth)
        lum = view * light * (1.05 - 0.55 * depth)
        rgb = lum[..., None] * tint[None, None, :]
        haze = turb * (0.4 + 0.6 * depth)[..., None]                   # turbidity: fade to water colour
        rgb = rgb * (1 - haze) + water[None, None, :] * haze
        px += vx; py += vy; px %= w; py %= h                           # marine snow
        ix, iy = px.astype(int), py.astype(int)
        for dx, dy, a in ((0, 0, 0.5), (1, 0, 0.25), (0, 1, 0.25)):
            np.add.at(rgb, ((iy + dy) % h, (ix + dx) % w), a)
        rgb += rng.normal(0, 0.004, rgb.shape)                         # sensor noise (camera gain)
        proc.stdin.write((np.clip(rgb, 0, 1) * 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()

if not SRC.exists():
    if ROV_SOURCE:
        run([FFMPEG, "-y", "-hide_banner", "-i", ROV_SOURCE, "-t", str(SECONDS), "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
             "-an", "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(SRC)])
    else:
        t0 = time.time(); tmp = WORK / "source_tmp.mkv"; synth_underwater_clip(tmp); tmp.rename(SRC)
        print(f"Synthetic clip generated in {time.time()-t0:.1f} s")

# Encoders read an uncompressed copy, so CPU measurements contain (almost) only encoding work.
SRC_RAW = WORK / "source.yuv"
if not SRC_RAW.exists():
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(SRC), "-f", "rawvideo", "-pix_fmt", "yuv420p", str(SRC_RAW)])
SRC_IN = ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", str(FPS), "-i", str(SRC_RAW)]
info = probe(SRC); print(info)
# Show three frames from the clip
fig, axs = plt.subplots(1, 3, figsize=(12, 2.6))
for ax, t in zip(axs, (0.5, 2.5, 5.0)):
    png = WORK / f"src_{t}.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(SRC), "-frames:v", "1", str(png)])
    ax.imshow(plt.imread(png)); ax.set_title(f"t = {t} s"); ax.axis("off")
plt.suptitle("Reference clip (lossless)", fontweight="bold"); plt.tight_layout(); plt.show()
''')

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 1 — How big is raw video?

**Question.** If a camera sent every pixel without compression, how much bandwidth would it need?

**Theory.** A video is a sequence of images. Each image has $W \times H$ pixels, each pixel needs some number of **bits per pixel** (bpp), and we send $f$ images per second:

$$
R_{\text{raw}} \;=\; W \times H \times \text{bpp} \times f \qquad [\text{bit/s}]
$$

| Symbol | Meaning | Example |
|---|---|---|
| $W \times H$ | resolution (pixels per frame) | 1920 × 1080 = 2 073 600 px |
| bpp | bits per pixel — depends on the **pixel format** | RGB24 = 24, YUYV 4:2:2 = 16, NV12 4:2:0 = 12 |
| $f$ | frame rate (frames per second) | 30 |

**Worked example — 1080p30 in RGB24:** $1920 \times 1080 \times 24 \times 30 = 1\,492\,992\,000$ bit/s ≈ **1.49 Gbit/s**. That is *one camera*, already **more than a whole Gigabit Ethernet link**.

Why the pixel formats differ: the eye is much more sensitive to brightness (luma, **Y**) than to colour (chroma, **U/V**). **4:2:0** keeps full-resolution luma but stores one U and one V sample for every 2×2 block of pixels, so each pixel costs $8 + \tfrac{8+8}{4} = 12$ bits instead of 24. We will come back to this in the slides.

> Units: in networking, **1 Mbit/s = 10⁶ bit/s** (decimal). Storage often uses MiB = 2²⁰ bytes. We use decimal bits everywhere in this notebook, and write **Mb/s** for megabits per second and **MB** for megabytes.
""")

code(r'''
PIXEL_FORMATS = {"RGB24 (8-bit RGB)": 24, "YUYV 4:2:2 (USB webcam raw)": 16, "NV12 / YUV420P 4:2:0": 12}
RESOLUTIONS = {"640×480": (640, 480), "1280×720": (1280, 720), "1920×1080": (1920, 1080), "3840×2160": (3840, 2160)}

def raw_mbps(w, h, fps, bpp):
    return w * h * bpp * fps / 1e6

rows = []
for rname, (w, h) in RESOLUTIONS.items():
    for fps in (15, 30, 60):
        row = {"resolution": rname, "fps": fps}
        for pname, bpp in PIXEL_FORMATS.items():
            row[pname] = raw_mbps(w, h, fps, bpp)
        rows.append(row)
raw_table = pd.DataFrame(rows)
print("Raw bandwidth of ONE camera, Mb/s")
display(raw_table.style.format({c: "{:,.0f}" for c in PIXEL_FORMATS}).hide(axis="index"))

one = raw_mbps(1920, 1080, 30, 24); eight = 8 * one
print(f"1 × 1080p30 RGB24 = {one:,.0f} Mb/s   |   8 cameras = {eight:,.0f} Mb/s = {eight/1000:.1f} Gb/s")
print(f"1 × 1080p30 NV12  = {raw_mbps(1920,1080,30,12):,.0f} Mb/s   |   8 cameras = {8*raw_mbps(1920,1080,30,12):,.0f} Mb/s")
''')

code(r'''
# Chart: one camera's raw bandwidth at 30 FPS vs the capacity of the links an ROV actually has.
LINKS = {"Fast Ethernet (100 Mb/s)": 100, "UVC isochronous max, one USB 2.0 camera (~197 Mb/s)": 196.6,
         "USB 2.0 signalling (480 Mb/s, shared per bus)": 480, "Gigabit Ethernet (1000 Mb/s)": 1000}
fig, ax = plt.subplots(figsize=(12, 4.6))
x = np.arange(len(RESOLUTIONS)); width = 0.26
for k, (pname, bpp) in enumerate(PIXEL_FORMATS.items()):
    vals = [raw_mbps(w, h, 30, bpp) for (w, h) in RESOLUTIONS.values()]
    ax.bar(x + (k - 1) * width, vals, width - 0.03, label=pname, color=PALETTE[k])
for (lname, cap), ls in zip(LINKS.items(), (":", "-.", "--", "-")):
    ax.axhline(cap, color="#52514e", ls=ls, lw=1.2)
    ax.text(1.01, cap, lname, fontsize=8, color="#52514e", ha="left", va="center", transform=ax.get_yaxis_transform())
ax.set_yscale("log"); ax.yaxis.set_major_formatter(FuncFormatter(mbps_fmt))
ax.set_xticks(x, RESOLUTIONS.keys()); ax.set_ylabel("Mb/s (log scale)")
ax.set_title("Raw bandwidth of ONE camera at 30 FPS vs. link capacity"); ax.legend(loc="upper left")
fig.subplots_adjust(left=0.08, right=0.68, bottom=0.12, top=0.9); plt.show()
''')

md(r"""
**Interpretation.**

* Raw 1080p30 from even **one** camera does not fit a Fast-Ethernet tether, and 8 raw 1080p cameras would need ~6–12 Gb/s. **Compression is not optional; it is the core of the system.**
* Look at the USB lines. A USB 2.0 UVC camera sending *uncompressed* YUYV can only do about 640×480@30 or 1280×720@~10. That is why most USB webcams switch to **MJPEG** (compressed inside the camera) at 720p and above — and why many student ROVs end up streaming MJPEG without ever deciding to.
* USB 2.0 bandwidth is **shared by every device on the same bus** (a hub does not add bandwidth). High-speed USB also limits *periodic* (isochronous) traffic to 80 % of each micro-frame, and many UVC cameras *reserve* a large isochronous slot even when sending small MJPEG frames. The classic symptom with 3–4 USB cameras on one hub is that the next camera fails to open (`No space left on device` / `VIDIOC_STREAMON` errors). **Before blaming the network, check `lsusb -t`.**

### Exercises
1. Your team's camera outputs YUYV 640×480 at 30 FPS. How many such cameras fit on one USB 2.0 bus (use 80 % of 480 Mb/s as the periodic budget)?
2. A 100 Mb/s tether must carry 8 cameras. What is the **maximum average bitrate per camera** if you keep 30 % headroom? (Answer: $100 \times 0.7 / 8 = 8.75$ Mb/s *before* protocol overhead.)
3. Why is "lower the resolution" a weak first response to a bandwidth problem? *(Hint: compare the ratio raw/compressed in Experiment 2.)*
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 2 — Your first encodes: H.264, H.265, MJPEG, AV1

**Question.** How much smaller does the same 6-second clip become with different codecs, and what does it cost in encoding time?

**Theory (short).**

| Codec | Idea | Uses previous frames? |
|---|---|---|
| **MJPEG** | Every frame is an independent JPEG image | ❌ intra-only |
| **H.264 / AVC** | Predicts each block from neighbours *or* from previous frames, codes only the difference | ✅ |
| **H.265 / HEVC** | Same idea, bigger and more flexible blocks (CTUs up to 64×64), better prediction tools | ✅ |
| **AV1** | Royalty-free successor to VP9, even more tools; expensive to encode in software | ✅ |

**The commands, line by line** (the H.264 one):

```bash
ffmpeg -y -i work/source.mkv \      # -y overwrite; -i input file
       -c:v libx264 \               # video codec = the x264 software H.264 encoder
       -preset medium \             # speed/efficiency trade-off (Experiment 4)
       -crf 23 \                    # constant-quality target: lower = better quality, bigger file (Experiment 3)
       -pix_fmt yuv420p \           # 4:2:0 chroma — what every hardware decoder and browser supports
       -an \                        # no audio
       work/e2_h264.mp4             # MP4 container
```

* `libx265` uses `-crf 28` as its default "visually similar" point — **CRF numbers are not comparable between codecs.**
* MJPEG uses `-q:v` (2 = best, 31 = worst) instead of CRF.
* `libsvtav1 -preset 8` is a fast SVT-AV1 setting; AV1 CRF runs from 0 to 63.

We also record **PSNR** and **SSIM** (explained properly in Experiment 6) so we are not comparing file sizes blindly.
""")

code(r'''
E2 = [
    ("H.264 (x264, CRF 23)",  "libx264",   ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"], "mp4"),
    ("H.265 (x265, CRF 28)",  "libx265",   ["-c:v", "libx265", "-preset", "medium", "-crf", "28", "-pix_fmt", "yuv420p",
                                             "-tag:v", "hvc1", "-x265-params", "log-level=error"], "mp4"),
    ("MJPEG (q:v 5)",         "mjpeg",     ["-c:v", "mjpeg", "-q:v", "5", "-pix_fmt", "yuvj420p"], "mkv"),
    ("AV1 (SVT-AV1, CRF 35)", "libsvtav1", ["-c:v", "libsvtav1", "-preset", "8", "-crf", "35", "-pix_fmt", "yuv420p"], "mkv"),
]
raw_bits = W * H * 12 * N_FRAMES   # 4:2:0 raw size of the clip, in bits
rows = []
for label, enc, args, ext in E2:
    if not HAS.get(enc):
        print(f"skip {label}: encoder {enc} not available in this FFmpeg build"); continue
    out = WORK / f"e2_{enc}.{ext}"
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, *args, "-an", str(out)])
    p = probe(out); psnr, ssim = quality(out, SRC)
    rows.append({"codec": label, "size_MB": p["size_bytes"] / 1e6, "bitrate_Mb/s": p["bitrate_mbps"],
                 "compression_ratio": raw_bits / (p["size_bytes"] * 8), "encode_fps": N_FRAMES / r["wall_s"],
                 "cores_used": r["cpu_s"] / r["wall_s"], "PSNR_dB": psnr, "SSIM": ssim})
e2 = pd.DataFrame(rows)
print(f"Raw 4:2:0 size of the clip: {raw_bits/8/1e6:.0f} MB  ({raw_mbps(W,H,FPS,12):.0f} Mb/s)")
display(e2.style.format({"size_MB": "{:.2f}", "bitrate_Mb/s": "{:.2f}", "compression_ratio": "{:,.0f}:1",
                         "encode_fps": "{:.0f}", "cores_used": "{:.1f}", "PSNR_dB": "{:.1f}", "SSIM": "{:.4f}"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(8, 3.4))
ax.barh(e2["codec"], e2["bitrate_Mb/s"], color=PALETTE[0], height=0.55)
for y, v in enumerate(e2["bitrate_Mb/s"]):
    ax.text(v, y, f"  {v:.2f} Mb/s", va="center", fontsize=9)
ax.invert_yaxis(); ax.set_xlabel("Average bitrate (Mb/s)"); ax.set_title("Same clip, four codecs (default-ish settings)")
plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation.**

* Even at default settings, the inter-frame codecs (H.264/H.265/AV1) are typically **several times smaller than MJPEG**, and **one to two orders of magnitude smaller than raw**. On a bandwidth-limited tether, *switching codec is usually worth far more than lowering resolution.*
* But look at the PSNR/SSIM columns before declaring a winner: the four encodes are **not at equal quality**. A fair comparison draws a whole *rate–quality curve* for each codec — we do that in Experiment 6.
* Look at **encode_fps** and **cores_used**. H.265 and AV1 buy their efficiency with CPU time. On a Raspberry Pi 5 (no hardware encoder) that CPU budget is the real constraint; on a Jetson Nano, the hardware encoder makes H.264/H.265 almost free for the CPU. → Experiment 10.
* MJPEG's one big advantage: every frame stands alone, so decoding is trivial, latency is minimal, and a lost frame never corrupts the next one.

### Exercises
1. Run `ffprobe -hide_banner work/e2_libx264.mp4` and identify: container, codec, profile, pixel format, resolution, frame rate, bitrate.
2. Re-encode MJPEG at `-q:v 2` and `-q:v 15`. How far does the bitrate move? Is MJPEG at `-q:v 15` still usable for piloting?
3. Which of these codecs can **your pilot's browser** decode? (Search "caniuse H.265" and test on the actual topside laptop.)
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 3 — Quality-based (CRF) vs bitrate-based encoding

**Question.** Should we tell the encoder *"give me this quality"* or *"give me this bitrate"*?

**Theory.**

* **CRF (Constant Rate Factor)** — *quality-based*. The encoder chooses a quantizer per frame so that perceived quality stays roughly constant. Easy scenes get few bits, complex scenes many. **Bitrate varies with content.** Each +6 CRF roughly halves the bitrate in x264.
* **Target bitrate with a VBV buffer** — *bitrate-based*. We specify `-b:v` (average), `-maxrate` (ceiling) and `-bufsize` (how much burst is tolerated). **Quality varies with content.** This is what live streaming over a fixed-capacity link needs.

$$
\text{bufsize} \approx \text{maxrate} \times \text{(tolerated burst time)} \qquad\Rightarrow\qquad \text{small bufsize} = \text{smoother bitrate} + \text{lower latency} - \text{lower quality on hard frames}
$$

> On an ROV, a tether has a hard capacity. A CRF stream can suddenly double its bitrate when the ROV stirs up sediment — exactly when the pilot needs the video most. This is why live systems use **capped** rate control (VBV / CBR), and use CRF mainly for **recording**.
""")

code(r'''
CRFS = [18, 23, 28, 33, 38, 43]
TARGETS_MBPS = [0.25, 0.5, 1, 2, 4, 8]
rows = []
for crf in CRFS:
    out = WORK / f"e3_crf{crf}.mp4"
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", "medium",
             "-crf", str(crf), "-pix_fmt", "yuv420p", "-an", str(out)])
    p = probe(out); psnr, ssim = quality(out, SRC)
    rows.append({"mode": "CRF", "setting": f"crf {crf}", "bitrate_Mb/s": p["bitrate_mbps"], "size_MB": p["size_bytes"]/1e6,
                 "encode_s": r["wall_s"], "PSNR_dB": psnr, "SSIM": ssim, "file": out})
for tgt in TARGETS_MBPS:
    out = WORK / f"e3_vbv{tgt}.mp4"; kb = int(tgt * 1000)
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", "medium",
             "-b:v", f"{kb}k", "-maxrate", f"{kb}k", "-bufsize", f"{kb // 2}k",   # 0.5 s of buffer
             "-pix_fmt", "yuv420p", "-an", str(out)])
    p = probe(out); psnr, ssim = quality(out, SRC)
    rows.append({"mode": "Target bitrate (VBV)", "setting": f"{tgt} Mb/s", "bitrate_Mb/s": p["bitrate_mbps"],
                 "size_MB": p["size_bytes"]/1e6, "encode_s": r["wall_s"], "PSNR_dB": psnr, "SSIM": ssim, "file": out})
e3 = pd.DataFrame(rows)
display(e3.drop(columns="file").style.format({"bitrate_Mb/s": "{:.2f}", "size_MB": "{:.2f}", "encode_s": "{:.1f}",
                                              "PSNR_dB": "{:.1f}", "SSIM": "{:.4f}"}).hide(axis="index"))
''')

code(r'''
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
for k, (mode, g) in enumerate(e3.groupby("mode", sort=False)):
    axs[0].plot(g["bitrate_Mb/s"], g["PSNR_dB"], "o-", label=mode, color=PALETTE[k])
    axs[1].plot(g["bitrate_Mb/s"], g["SSIM"], "o-", label=mode, color=PALETTE[k])
for _, r in e3[e3["mode"] == "CRF"].iterrows():
    axs[0].annotate(r["setting"], (r["bitrate_Mb/s"], r["PSNR_dB"]), textcoords="offset points", xytext=(6, -10), fontsize=8)
for ax, yl in zip(axs, ("PSNR (dB)", "SSIM")):
    ax.set_xscale("log"); ax.xaxis.set_major_formatter(FuncFormatter(mbps_fmt))
    ax.set_xlabel("Average bitrate (Mb/s, log)"); ax.set_ylabel(yl); ax.legend()
axs[0].set_title("Rate–quality curve (PSNR)"); axs[1].set_title("Rate–quality curve (SSIM)")
plt.tight_layout(); plt.show()
''')

md(r"""
Now the important part for live streaming: **how does the bitrate behave over time?** We match a VBV encode to the *same average bitrate* as CRF 23 and plot the bitrate in 200 ms windows. Remember the scene cut at t = 4 s.
""")

code(r'''
crf23 = e3[(e3["mode"] == "CRF") & (e3["setting"] == "crf 23")].iloc[0]
avg_kb = int(crf23["bitrate_Mb/s"] * 1000)
vbv_match = WORK / "e3_vbv_match.mp4"
run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", "medium",
     "-b:v", f"{avg_kb}k", "-maxrate", f"{avg_kb}k", "-bufsize", f"{avg_kb // 3}k", "-pix_fmt", "yuv420p", "-an", str(vbv_match)])

def windowed_mbps(path, win=0.2):
    pk = packets(path); bins = np.floor(pk["pts"] / win)
    s = pk.groupby(bins)["size"].sum() * 8 / win / 1e6
    return s.index.values * win, s.values, pk

fig, ax = plt.subplots(figsize=(10, 3.8))
for k, (label, path) in enumerate((("CRF 23 (quality-based)", crf23["file"]), (f"VBV, capped at {avg_kb/1000:.2f} Mb/s", vbv_match))):
    t, mb, pk = windowed_mbps(path)
    ax.step(t, mb, where="post", label=f"{label} — peak {mb.max():.2f} Mb/s", color=PALETTE[k])
ax.axvline(4.0, color="#52514e", ls=":", lw=1); ax.text(4.05, ax.get_ylim()[1]*0.92, "scene cut", fontsize=8, color="#52514e")
ax.set_xlabel("time (s)"); ax.set_ylabel("Mb/s in 200 ms windows"); ax.set_title("Same average bitrate, very different peaks")
ax.legend(); plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation.**

* The rate–quality curve has **diminishing returns**: the step from 0.5 → 1 Mb/s buys far more quality than 4 → 8 Mb/s. Somewhere on that curve is the "good enough for piloting" point — find it *with your footage and your pilots*, not by guessing.
* With CRF, the **peaks** (I-frames, scene cuts, sudden motion, sediment clouds) can be several times the average. A tether planned on *average* bitrate will congest on *peaks* → packet loss → corrupted video exactly when things get exciting.
* VBV trades those peaks for temporary quality drops. That is usually the right trade for a live link; record a CRF stream locally (on the ROV or topside) if you need high quality for later analysis.

### Exercises
1. From the CRF table, estimate the "half-bitrate CRF step" for x264 on this clip. Is it close to 6?
2. Repeat the VBV encode with `-bufsize` equal to 2× the bitrate. What happens to the peaks? What would that do to latency?
3. Which mode would you use for (a) the pilot's live view, (b) the recording used for a mission photomosaic or measurement task? Why?
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 4 — Encoder presets: speed vs efficiency

**Question.** x264 offers presets from `ultrafast` to `veryslow`. What do we gain and lose?

**Theory.** A preset bundles dozens of internal decisions: how hard to search for motion vectors (`me`, `subme`, `merange`), how many reference frames, how many B-frames, how many frames of **lookahead** to analyse, which block partitions to try, whether to use CABAC entropy coding, and so on. Slower presets search harder, so they find cheaper ways to describe the same picture → **fewer bits for the same quality** — at the price of CPU time.

We keep `-crf 23` constant and measure for each preset:

* **encode FPS** — can it keep up with 30 FPS live?
* **cores used** = CPU time / wall time — how much of the SBC it would eat.
* **bitrate and PSNR** — efficiency.
""")

code(r'''
PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
rows = []
for pr in PRESETS:
    out = WORK / f"e4_{pr}.mp4"
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", pr,
             "-crf", "23", "-pix_fmt", "yuv420p", "-an", str(out)])
    p = probe(out); psnr, ssim = quality(out, SRC)
    rows.append({"preset": pr, "encode_fps": N_FRAMES / r["wall_s"], "cores_used": r["cpu_s"] / r["wall_s"],
                 "cpu_ms_per_frame": 1000 * r["cpu_s"] / N_FRAMES, "bitrate_Mb/s": p["bitrate_mbps"], "PSNR_dB": psnr, "SSIM": ssim})
e4 = pd.DataFrame(rows)
display(e4.style.format({"encode_fps": "{:.0f}", "cores_used": "{:.1f}", "cpu_ms_per_frame": "{:.1f}",
                         "bitrate_Mb/s": "{:.2f}", "PSNR_dB": "{:.2f}", "SSIM": "{:.4f}"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(9, 4.4))
ax.plot(e4["cpu_ms_per_frame"], e4["bitrate_Mb/s"], "o-", color=PALETTE[0])
for _, r in e4.iterrows():
    ax.annotate(r["preset"], (r["cpu_ms_per_frame"], r["bitrate_Mb/s"]), textcoords="offset points", xytext=(6, 4), fontsize=8)
ax.set_xscale("log"); ax.set_xlabel("CPU time per frame (ms, log) — on THIS machine")
ax.set_ylabel("bitrate at CRF 23 (Mb/s)"); ax.set_title("x264 presets: CPU cost vs bits")
plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation.**

* Read the chart from left to right: each slower preset costs more CPU per frame; the bitrate saving shrinks fast after `medium`/`slow`. Note that CRF 23 is *not exactly* equal quality across presets (check the PSNR column) — `ultrafast` disables many tools, so its bitrate *and* quality both differ.
* For a live ROV encoder on an SBC **without** a hardware encoder, you will usually live at `ultrafast`–`veryfast` with `-tune zerolatency`. Raspberry Pi's own white paper measured 1080p30 at roughly 62–90 % of one Cortex-A76 core with an `ultrafast`/zerolatency configuration, and ~100–150 % of a core with a `superfast` high-quality configuration (see References).
* **CPU time per frame** is the number you can transfer between machines: measure it on the actual SBC, multiply by FPS × number of streams, and compare with the cores you can spare *after* the control software, telemetry and the web server.

### Exercises
1. Using `cpu_ms_per_frame` for `ultrafast`, how many 720p30 streams could **this** machine encode if you reserve one core for everything else?
2. Repeat this experiment **on your SBC** (Raspberry Pi 5 or Jetson Nano). By what factor is it slower than your laptop?
3. Why might a *faster* preset produce *lower* latency even if the machine is fast enough for `medium`? *(Hint: lookahead and B-frames — Experiment 9.)*
""")
