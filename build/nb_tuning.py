# Interactive "Try it yourself" tuning panels. Inserted into the cell list by make_notebook.py.
# Each entry: (anchor text that must appear in the cell the panel goes AFTER, [(kind, text), ...])

HELPER_MD = r"""
### 0.2 Interactive tuning panels

Experiments 3, 4, 5, 7 and 8 end with a red **Try it yourself** panel. Move the controls, press **Encode**, and the panel re-encodes the reference clip with *your* settings. It then shows the measured result next to the experiment's baseline.

* Results are cached in `work/`, so returning to a setting you already tried is instant.
* Panels need `ipywidgets` (included in `requirements.txt`). Without it they show the default setting only.
* Want more knobs, other codecs or your own footage? The stand-alone **ROV Encoding Lab** app (`encoding_lab/`) is the big brother of these panels.
"""

HELPER_CODE = r'''
import hashlib
from IPython.display import HTML, display

try:
    import ipywidgets as wdg
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

# Centre figures and tables when this notebook runs live in Jupyter (purely cosmetic).
display(HTML("<style>.jp-OutputArea-output img, .output_png img {display:block; margin:0 auto}"
             " .jp-RenderedHTMLCommon table {margin-left:auto; margin-right:auto}</style>"))

MIA_RED = "#C00000"
BATCH = os.environ.get("NB_BATCH") == "1"   # set by the build script that executes this notebook unattended

def cards(items):
    """Centred row of metric cards. items: (label, value, note) or (label, value, note, good) with good ∈ {True, False, None}."""
    html = []
    for it in items:
        label, value, note = it[:3]; good = it[3] if len(it) > 3 else None
        colour = {True: "#2e7d32", False: "#c62828", None: "#8a8a8a"}[good]
        html.append(f'<div style="min-width:120px; padding:10px 14px; margin:5px; border-radius:12px; background:#ffffff; '
                    f'border:1px solid #e4e4e4; box-shadow:0 1px 6px rgba(0,0,0,.06); text-align:center; display:inline-block">'
                    f'<div style="font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; color:#8a8a8a">{label}</div>'
                    f'<div style="font-size:21px; font-weight:700; color:#262626; margin-top:2px">{value}</div>'
                    f'<div style="font-size:11px; color:{colour}">{note or "&nbsp;"}</div></div>')
    display(HTML(f'<div style="text-align:center">{"".join(html)}</div>'))

def delta(cur, ref, fmt, higher_is_better):
    """Text + colour flag for a change against a baseline."""
    d = cur - ref
    if abs(d) < 1e-9:
        return "same as baseline", None
    return f"{fmt(d)} vs baseline", (d > 0) == higher_is_better

def encode_cached(args, tag, vf=None, ext="mp4"):
    """Encode the reference clip with x264/FFmpeg arguments `args`, measure it, and cache the result in work/."""
    key = hashlib.sha1(json.dumps([args, vf, ext]).encode()).hexdigest()[:12]
    out = WORK / f"tune_{tag}_{key}.{ext}"; meta = out.with_suffix(".json")
    if out.exists() and meta.exists():
        return {**json.loads(meta.read_text()), "file": out}
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, *(["-vf", vf] if vf else []), *args,
             "-pix_fmt", "yuv420p", "-an", str(out)])
    p = probe(out); psnr, ssim, pf = quality(out, SRC, per_frame=True)
    res = {"bitrate": p["bitrate_mbps"], "size": p["size_bytes"], "wall": r["wall_s"], "cpu": r["cpu_s"],
           "psnr": psnr, "ssim": ssim, "pf": [float(x) for x in pf]}
    meta.write_text(json.dumps(res))
    return {**res, "file": out}

def frame_png(path, t, tag):
    png = WORK / f"view_{tag}.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(png)])
    return plt.imread(png)

PANELS = {}

def tuning_panel(name, title, subtitle, spec, render, live=False):
    """Build a centred control panel.

    spec:   {arg: (kind, options, default, label)}; kind ∈ int | float | options | toggle | check
            int/float options = (min, max, step); options/toggle options = list of values.
    render: function(**values) that prints cards and draws charts for one setting.
    live:   re-render on every change (for cheap calculations) instead of waiting for the Encode button.
    """
    header = (f'<div style="text-align:center; background-color:{MIA_RED}; color:#ffffff; border-radius:14px; '
              f'padding:12px 14px; margin:8px 0">'
              f'<div style="font-size:10px; letter-spacing:.3em; color:#ffd0d0">TRY IT YOURSELF</div>'
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
        elif kind == "toggle":
            ws[k] = wdg.ToggleButtons(options=opts, value=default, description=label, style={**style, "button_width": "auto"})
        elif kind == "check":
            ws[k] = wdg.Checkbox(value=default, description=label, style=style, indent=False, layout=wdg.Layout(width="310px"))
    out = wdg.Output(layout=wdg.Layout(width="100%"))
    status = wdg.HTML()
    button = wdg.Button(description="Encode", icon="play", button_style="danger", layout=wdg.Layout(width="160px"))

    def refresh(*_):
        t0 = time.perf_counter(); status.value = "<i>working…</i>"; button.disabled = True
        with out:
            out.clear_output(wait=True)
            try:
                render(**{k: w.value for k, w in ws.items()})
                status.value = f'<span style="color:#8a8a8a">updated in {time.perf_counter() - t0:.1f} s</span>'
            except Exception as exc:   # show the problem in the panel instead of killing the widget
                print(f"This setting failed: {exc}"); status.value = '<span style="color:#c62828">failed</span>'
        button.disabled = False

    toggles = [w for w in ws.values() if isinstance(w, wdg.ToggleButtons)]
    others = [w for w in ws.values() if not isinstance(w, wdg.ToggleButtons)]
    grid = wdg.GridBox(others, layout=wdg.Layout(grid_template_columns="repeat(3, 320px)", justify_content="center", grid_gap="4px 10px"))
    rows = [wdg.HTML(header), *[wdg.HBox([t], layout=wdg.Layout(justify_content="center")) for t in toggles], grid]
    if live:
        for w in ws.values():
            w.observe(refresh, names="value")
        rows.append(wdg.HBox([status], layout=wdg.Layout(justify_content="center")))
    else:
        button.on_click(refresh)
        rows.append(wdg.HBox([button, status], layout=wdg.Layout(justify_content="center", align_items="center", grid_gap="12px")))
    rows.append(out)
    box = wdg.VBox(rows, layout=wdg.Layout(border="1px solid #eeeeee", padding="0 8px 10px", width="100%"))
    PANELS[name] = {"widgets": ws, "button": button, "refresh": refresh, "out": out}
    display(box)
    if BATCH:   # unattended run (e.g. nbclient): draw the default result straight into the cell
        status.value = '<span style="color:#8a8a8a">showing the default setting: run this cell to use the controls</span>'
        render(**defaults)
    else:
        refresh()
print("Tuning panels ready" + ("" if HAS_WIDGETS else " (static mode: pip install ipywidgets for the controls)"))
'''

E3 = r'''
def tune_rate(mode, crf, target, buffer_s):
    if mode == "CRF (quality)":
        args = ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf)]; label = f"CRF {crf}"
    else:
        kb = int(target * 1000)
        args = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{kb}k", "-maxrate", f"{kb}k", "-bufsize", f"{int(kb * buffer_s)}k"]
        label = f"cap {target:g} Mb/s, buffer {buffer_s:g} s"
    res = encode_cached(args, "e3")
    t, mb, _ = windowed_mbps(res["file"]); t0, mb0, _ = windowed_mbps(crf23["file"])
    cards([("bitrate", f"{res['bitrate']:.2f} Mb/s", *delta(res["bitrate"], crf23["bitrate_Mb/s"], lambda d: f"{d:+.2f}", False)),
           ("peak (200 ms)", f"{mb.max():.2f} Mb/s", *delta(mb.max(), mb0.max(), lambda d: f"{d:+.2f}", False)),
           ("compression", f"{raw_bits / (res['size'] * 8):,.0f} : 1", "vs raw 4:2:0"),
           ("PSNR", f"{res['psnr']:.1f} dB", *delta(res["psnr"], crf23["PSNR_dB"], lambda d: f"{d:+.1f} dB", True)),
           ("SSIM", f"{res['ssim']:.4f}", *delta(res["ssim"], crf23["SSIM"], lambda d: f"{d:+.4f}", True))])
    fig = plt.figure(figsize=(13, 3.6)); gs = fig.add_gridspec(1, 3, width_ratios=[1.6, 1, 1])
    ax = fig.add_subplot(gs[0])
    ax.step(t0, mb0, where="post", color="#b5b5b5", label="baseline: CRF 23")
    ax.step(t, mb, where="post", color=PALETTE[0], label=label)
    ax.axvline(4.0, color="#52514e", ls=":", lw=1); ax.set_xlabel("time (s)"); ax.set_ylabel("Mb/s (200 ms windows)")
    ax.set_title("Bitrate over time"); ax.legend(fontsize=8)
    y0, x0 = int(0.48 * H), int(0.40 * W)   # zoom on the pipeline at t = 2 s, where detail is hardest to keep
    for k, (img, cap) in enumerate(((frame_png(SRC, 2.0, "e3_ref"), "original"), (frame_png(res["file"], 2.0, "e3_enc"), label))):
        a = fig.add_subplot(gs[k + 1]); a.imshow(img[y0:y0 + H // 4, x0:x0 + W // 4]); a.set_title(f"zoom · {cap}", fontsize=9); a.axis("off")
    plt.tight_layout(); plt.show()

tuning_panel("e3", "Rate control", "Quality target or bitrate cap: watch the peaks and the detail",
             {"mode": ("toggle", ["CRF (quality)", "Target bitrate (VBV)"], "CRF (quality)", ""),
              "crf": ("int", (12, 45, 1), 23, "CRF"),
              "target": ("options", [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0], 1.0, "bitrate cap (Mb/s)"),
              "buffer_s": ("options", [0.1, 0.25, 0.5, 1.0, 2.0], 0.5, "VBV buffer (s)")}, tune_rate)
'''

E4 = r'''
def tune_preset(preset, zerolatency):
    args = ["-c:v", "libx264", "-preset", preset, "-crf", "23", *(["-tune", "zerolatency"] if zerolatency else [])]
    res = encode_cached(args, "e4")
    base = e4[e4["preset"] == "medium"].iloc[0]
    fps_ = N_FRAMES / res["wall"]; cores = res["cpu"] / res["wall"]; ms = 1000 * res["cpu"] / N_FRAMES
    cards([("encode speed", f"{fps_:.0f} fps", f"{fps_ / FPS:.1f}× real time", fps_ >= FPS),
           ("CPU per frame", f"{ms:.1f} ms", *delta(ms, base["cpu_ms_per_frame"], lambda d: f"{d:+.1f} ms", False)),
           ("cores used", f"{cores:.1f}", f"of {CPU_CORES} on this machine"),
           ("bitrate", f"{res['bitrate']:.2f} Mb/s", *delta(res["bitrate"], base["bitrate_Mb/s"], lambda d: f"{d:+.2f}", False)),
           ("PSNR", f"{res['psnr']:.2f} dB", *delta(res["psnr"], base["PSNR_dB"], lambda d: f"{d:+.2f} dB", True))])
    need = ms * FPS * 8 / 1000
    display(HTML(f'<p style="text-align:center">Eight 720p30 cameras with these settings would need <b>{need:.1f} cores</b> '
                 f'of <i>this</i> computer. Repeat on the SBC before you believe it.</p>'))
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(e4["cpu_ms_per_frame"], e4["bitrate_Mb/s"], "o-", color="#b5b5b5", label="all presets (Experiment 4)")
    ax.plot([ms], [res["bitrate"]], "o", ms=13, color=PALETTE[1], label=f"your setting: {preset}{' + zerolatency' if zerolatency else ''}")
    ax.set_xscale("log"); ax.set_xlabel("CPU time per frame (ms, log)"); ax.set_ylabel("bitrate at CRF 23 (Mb/s)")
    ax.set_title("Where your setting sits on the speed–efficiency curve"); ax.legend(fontsize=8); plt.tight_layout(); plt.show()

tuning_panel("e4", "Encoder speed", "Same CRF, different preset: CPU cost versus bits",
             {"preset": ("options", PRESETS, "veryfast", "preset"),
              "zerolatency": ("check", None, False, "-tune zerolatency (no B-frames, no lookahead)")}, tune_preset)
'''

E5 = r'''
def tune_gop(gop_s, intra_refresh, loss_kb, loss_at):
    g = max(1, int(round(gop_s * FPS)))
    extra = (["-g", str(g), "-sc_threshold", "0", "-x264-params", "intra-refresh=1"] if intra_refresh
             else ["-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0"])
    args = ["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-threads", "1",
            "-b:v", "2000k", "-maxrate", "2000k", "-bufsize", "700k", *extra]
    key = hashlib.sha1(json.dumps(args).encode()).hexdigest()[:12]
    ts = WORK / f"tune_e5_{key}.ts"
    if not ts.exists():
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, *args, "-pix_fmt", "yuv420p", "-an", "-f", "mpegts", str(ts)])
    pk = packets(ts); data = ts.read_bytes()
    _, _, clean = quality(ts, SRC, per_frame=True)
    pos = int(pk.loc[(pk["pts"] - pk["pts"].min() - loss_at).abs().idxmin(), "pos"]); pos -= pos % 188
    n_drop = max(1, int(loss_kb * 1000 / 188))
    dam = WORK / "tune_e5_damaged.ts"; dam.write_bytes(data[:pos] + data[pos + 188 * n_drop:])
    dec = WORK / "tune_e5_decoded.mkv"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(dam), "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(dec)])
    _, _, broken = quality(dec, SRC, per_frame=True)
    mbps = len(data) * 8 / (N_FRAMES / FPS) / 1e6
    cards([("I-frames", f"{int(pk['key'].sum())}", "intra refresh: only the first" if intra_refresh else f"one every {g / FPS:.2f} s"),
           ("stream bitrate", f"{mbps:.2f} Mb/s", "incl. MPEG-TS overhead"),
           ("biggest frame", f"{pk['size'].max() / 1e3:.0f} kB", f"average {pk['size'].mean() / 1e3:.1f} kB"),
           ("broken picture", f"{damage_seconds(clean, broken):.2f} s", f"after losing {n_drop * 188 / 1000:.0f} kB",
            damage_seconds(clean, broken) <= 1.0),
           ("worst join wait", f"{g / FPS:.2f} s", "camera switch / new viewer")])
    fig, axs = plt.subplots(1, 2, figsize=(13, 3.6), gridspec_kw={"width_ratios": [1, 1.3]})
    axs[0].bar(np.arange(len(pk)), pk["size"] / 1e3, width=0.9, color=[PALETTE[1] if k else PALETTE[0] for k in pk["key"]])
    axs[0].set_xlabel("frame"); axs[0].set_ylabel("kB"); axs[0].set_title("Frame sizes (orange = I-frame)")
    tt = np.arange(len(broken)) / FPS
    axs[1].plot(np.arange(len(clean)) / FPS, clean, color="#b5b5b5", label="no loss")
    axs[1].plot(tt, broken, color=PALETTE[1], label="after the loss")
    axs[1].axvline(loss_at, color="#52514e", ls=":", lw=1); axs[1].set_ylim(10, None)
    axs[1].set_xlabel("time (s)"); axs[1].set_ylabel("PSNR vs original (dB)"); axs[1].set_title("Damage and recovery"); axs[1].legend(fontsize=8)
    plt.tight_layout(); plt.show()

tuning_panel("e5", "Keyframes and packet loss", "Shorter GOP or intra refresh: how fast does the picture heal?",
             {"gop_s": ("options", [0.25, 0.5, 1.0, 2.0, 3.0, 5.0], 1.0, "keyframe every (s)"),
              "loss_kb": ("int", (1, 40, 1), 8, "data lost (kB)"),
              "loss_at": ("float", (0.5, 4.5, 0.1), 1.4, "loss at (s)"),
              "intra_refresh": ("check", None, False, "intra refresh instead of I-frames")}, tune_gop)
'''

E7 = r'''
def explore(n_main=1, main_res="1920×1080", main_fps=30, n_sub=7, sub_res="640×360", sub_fps=15,
            codec="H.264", link_mbps=100, transport="RTP/UDP"):
    s = simulate("custom", [(n_main, codec, main_res, main_fps), (n_sub, codec, sub_res, sub_fps)], transport)
    u = s["wire_Mb/s"] / link_mbps; v = verdict(s["wire_Mb/s"], link_mbps)
    cards([("on the wire", f"{s['wire_Mb/s']:.1f} Mb/s", f"{transport}"), ("link use", f"{u:.0%}", v, v == "OK"),
           ("cameras", f"{n_main + n_sub}", f"{n_main} main + {n_sub} sub")])
    fig, ax = plt.subplots(figsize=(9, 1.6))
    ax.barh([0], [s["wire_Mb/s"]], color=STATUS[v], height=0.5)
    ax.axvline(link_mbps * HEADROOM, ls="--", color="#52514e", lw=1); ax.axvline(link_mbps, color="#52514e", lw=1.5)
    ax.set_xlim(0, max(link_mbps, s["wire_Mb/s"]) * 1.15); ax.set_yticks([]); ax.set_xlabel("Mb/s (dashed = 70 % headroom, solid = link)")
    plt.tight_layout(); plt.show()

tuning_panel("e7", "Eight-camera budget", "Instant calculation: change anything and the verdict updates",
             {"n_main": ("int", (0, 8, 1), 1, "main streams"), "main_res": ("options", list(RES), "1920×1080", "main resolution"),
              "main_fps": ("int", (5, 60, 5), 30, "main fps"), "n_sub": ("int", (0, 8, 1), 7, "substreams"),
              "sub_res": ("options", list(RES), "640×360", "sub resolution"), "sub_fps": ("int", (1, 30, 1), 15, "sub fps"),
              "codec": ("options", list(CODEC_BPP), "H.264", "codec"), "link_mbps": ("options", [100, 1000], 100, "link (Mb/s)"),
              "transport": ("options", list(OVERHEAD), "RTP/UDP", "transport")}, explore, live=True)
'''

E8 = r'''
def tune_substream(width, fps, kbps):
    w = int(width); h = int(round(w * 9 / 16 / 2) * 2)
    args = ["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k",
            "-bufsize", f"{kbps // 2}k", "-g", str(fps)]
    res = encode_cached(args, "e8", vf=f"scale={w}:{h}:flags=area,fps={fps}")
    main = float(e8.iloc[0]["bitrate_Mb/s"]); total = main + 7 * res["bitrate"]
    cards([("substream", f"{res['bitrate']:.2f} Mb/s", f"{w}×{h} @ {fps} fps"),
           ("SSIM (upscaled)", f"{res['ssim']:.3f}", "0.95+ is fine for a thumbnail", res["ssim"] >= 0.95),
           ("1 main + 7 of these", f"{total:.1f} Mb/s", f"{total / (8 * main):.0%} of eight main streams", True),
           ("saving", f"{8 * main - total:.1f} Mb/s", "free for the pilot view or headroom")])
    fig, axs = plt.subplots(1, 2, figsize=(10, 2.9))
    for ax, (path, cap) in zip(axs, ((e8.iloc[0]["file"], "main 1280×720 @ 2.5 Mb/s"), (res["file"], f"your substream {w}×{h}@{fps}"))):
        ax.imshow(frame_png(path, 2.0, "e8_" + str(abs(hash(cap)))), extent=(0, 16, 0, 9)); ax.set_title(cap, fontsize=9); ax.axis("off")
    plt.suptitle("Shown at the same tile size, as on the pilot screen", fontweight="bold"); plt.tight_layout(); plt.show()

tuning_panel("e8", "Design a substream", "How small can a thumbnail stream be before it stops being useful?",
             {"width": ("options", [256, 320, 426, 512, 640, 854, 960], 640, "width (16:9)"),
              "fps": ("int", (2, 30, 1), 15, "fps"),
              "kbps": ("options", [60, 100, 150, 250, 400, 600, 1000], 400, "bitrate (kb/s)")}, tune_substream)
'''

INSERTS = [
    # (unique text in the cell to insert AFTER, cells)
    ('plt.suptitle("Reference clip (lossless)"', [("markdown", HELPER_MD), ("code", HELPER_CODE)]),
    ('ax.set_title("Same average bitrate, very different peaks")', [("code", E3)]),
    ('ax.set_title("x264 presets: CPU cost vs bits")', [("code", E4)]),
    ('ax.set_title("Intra refresh spreads the I-frame cost over many frames")', [("code", E5)]),
    ('ax.set_xlim(right=max(strategies.values()) * 1.35)', [("code", E8)]),
]
REPLACE = {  # old Experiment 7 interact cell -> panel
    "def explore(n_main=1": E7,
}
