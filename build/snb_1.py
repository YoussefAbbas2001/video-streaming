"""Session notebook, part 1: start page, setup, Part 01 (water and architecture), Part 02 (bandwidth)."""
from snb_common import md, code, part, exp

md(r"""
<div style="border-radius:22px; padding:34px 30px 28px; background:linear-gradient(120deg, #C00000 0%, #6e0000 100%); color:#ffffff">
<div style="font-size:11px; letter-spacing:.32em; color:#ffc9c9">M.I.A ROBOTICS · VIDEO ENGINEERING SESSION</div>
<div style="font-size:34px; font-weight:800; margin:10px 0 6px">ROV Video Streaming Lab</div>
<div style="font-size:15px; color:#ffe1e1">Every experiment from the talk, in the order of the slides. Drag, encode, look.</div>
</div>

This notebook goes with `presentation/MIA_Video_Streaming.pptx`. Each red banner names the slide it belongs to, so you can open the matching experiment while the slide is on the screen.

**How to use it**

1. Run everything once: **Kernel → Restart Kernel and Run All Cells**. It takes 10–20 minutes the first time (it encodes a lot of video). After that, results are cached in `work/` and it's quick.
2. Then play with the panels. Panels marked **live** update while you drag. Panels marked **press Encode** re-encode real video with your settings.
3. Every number here is measured on *this* computer or calculated from a formula you can read in the cell. Anything that is a model or an estimate says so.

The test clip is a synthetic underwater scene (a pipeline, haze, marine snow, sensor noise). To use your own footage, set `ROV_SOURCE` before starting Jupyter: `ROV_SOURCE=my_dive.mp4 jupyter lab`.

{{TOC}}
""")

md(r"""
## Setup

Run these three cells and move on. They load the tools, make the test clip, and build the control panels. You don't need to read them to do the experiments, but everything below calls them, so they're short and plain.

```bash
pip install -r requirements.txt     # numpy pandas matplotlib scipy jupyterlab ipywidgets av
```
FFmpeg 5 or newer must be on your `PATH` (with `libx264`; `libx265` and `libsvtav1` are optional).
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

code(r'''
import hashlib
from IPython.display import HTML, Markdown, display

try:
    import ipywidgets as wdg
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

display(HTML("<style>.jp-OutputArea-output img, .output_png img {display:block; margin:0 auto}"
             " .jp-RenderedHTMLCommon table {margin-left:auto; margin-right:auto}</style>"))

MIA_RED = "#C00000"
GOOD, BAD, GREY = "#2e7d32", "#c62828", "#8a8a8a"
BATCH = os.environ.get("NB_BATCH") == "1"   # set when the notebook is run unattended (build/run_nb.py)


def rate(mbps):
    """1493 -> '1.49 Gb/s', 8.2 -> '8.2 Mb/s', 0.42 -> '0.42 Mb/s'."""
    if mbps >= 1000:
        return f"{mbps / 1000:.2f} Gb/s"
    return f"{mbps:,.0f} Mb/s" if mbps >= 10 else (f"{mbps:.1f} Mb/s" if mbps >= 1 else f"{mbps:.2f} Mb/s")


def cards(items):
    """A row of number cards. items: (label, value, note) or (label, value, note, good) with good = True/False/None."""
    html = []
    for it in items:
        label, value, note = it[:3]; good = it[3] if len(it) > 3 else None
        colour = {True: GOOD, False: BAD, None: GREY}[good]
        html.append(f'<div style="min-width:130px; padding:12px 16px; margin:5px; border-radius:14px; background:#ffffff; '
                    f'border:1px solid #ececec; box-shadow:0 2px 10px rgba(0,0,0,.05); text-align:center; display:inline-block">'
                    f'<div style="font-size:10.5px; letter-spacing:.1em; text-transform:uppercase; color:#8a8a8a">{label}</div>'
                    f'<div style="font-size:22px; font-weight:750; color:#1d1d1f; margin-top:3px">{value}</div>'
                    f'<div style="font-size:11.5px; color:{colour}">{note or "&nbsp;"}</div></div>')
    display(HTML(f'<div style="text-align:center">{"".join(html)}</div>'))


def note(text):
    display(HTML(f'<p style="text-align:center; color:#52514e; margin:6px 0">{text}</p>'))


def delta(cur, ref, fmt, higher_is_better):
    """Text + colour flag for a change against a baseline."""
    d = cur - ref
    if abs(d) < 1e-9:
        return "same as baseline", None
    return f"{fmt(d)} vs baseline", (d > 0) == higher_is_better


def encode_cached(args, tag, vf=None, ext="mp4", pix_fmt="yuv420p"):
    """Encode the test clip with these FFmpeg arguments, measure it, and cache the result in work/."""
    key = hashlib.sha1(json.dumps([args, vf, ext, pix_fmt]).encode()).hexdigest()[:12]
    out = WORK / f"tune_{tag}_{key}.{ext}"; meta = out.with_suffix(".json")
    if out.exists() and meta.exists():
        return {**json.loads(meta.read_text()), "file": out}
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, *(["-vf", vf] if vf else []), *args,
             "-pix_fmt", pix_fmt, "-an", str(out)])
    p = probe(out); psnr, ssim, pf = quality(out, SRC, per_frame=True)
    res = {"bitrate": p["bitrate_mbps"], "size": p["size_bytes"], "wall": r["wall_s"], "cpu": r["cpu_s"],
           "psnr": psnr, "ssim": ssim, "pf": [float(x) for x in pf]}
    meta.write_text(json.dumps(res))
    return {**res, "file": out}


def frame_png(path, t, tag):
    png = WORK / f"view_{tag}.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(png)])
    return plt.imread(png)


def gray(img):
    """RGB(A) float image from frame_png -> luma 0..255."""
    return img[..., :3] @ np.array([0.299, 0.587, 0.114]) * 255.0


PANELS = {}


def panel(name, title, subtitle, spec, render, live=False):
    """A control panel.

    spec:   {argument: (kind, options, default, label)}
            kind = int | float -> options (min, max, step) · options | toggle | dropdown -> list · check · text
    render: function(**values) that shows the result for one setting.
    live:   redraw on every change (cheap maths). Otherwise the panel waits for the Encode button.
    """
    header = (f'<div style="text-align:center; border-radius:14px; padding:12px 16px; margin:8px 0; color:#ffffff; '
              f'background:linear-gradient(115deg, {MIA_RED} 0%, #7d0000 100%)">'
              f'<div style="font-size:10px; letter-spacing:.3em; color:#ffd0d0">{"LIVE" if live else "PRESS ENCODE"}</div>'
              f'<div style="font-size:18px; font-weight:700; margin-top:2px">{title}</div>'
              f'<div style="font-size:12.5px; color:#ffe6e6; margin-top:2px">{subtitle}</div></div>')
    defaults = {k: s[2] for k, s in spec.items()}
    if not HAS_WIDGETS:
        display(HTML(header)); print("ipywidgets is not installed: showing the default setting only.")
        render(**defaults); return
    ws, style = {}, {"description_width": "initial"}
    for k, (kind, opts, default, label) in spec.items():
        lay = wdg.Layout(width="310px")
        if kind == "int":
            ws[k] = wdg.IntSlider(value=default, min=opts[0], max=opts[1], step=opts[2], description=label, style=style, layout=lay, continuous_update=False)
        elif kind == "float":
            ws[k] = wdg.FloatSlider(value=default, min=opts[0], max=opts[1], step=opts[2], description=label, style=style, layout=lay, continuous_update=False)
        elif kind == "options":
            ws[k] = wdg.SelectionSlider(options=opts, value=default, description=label, style=style, layout=lay, continuous_update=False)
        elif kind == "dropdown":
            ws[k] = wdg.Dropdown(options=opts, value=default, description=label, style=style, layout=lay)
        elif kind == "toggle":
            ws[k] = wdg.ToggleButtons(options=opts, value=default, description=label, style={**style, "button_width": "auto"})
        elif kind == "check":
            ws[k] = wdg.Checkbox(value=default, description=label, style=style, indent=False, layout=lay)
        elif kind == "text":
            ws[k] = wdg.Text(value=default, description=label, style=style, layout=wdg.Layout(width="640px"), continuous_update=False)
    out = wdg.Output(layout=wdg.Layout(width="100%"))
    status = wdg.HTML()
    button = wdg.Button(description="Encode", icon="play", button_style="danger", layout=wdg.Layout(width="160px"))

    def refresh(*_):
        t0 = time.perf_counter(); status.value = "<i>working…</i>"; button.disabled = True
        with out:
            out.clear_output(wait=True)
            try:
                render(**{k: w.value for k, w in ws.items()})
                status.value = f'<span style="color:{GREY}">updated in {time.perf_counter() - t0:.1f} s</span>'
            except Exception as exc:   # show the problem in the panel instead of breaking the widget
                print(f"This setting failed: {exc}"); status.value = f'<span style="color:{BAD}">failed</span>'
        button.disabled = False

    wide = [w for w in ws.values() if isinstance(w, (wdg.ToggleButtons, wdg.Text))]
    grid_items = [w for w in ws.values() if w not in wide]
    grid = wdg.GridBox(grid_items, layout=wdg.Layout(grid_template_columns="repeat(3, 320px)", justify_content="center", grid_gap="4px 10px"))
    rows = [wdg.HTML(header), *[wdg.HBox([w], layout=wdg.Layout(justify_content="center")) for w in wide], grid]
    if live:
        for w in ws.values():
            w.observe(refresh, names="value")
        rows.append(wdg.HBox([status], layout=wdg.Layout(justify_content="center")))
    else:
        button.on_click(refresh)
        rows.append(wdg.HBox([button, status], layout=wdg.Layout(justify_content="center", align_items="center", grid_gap="12px")))
    rows.append(out)
    display(wdg.VBox(rows, layout=wdg.Layout(border="1px solid #efefef", padding="0 8px 10px", width="100%")))
    PANELS[name] = {"widgets": ws, "button": button, "refresh": refresh, "out": out}
    if BATCH:   # unattended run: draw the default straight into the cell so the saved notebook shows a result
        status.value = f'<span style="color:{GREY}">default setting shown: run this cell to use the controls</span>'
        render(**defaults)
    else:
        refresh()


print("Panels ready" + ("" if HAS_WIDGETS else " (static mode: pip install ipywidgets for the controls)"))
''')

# =================================================================================================== PART 01
part("01", "Underwater video and our architecture", "3–11", "What the water does to the picture, and where our video gets compressed.")

exp(6, "Physics first", "What does the water cost in bits?", "Murky, noisy water is the most expensive video there is.", "encode")
md(r"""
**Try it.** The panel films a small synthetic scene with the water settings you choose and encodes it with H.264 at the same quality (CRF 23). Push **sensor noise** up, or turn the **light** down (the camera raises its gain, so noise grows). The picture hardly changes. The bitrate does.
""")
code(r'''
from scipy.ndimage import gaussian_filter

WW, WH, W_SECONDS = 640, 360, 2
_rng = np.random.default_rng(3)
_lo = gaussian_filter(_rng.standard_normal((WH, WW + 400)), 12); _lo /= np.abs(_lo).max()
_hi = gaussian_filter(_rng.standard_normal((WH, WW + 400)), 1.2); _hi /= np.abs(_hi).max()
_yy = np.arange(WH)[:, None]
_pipe = np.exp(-((_yy - 0.6 * WH) / (0.1 * WH)) ** 2)
SEABED = (0.55 + 0.25 * _lo + 0.12 * _hi) * (1 - 0.6 * _pipe) + _pipe * (0.75 + 0.15 * _hi)
WATER_RGB, RED_LOSS = np.array([18, 92, 110]) / 255, np.array([0.35, 0.85, 0.95])


def water_frames(turbidity, particles, noise, light, n, seed=1):
    """Frames of a camera panning over the seabed. The camera's gain makes up for low light, so noise grows as 1/light."""
    rng = np.random.default_rng(seed)
    depth = np.linspace(0, 1, WH)[:, None]
    px, py = rng.uniform(0, WW, particles), rng.uniform(0, WH, particles)
    vx, vy = rng.normal(0.4, 0.5, particles), rng.normal(-0.6, 0.4, particles)
    for i in range(n):
        lum = SEABED[:, 2 * i:2 * i + WW] * (1.05 - 0.55 * depth)
        rgb = lum[..., None] * RED_LOSS
        haze = (turbidity * (0.4 + 0.6 * depth))[..., None]
        rgb = rgb * (1 - haze) + WATER_RGB * haze
        if particles:
            px, py = (px + vx) % WW, (py + vy) % WH
            np.add.at(rgb, (py.astype(int), px.astype(int)), 0.5)
        if noise:
            rgb = rgb + rng.normal(0, noise / light, rgb.shape)
        yield (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def water_bitrate(turbidity, particles, noise, light):
    out = WORK / f"water_{turbidity:.2f}_{particles}_{noise}_{light}.mp4"
    if not out.exists():
        p = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WW}x{WH}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                              "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        for f in water_frames(turbidity, particles, noise, light, FPS * W_SECONDS):
            p.stdin.write(f.tobytes())
        p.stdin.close(); p.wait()
    return out.stat().st_size * 8 / W_SECONDS / 1e6


CLEAR_WATER = water_bitrate(0.35, 0, 0, 1.0)


def water_view(turbidity, particles, noise, light):
    mbps = water_bitrate(turbidity, particles, noise, light)
    frame = next(water_frames(turbidity, particles, noise, light, 1))
    cards([("bitrate at CRF 23", rate(mbps), "same quality target every time"),
           ("clear, still water", rate(CLEAR_WATER), "no particles, no noise"),
           ("cost of this water", f"{mbps / CLEAR_WATER:.1f}×", "more bits than clear water", mbps / CLEAR_WATER < 1.5)])
    plt.figure(figsize=(8, 4.5)); plt.imshow(frame); plt.axis("off")
    plt.title(f"turbidity {turbidity:.2f} · {particles} particles · noise {noise} · light {light}", fontsize=10); plt.show()


panel("water", "The price of murky water", "Same encoder, same quality target: only the water changes",
      {"turbidity": ("float", (0, 0.8, 0.05), 0.35, "turbidity (haze)"),
       "particles": ("int", (0, 1500, 50), 350, "marine snow particles"),
       "noise": ("options", [0, 0.002, 0.004, 0.008, 0.016, 0.03], 0.004, "sensor noise"),
       "light": ("options", [0.25, 0.5, 0.75, 1.0], 1.0, "light (1 = bright)")}, water_view)
''')
md(r"""
**Look for**
- Noise and particles are new, random detail in every frame. The encoder can't predict them from the last frame, so it pays for them.
- Halving the light doubles the noise after the camera's gain. Good lights are a bandwidth saving.
- Haze on its own is cheap: it *removes* detail. It's bad for the pilot, not for the tether.
""")

exp(9, "Camera choice", "Will the USB bus take another camera?", "USB 2.0 is 480 Mb/s for the whole bus, and cameras book their share in advance.", "live")
md(r"""
**Try it.** Add cameras until one won't start. Then switch the format from raw YUYV to MJPEG. Tick *camera books its maximum* to see why some cheap MJPEG cameras still fail.

This is a model of the bus budget, not a measurement: on the ROV, confirm with `lsusb -t` and `dmesg` (look for `No space left on device`).
""")
code(r'''
USB_BUDGET = {"USB 2.0": 0.8 * 480, "USB 3.0": 0.9 * 4000}   # periodic share; USB 3 after 8b/10b coding (approximate)
ISO_MAX_USB2 = 3 * 1024 * 8 * 8000 / 1e6                      # 196.6 Mb/s: the most one high-speed camera can book
CAM_RES = {"320×240": (320, 240), "640×480": (640, 480), "1280×720": (1280, 720), "1920×1080": (1920, 1080)}
MJPEG_BPP = 0.34                                               # measured at good quality (Activity 1, card B)


def usb_view(cams, fmt, res, fps, bus, books_max):
    w, h = CAM_RES[res]
    need = w * h * fps * (16 if fmt == "raw YUYV" else MJPEG_BPP) / 1e6
    booked = ISO_MAX_USB2 if (fmt == "MJPEG" and books_max and bus == "USB 2.0") else need
    budget = USB_BUDGET[bus]
    too_big = bus == "USB 2.0" and need > ISO_MAX_USB2
    fit = 0 if too_big else min(cams, int(budget // booked))
    cards([("one camera needs", rate(need), fmt),
           ("one camera books", rate(booked), "its share of the bus"),
           ("bus budget", rate(budget), f"{bus}, periodic share"),
           ("cameras that start", f"{fit} of {cams}", "camera too big for USB 2.0 on its own" if too_big else
            ("all fine" if fit == cams else f"camera {fit + 1} fails"), fit == cams)])
    used = np.cumsum([booked] * cams)
    plt.figure(figsize=(9, 2.8))
    plt.bar(range(1, cams + 1), [booked] * cams, bottom=used - booked,
            color=[GOOD if (u <= budget and not too_big) else BAD for u in used], width=0.6)
    plt.axhline(budget, color="#52514e", ls="--", lw=1.2); plt.text(cams + 0.45, budget, " budget", va="center", fontsize=9)
    plt.xlabel("camera number"); plt.ylabel("bus booked (Mb/s)"); plt.xticks(range(1, cams + 1))
    plt.title("Each camera stacks its booking on the same bus"); plt.tight_layout(); plt.show()


panel("usb", "USB bus budget", "Raw video eats the bus; MJPEG fits more cameras",
      {"fmt": ("toggle", ["raw YUYV", "MJPEG"], "raw YUYV", "format"),
       "bus": ("toggle", ["USB 2.0", "USB 3.0"], "USB 2.0", "bus"),
       "cams": ("int", (1, 8, 1), 4, "cameras on this bus"),
       "res": ("options", list(CAM_RES), "640×480", "resolution"),
       "fps": ("options", [5, 10, 15, 30], 30, "fps"),
       "books_max": ("check", None, False, "camera books its maximum (common with cheap MJPEG cameras)")}, usb_view, live=True)
''')
md(r"""
**Look for**
- Raw 640×480 at 30 fps is 147 Mb/s per camera: two fit on one USB 2.0 bus, the third fails. That's slide 14 and Activity 1, card A.
- A USB 2.0 camera plugged into a USB 3.0 port still uses the USB 2.0 part of the controller. The USB 3.0 setting only helps with USB 3 cameras.
- The fix is rarely "lower the resolution": use MJPEG modes and spread cameras over separate controllers.
""")

# =================================================================================================== PART 02
part("02", "Bandwidth engineering", "12–18", "Count the bits before you plug anything in.")

exp("13–14", "Counting bits", "How big is raw video?", "R = W × H × bits per pixel × frames per second", "live")
md(r"""
$$R_{\text{raw}} = W \times H \times \text{bpp} \times f$$

Worked out for one 1080p camera in RGB: $1920 \times 1080 \times 24 \times 30 = 1.49$ Gb/s. That's one camera, already bigger than a gigabit link.

**Try it.** Pick a camera and a count. The chart compares the total with the links we actually have.
""")
code(r'''
PIXEL_FORMATS = {"RGB24": 24, "YUYV 4:2:2": 16, "NV12 4:2:0": 12}
RESOLUTIONS = {"640×480": (640, 480), "1280×720": (1280, 720), "1920×1080": (1920, 1080), "3840×2160": (3840, 2160)}
LINKS = {"Fast Ethernet tether": 100, "one USB 2.0 camera (max)": 196.6, "USB 2.0 bus": 480, "Gigabit Ethernet": 1000}


def raw_mbps(w, h, fps, bpp):
    return w * h * bpp * fps / 1e6


def raw_view(res, fmt, fps, cams):
    w, h = RESOLUTIONS[res]; one = raw_mbps(w, h, fps, PIXEL_FORMATS[fmt]); total = one * cams
    cards([("one camera", rate(one), f"{res} {fmt} @ {fps}"),
           (f"{cams} cameras", rate(total), "uncompressed"),
           ("vs 100 Mb/s tether", f"{total / 100:,.1f}×", "fits" if total <= 100 else "does not fit", total <= 100),
           ("vs gigabit", f"{total / 1000:,.2f}×", "fits" if total <= 1000 else "does not fit", total <= 1000)])
    fig, ax = plt.subplots(figsize=(10, 2.9))
    ax.barh([0], [total], color=MIA_RED, height=0.45)
    for k, ((name, cap), ls) in enumerate(zip(LINKS.items(), (":", "-.", "--", "-"))):
        ax.axvline(cap, color="#52514e", ls=ls, lw=1.1)
        ax.text(cap * 1.04, 0.62 - 0.16 * (k % 2), f"{name} ({cap:g})", fontsize=8, color="#52514e", va="center")
    ax.set_xscale("log"); ax.set_xlim(10, max(total, 1000) * 3); ax.set_ylim(-0.4, 0.75); ax.set_yticks([])
    ax.set_xlabel("Mb/s (log scale)"); ax.set_title(f"{rate(total)} of raw video against our links"); plt.tight_layout(); plt.show()


panel("raw", "Raw bandwidth", "Uncompressed video against the links we own",
      {"fmt": ("toggle", list(PIXEL_FORMATS), "RGB24", "pixel format"),
       "res": ("options", list(RESOLUTIONS), "1920×1080", "resolution"),
       "fps": ("options", [10, 15, 25, 30, 60], 30, "fps"),
       "cams": ("int", (1, 8, 1), 1, "cameras")}, raw_view, live=True)
''')
md(r"""
**Look for**
- Nothing raw above 640×480 fits a 100 Mb/s tether, and eight raw 1080p cameras need about 12 Gb/s. Compression isn't an option to tune; it's the whole system.
- The pixel format alone changes the size by 2×: RGB 24, YUYV 16, NV12 12 bits per pixel (slide 21 explains why).
""")

exp(15, "Counting bits", "One hour of video, in Egyptian pounds", "Compression makes video about 300× cheaper.", "live")
md(r"""
**Try it.** Pick a stream and a price. Prices are the WE entry package from 1 Nov 2026: 100 GB for EGP 171 with VAT, about EGP 1.71 per GB. They change often: check te.eg and type the new price in.
""")
code(r'''
STREAMS_EGP = {"Raw RGB 1080p30": 1493, "Raw 4:2:0 1080p30": 746, "MJPEG 720p30": 8.2,
               "H.264 HD streaming": 5, "Our pilot camera (H.264)": 2}


def egp_view(stream, hours, price_gb, package_gb, speed_MBps):
    mbps = STREAMS_EGP[stream]
    gb = mbps * hours * 3600 / 8 / 1000
    lasts_h = package_gb / (mbps * 3600 / 8 / 1000)
    download_h = gb * 1000 / speed_MBps / 3600
    lasts = f"{lasts_h * 60:.0f} minutes" if lasts_h < 1 else f"{lasts_h:,.0f} hours"
    took = f"{download_h * 60:.1f} minutes" if download_h < 1 else f"{download_h:,.1f} hours"
    cards([("data", f"{gb:,.2f} GB", f"{hours} h of {stream}"),
           ("cost", f"EGP {gb * price_gb:,.2f}", f"at EGP {price_gb}/GB", gb * price_gb < 50),
           (f"{package_gb} GB package lasts", lasts, "of this stream"),
           ("download time", took, f"at {speed_MBps} MB/s")])


panel("egp", "Video in Egyptian pounds", "The same hour, raw or compressed",
      {"stream": ("dropdown", list(STREAMS_EGP), "Raw RGB 1080p30", "stream"),
       "hours": ("int", (1, 24, 1), 1, "hours"),
       "price_gb": ("options", [1.0, 1.25, 1.5, 1.71, 2.0, 2.5], 1.71, "EGP per GB"),
       "package_gb": ("options", [100, 150, 200, 300], 100, "package (GB)"),
       "speed_MBps": ("options", [1.25, 3.75, 10, 12.5], 10, "download speed (MB/s)")}, egp_view, live=True)
''')
md(r"""
**Look for**
- Raw: about EGP 1,150 for the hour, and the month's 100 GB lasts nine minutes. H.264 at 5 Mb/s: about EGP 3.85.
- A 30 Mb/s line (3.75 MB/s) would need about 50× more speed just to carry raw 1080p30 live.
""")

exp(16, "Activity 1", "Check your card", "Raw → compressed → overhead → 70 % budget → verdict → measurement", "live")
md(r"""
Do the card on paper first. Then pick your card here and tick **show the working**.
""")
code(r'''
A1_CARDS = {
    "A": ("8 USB cameras, raw YUYV 640×480 @ 30 fps, all on one USB 2.0 hub.",
          [("raw per camera", "640 × 480 × 16 × 30 = 147.5 Mb/s"), ("raw total", "8 × 147.5 = 1,180 Mb/s"),
           ("compressed", "none: raw video crosses the USB bus"), ("budget", "USB periodic share = 80 % of 480 = 384 Mb/s"),
           ("verdict", "OVER on the USB bus, not the tether: only 2 cameras fit"),
           ("measure", "lsusb -t (all on one bus?), start cameras one by one, dmesg: 'No space left on device'")]),
    "B": ("8 cameras, MJPEG 1280×720 @ 30 fps over HTTP, 100 Mb/s tether, MJPEG ≈ 0.34 bits per pixel.",
          [("raw per camera", "1280 × 720 × 16 × 30 = 442 Mb/s (YUYV)"), ("compressed", "0.34 × 1280 × 720 × 30 = 9.4 Mb/s each → 75.2 Mb/s"),
           ("on the wire", "+6 % for HTTP/TCP → about 79.7 Mb/s"), ("budget", "70 % of 100 = 70 Mb/s"),
           ("verdict", "TIGHT, effectively over: no room for keyframe peaks or control"),
           ("measure", "the real MJPEG bitrate: iftop, or record 30 s and divide size by time")]),
    "C": ("8 cameras, H.264 1920×1080 @ 30 fps at 4 Mb/s each, RTP/UDP, 100 Mb/s tether, all encoded by a Jetson Nano.",
          [("raw per camera", "1920 × 1080 × 12 × 30 = 746 Mb/s (4:2:0)"), ("compressed", "8 × 4 = 32 Mb/s"),
           ("on the wire", "+5 % for RTP/UDP → about 33.7 Mb/s = 48 %"), ("tether", "OK"),
           ("verdict", "the hidden bottleneck: the Nano encodes 4 × 1080p30, so 8 is 2× over its encoder"),
           ("measure", "tegrastats (encoder load), dropped frames; or let IP cameras encode")]),
    "D": ("1 camera H.264 1080p30 at 6 Mb/s (main) + 7 cameras H.264 640×360 @ 15 fps at 0.5 Mb/s (substreams), RTP/UDP, 100 Mb/s.",
          [("raw", "main 746 Mb/s; each substream 640 × 360 × 12 × 15 = 41.5 Mb/s"), ("compressed", "6 + 7 × 0.5 = 9.5 Mb/s"),
           ("on the wire", "+5 % → about 10 Mb/s = 14 % of the link"), ("verdict", "OK, lots of headroom"),
           ("measure", "do the cameras really offer substreams? camera web page, ffprobe; measure real bitrates")]),
}


def a1_view(card, show):
    text, steps = A1_CARDS[card]
    html = f'<div style="max-width:760px; margin:6px auto; padding:14px 18px; border-radius:14px; border:1px solid #ececec">' \
           f'<div style="font-size:11px; letter-spacing:.2em; color:{MIA_RED}">CARD {card}</div><div style="font-size:15px; margin-top:4px">{text}</div>'
    if show:
        html += "".join(f'<div style="margin-top:8px"><b>{k}</b>: {v}</div>' for k, v in steps)
    else:
        html += f'<div style="margin-top:10px; color:{GREY}">Work it out on paper, then tick "show the working".</div>'
    display(HTML(html + "</div>"))


panel("a1", "Activity 1 answer check", "Scoring: arithmetic 4 · verdict 3 · measurement 3 · +3 for a hidden bottleneck",
      {"card": ("toggle", list(A1_CARDS), "A", "card"), "show": ("check", None, False, "show the working")}, a1_view, live=True)
''')

exp(17, "Measured", "Same clip, four codecs", "Compression is the core of the system: change the codec, not the picture size.", "encode")
md(r"""
First a fixed comparison at typical settings, then a panel where you pick the codec and a quality level from 1 (smallest file) to 10 (best picture).
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
code(r'''
CODECS = {   # quality level 1..10 -> each encoder's own scale
    "H.264 (x264)": ("libx264", lambda lv: ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(45 - 3 * lv)], f"CRF", "mp4", "yuv420p"),
    "H.265 (x265)": ("libx265", lambda lv: ["-c:v", "libx265", "-preset", "veryfast", "-crf", str(45 - 3 * lv), "-x265-params", "log-level=error"], "CRF", "mp4", "yuv420p"),
    "MJPEG":        ("mjpeg",   lambda lv: ["-c:v", "mjpeg", "-q:v", str(max(2, 31 - 3 * lv))], "q:v", "mkv", "yuvj420p"),
    "AV1 (SVT-AV1)": ("libsvtav1", lambda lv: ["-c:v", "libsvtav1", "-preset", "10", "-crf", str(60 - 4 * lv)], "CRF", "mkv", "yuv420p"),
}


def codec_view(codec, level):
    enc, mk, qname, ext, pix = CODECS[codec]
    if not HAS.get(enc):
        print(f"{enc} is not in this FFmpeg build."); return
    args = mk(level); res = encode_cached(args, "codec", ext=ext, pix_fmt=pix)
    cards([("setting", f"{qname} {args[args.index('-crf') + 1] if '-crf' in args else args[args.index('-q:v') + 1]}", codec),
           ("bitrate", rate(res["bitrate"]), f"{raw_bits / (res['size'] * 8):,.0f} : 1 vs raw"),
           ("SSIM", f"{res['ssim']:.3f}", "0.95+ looks good", res["ssim"] >= 0.95),
           ("encode speed", f"{N_FRAMES / res['wall']:.0f} fps", "real time needs 30", N_FRAMES / res["wall"] >= FPS)])
    y0, x0 = int(0.48 * H), int(0.40 * W)
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
    for ax, (img, cap) in zip(axs, ((frame_png(SRC, 2.0, "codec_ref"), "original"), (frame_png(res["file"], 2.0, "codec_enc"), f"{codec}, level {level}"))):
        ax.imshow(img[y0:y0 + H // 4, x0:x0 + W // 4]); ax.set_title(f"zoom · {cap}", fontsize=9); ax.axis("off")
    plt.tight_layout(); plt.show()


panel("codec", "Pick a codec", "Quality 1 = smallest file, 10 = best picture",
      {"codec": ("toggle", list(CODECS), "H.264 (x264)", "codec"), "level": ("int", (1, 10, 1), 6, "quality level")}, codec_view)
''')
md(r"""
**Look for**
- At the same SSIM, MJPEG needs several times the bits of H.264. On the slide: raw 332 → MJPEG 8.2 → H.264 1.5 Mb/s.
- Encode speed matters as much as size on the ROV: H.265 and AV1 buy their savings with CPU.
- Halving width and height divides the pixels by 4 and throws away detail. Switching codec saves more and keeps the detail.
""")

exp(18, "Words that get mixed up", "What does one packet cost on the wire?", "Bitrate, capacity, throughput, headroom: RTP adds about 5 %.", "live")
md(r"""
**Try it.** Change the payload size and watch the overhead. Small packets waste a lot; big ones risk fragmentation (slide 78). MPEG-TS packs 7 × 188-byte packets per datagram, so its payload size is fixed.
""")
code(r'''
def packet_view(proto, payload, video_mbps):
    if proto == "RTP over UDP":
        pay, hdr = payload, {"RTP": 12, "UDP": 8, "IPv4": 20, "Ethernet + gap": 38}
    else:
        pay, hdr = 7 * 184, {"TS headers (7 × 4)": 28, "UDP": 8, "IPv4": 20, "Ethernet + gap": 38}
    wire = pay + sum(hdr.values()); over = wire / pay - 1; pps = video_mbps * 1e6 / 8 / pay
    cards([("overhead", f"{over:.1%}", "on top of the video", over < 0.08),
           ("on the wire", rate(video_mbps * (1 + over)), f"for {rate(video_mbps)} of video"),
           ("packets per second", f"{pps:,.0f}", f"{wire} bytes each"),
           ("plan with", rate(video_mbps * (1 + over) / 0.7), "link size for 70 % use")])
    fig, ax = plt.subplots(figsize=(10, 1.6)); left = 0
    for k, (name, b) in enumerate([("video payload", pay), *hdr.items()]):
        ax.barh(0, b, left=left, color=[MIA_RED, *PALETTE][k], edgecolor="white", height=0.6)
        if b > 40: ax.text(left + b / 2, 0, f"{name}\n{b} B", ha="center", va="center", fontsize=8, color="white")
        left += b
    ax.set_xlim(0, left); ax.set_yticks([]); ax.set_xlabel("bytes on the wire for one packet"); plt.tight_layout(); plt.show()


panel("packet", "Packet overhead", "Every packet carries headers; small packets pay the most",
      {"proto": ("toggle", ["RTP over UDP", "MPEG-TS over UDP"], "RTP over UDP", "transport"),
       "payload": ("int", (200, 1460, 20), 1460, "RTP payload (bytes)"),
       "video_mbps": ("options", [0.5, 1, 2, 4, 8, 20, 50], 4, "video (Mb/s)")}, packet_view, live=True)
''')
md(r"""
**Look for**
- 1,460-byte RTP payloads: about 5 %. MPEG-TS: about 7 %. Below 500 bytes the headers start to matter.
- *Bitrate* is what the encoder makes, *capacity* what the link negotiates, *throughput* what `iperf3` measures, and *headroom* the 30 % you leave free on purpose.
""")
