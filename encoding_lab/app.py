"""ROV Encoding Lab — tune every encoder setting on real video, and benchmark the computer that will run it.

Run:  streamlit run app.py
"""
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lab import bench as B
from lab import engine as E

APP_DIR = Path(__file__).parent
WORK = Path(os.environ.get("LAB_WORKDIR", APP_DIR / ".lab_work"))
RED, DRED, CHAR, GRAY, GREEN, AMBER, BLUE = "#E5383B", "#7A0000", "#D0D4DA", "#8B93A1", "#3DBE8B", "#F2A93B", "#5B9BD5"
BG, PANEL, CARD, LINE, TEXT, MUTED = "#0F1115", "#171A21", "#1A1E26", "#2A2F3A", "#F1F3F5", "#9AA3AF"   # dark theme
TYPE_COL = {"I": RED, "P": "#8FB8E8", "B": "#5C6370"}
CODEC_COL = {"H.264": RED, "H.265": "#8FB8E8", "AV1": "#E07A5F", "MJPEG": AMBER}
STATUS = {"good": GREEN, "warn": AMBER, "bad": RED, "info": GRAY}
STAGE_COL = ["#B23A48", RED, "#E07A5F", AMBER, "#8B93A1", BLUE, "#C9A0DC", GREEN]

st.set_page_config(page_title="ROV Encoding Lab", page_icon=":material/videocam:", layout="wide")

# ============================================================================= style
st.markdown(f"""
<style>
.block-container {{ padding-top: 3.4rem; max-width: 1440px; }}
.hero {{ text-align:center; padding: 1.3rem 1rem 1rem; border-radius: 18px; color: white; margin-bottom: .8rem;
        background: linear-gradient(120deg, {DRED} 0%, {RED} 55%, #E2403B 100%); box-shadow: 0 8px 24px rgba(192,0,0,.18); }}
.hero h1 {{ color: white; font-size: 2.1rem; margin: 0; letter-spacing: -.5px; padding: 0; }}
.hero p {{ color: #FFE3E3; margin: .3rem 0 .7rem; font-size: 1.02rem; }}
.kicker {{ font-size: .74rem; letter-spacing: .22em; font-weight: 700; color: #FFC2C2; }}
.steps {{ display:flex; justify-content:center; gap:.6rem; flex-wrap:wrap; }}
.step {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28); border-radius: 999px; padding: .28rem .85rem; font-size: .88rem; }}
.step b {{ color: #FFD6D6; margin-right: .3rem; }}
.cards {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:.7rem; margin:.4rem 0 .6rem; }}
.cards.c2 {{ grid-template-columns: repeat(2, minmax(0,1fr)); }}
.cards.c3 {{ grid-template-columns: repeat(3, minmax(0,1fr)); }}
.cards.c5 {{ grid-template-columns: repeat(5, minmax(0,1fr)); }}
.card {{ background:{CARD}; border:1px solid {LINE}; border-left:5px solid {GRAY}; border-radius:12px; padding:.62rem .8rem .55rem;
        box-shadow:0 4px 14px rgba(0,0,0,.35); text-align:center; }}
.card .l {{ font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; font-weight:600; }}
.card .v {{ font-size:1.55rem; font-weight:750; color:{TEXT}; line-height:1.25; margin-top:.1rem; }}
.card .n {{ font-size:.78rem; color:{MUTED}; margin-top:.1rem; }}
.card .d {{ font-size:.78rem; font-weight:600; }}
.chips {{ display:flex; gap:.45rem; flex-wrap:wrap; justify-content:center; margin:.3rem 0 .5rem; }}
.chip {{ border-radius:999px; padding:.26rem .8rem; font-size:.86rem; font-weight:600; border:1px solid; }}
.tip {{ border-left: 4px solid {RED}; background: #2A1517; color: #F3D9DA; border-radius: 8px; padding: .55rem .9rem; margin: .4rem 0 .8rem; font-size: .93rem; }}
.verdict {{ text-align:center; border-radius: 14px; padding: .75rem; color: white; font-weight: 700; font-size: 1.12rem; margin:.3rem 0 .6rem; }}
.side {{ background:{PANEL}; border:1px solid {LINE}; border-radius:12px; padding:.75rem .9rem; margin:.3rem 0 .6rem; font-size:.92rem; }}
.mathrow td {{ padding:.2rem .5rem; }}
h3 {{ text-align: center; }}
div[role="tablist"] {{ justify-content: center; gap: .75rem; flex-wrap: wrap; padding: 1.1rem 0 1rem;
        border-bottom: 1px solid {LINE}; margin-bottom: 1.1rem; }}
div[role="tablist"]::after, div[role="tablist"]::before {{ display: none !important; }}
.react-aria-SelectionIndicator, div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {{ display: none !important; }}
[data-testid="stTab"] {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 999px;
        padding: .6rem 1.2rem !important; height: auto !important; min-height: 0; transition: background .15s ease, border-color .15s ease; }}
[data-testid="stTab"] p {{ font-size: 1.02rem !important; font-weight: 650; color: #C9CED6 !important; margin: 0; }}
[data-testid="stTab"]:hover {{ border-color: {RED}; background: #24171B; }}
[data-testid="stTab"]:hover p {{ color: #FFFFFF !important; }}
[data-testid="stTab"][aria-selected="true"] {{ background: linear-gradient(120deg, #B3121A, {RED}); border-color: {RED};
        box-shadow: 0 4px 14px rgba(229,56,59,.35); }}
[data-testid="stTab"][aria-selected="true"] p {{ color: #FFFFFF !important; }}
[data-testid="stTab"]:focus-visible {{ outline: 2px solid #F1F3F5; outline-offset: 2px; }}
/* nested (sub) tabs: smaller, quieter pills so the hierarchy reads clearly */
.stTabs .stTabs div[role="tablist"] {{ gap: .5rem; padding: .2rem 0 .7rem; margin-bottom: .8rem; border-bottom: none; }}
.stTabs .stTabs [data-testid="stTab"] {{ padding: .38rem .9rem !important; background: {CARD}; }}
.stTabs .stTabs [data-testid="stTab"] p {{ font-size: .9rem !important; }}
.stTabs .stTabs [data-testid="stTab"][aria-selected="true"] {{ background: linear-gradient(120deg, #B3121A, {RED}); border-color: {RED}; }}
div[data-testid="stSegmentedControl"] button {{ white-space: nowrap; }}
</style>
<div class="hero"><div class="kicker">M.I.A ROBOTICS · ENGINEERING BETTER ROV SYSTEMS</div>
<h1>ROV Encoding Lab</h1>
<p>Turn one knob, see what it does to size, quality, speed and latency — then benchmark the computer that has to do it.</p>
<div class="steps"><span class="step"><b>1</b>Pick a video (sidebar)</span><span class="step"><b>2</b>Turn one knob (Encode)</span>
<span class="step"><b>3</b>Read the verdicts and the math</span><span class="step"><b>4</b>Benchmark this computer</span></div></div>
""", unsafe_allow_html=True)


# ============================================================================= helpers
def cards(items: list[tuple], cols: int = 4) -> None:
    """items: (label, value, note, status, delta_text) — status ∈ good / warn / bad / info."""
    html = []
    for it in items:
        label, value, note = it[0], it[1], it[2] if len(it) > 2 else ""
        status = it[3] if len(it) > 3 and it[3] else "info"
        delta = it[4] if len(it) > 4 and it[4] else ""
        dcol = GREEN if delta.startswith("▲ better") or delta.startswith("▼ better") else (RED if "worse" in delta else GRAY)
        html.append(f'<div class="card" style="border-left-color:{STATUS[status]}"><div class="l">{label}</div><div class="v">{value}</div>'
                    f'<div class="n">{note or "&nbsp;"}</div>' + (f'<div class="d" style="color:{dcol}">{delta}</div>' if delta else "") + "</div>")
    st.markdown(f'<div class="cards {"c%d" % cols if cols != 4 else ""}">{"".join(html)}</div>', unsafe_allow_html=True)


def chips(items: list[tuple[str, str]]) -> None:
    html = "".join(f'<span class="chip" style="color:{STATUS[s]};border-color:{STATUS[s]};background:{STATUS[s]}22">{t}</span>' for t, s in items)
    st.markdown(f'<div class="chips">{html}</div>', unsafe_allow_html=True)


def tip(text: str) -> None:
    st.markdown(f'<div class="tip">{text}</div>', unsafe_allow_html=True)


def verdict(text: str, status: str) -> None:
    st.markdown(f'<div class="verdict" style="background:{STATUS[status]}">{text}</div>', unsafe_allow_html=True)


def fig_layout(fig: go.Figure, title: str, height: int = 330, **kw) -> go.Figure:
    layout = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=height, title=dict(text=title, x=0.5, xanchor="center", font=dict(size=15)),
                  margin=dict(l=50, r=20, t=55, b=45), legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center"),
                  font=dict(family="Inter, Roboto, Arial", size=12, color="#D5D9E0"))
    fig.update_layout(**{**layout, **kw})   # caller options win over the defaults
    return fig


def fmt_bytes(n: float) -> str:
    return f"{n / 1e9:.2f} GB" if n >= 1e9 else (f"{n / 1e6:.2f} MB" if n >= 1e6 else f"{n / 1e3:.0f} kB")


def change(cur, prev, higher_is_better: bool, fmt) -> str:
    if prev is None or cur is None or abs(cur - prev) < 1e-9:
        return ""
    better = (cur > prev) == higher_is_better
    return f"{'▲' if cur > prev else '▼'} {'better' if better else 'worse'} {fmt(cur - prev)}"


def ssim_grade(ssim: float, floor: float) -> tuple[str, str]:
    if ssim >= max(floor, 0.97):
        return "excellent", "good"
    if ssim >= floor:
        return "good enough", "good"
    if ssim >= floor - 0.03:
        return "visible loss", "warn"
    return "poor", "bad"


# ============================================================================= sidebar
with st.sidebar:
    st.markdown("### :material/movie: Video source")
    kind = st.radio("Source", ["Synthetic underwater clip", "Upload your own video"], label_visibility="collapsed")
    upload_path, start_s = None, 0.0
    if kind == "Upload your own video":
        up = st.file_uploader("ROV footage (mp4, mkv, mov, avi)", type=["mp4", "mkv", "mov", "avi", "ts", "webm"])
        if up is not None:
            (WORK / "uploads").mkdir(parents=True, exist_ok=True)
            upload_path = WORK / "uploads" / up.name
            if not upload_path.exists() or upload_path.stat().st_size != up.size:
                upload_path.write_bytes(up.getbuffer())
            start_s = st.number_input("Start at (s)", 0.0, 3600.0, 0.0, 1.0)
        else:
            st.info("No file yet — using the synthetic clip.")
    seconds = st.slider("Clip length (s)", 2, 10, 4, help="Longer clips give steadier numbers but encode slower.")
    height = st.select_slider("Working resolution", [360, 540, 720, 1080], 540, format_func=lambda h: f"{int(h * 16 / 9)}×{h}",
                              help="540p keeps every encode to a few seconds.")
    with st.spinner("Preparing a lossless reference clip…"):
        SRC = E.prepare_source(WORK, upload_path, seconds, height, 30, start_s)
    st.markdown(f"""<div class="side"><b>{SRC.name}</b><br>{SRC.width}×{SRC.height} · {SRC.fps} fps · {SRC.seconds:.1f} s<br>
    Raw 4:2:0 = <b>{SRC.raw_mbps:,.0f} Mb/s</b></div>""", unsafe_allow_html=True)
    st.video(str(E.browser_preview(SRC.mkv, SRC)))

    st.markdown("### :material/flag: Our targets")
    st.caption("Every verdict in the app is judged against these.")
    BUDGET = st.number_input("Bitrate budget per camera (Mb/s)", 0.1, 50.0, 2.0, 0.1)
    LAT_TARGET = st.number_input("Glass-to-glass latency target (ms)", 30, 1000, 150, 10)
    LINK = st.number_input("Measured tether throughput (Mb/s)", 1.0, 1000.0, 94.0, 1.0, help="iperf3 result, not the label on the switch")
    SSIM_FLOOR = st.slider("Quality floor (SSIM)", 0.85, 0.99, 0.95, 0.01)
    caps = E.capabilities()
    st.caption(" ".join(E.ffmpeg_version().split()[:3]) + " · " + " · ".join(f"{'✅' if caps.get(e) else '❌'} {e}" for e in ("libx264", "libx265", "libsvtav1", "mjpeg"))
               + f" · VMAF {'✅' if caps.get('libvmaf') else '❌'}")

ss = st.session_state
ss.setdefault("history", {}); ss.setdefault("hold", {}); ss.setdefault("decode", {}); ss.setdefault("capacity", [])


def remember(res: E.EncodeResult) -> None:
    d = asdict(res); d["source"] = SRC.sid
    ss.history[Path(res.path).stem + SRC.sid] = d


def hold_for(s: E.EncodeSettings) -> dict:
    key = f"{SRC.sid}_{s.key()}"
    if key not in ss.hold:
        try:
            ss.hold[key] = B.encoder_hold(SRC, s)
        except Exception as exc:   # PyAV build without this encoder → fall back to the estimate
            est = B.X264_LOOKAHEAD.get(s.preset, 40) + (0 if s.zerolatency else s.bframes)
            ss.hold[key] = {"frames": 0 if s.zerolatency else est, "ms": (0 if s.zerolatency else est) * 1000 / (s.fps or SRC.fps),
                            "method": f"estimated ({type(exc).__name__})", "encode_call_ms": None}
    return ss.hold[key]


def decode_for(path: str) -> dict:
    if path not in ss.decode:
        ss.decode[path] = B.decode_speed(path, threads=1)
    return ss.decode[path]


def settings_panel(prefix: str = "") -> E.EncodeSettings:
    codecs = [c for c in E.CODECS if caps.get(E.CODECS[c].encoder)]
    codec = st.selectbox("Codec", codecs, key=prefix + "codec")
    spec = E.CODECS[codec]
    st.caption(spec.blurb)
    modes = {"crf": f"Quality ({spec.q_name})", "bitrate": "Bitrate cap"}
    mode = "crf" if not spec.has_bitrate else st.segmented_control("Rate control", list(modes), default="crf", format_func=modes.get, key=prefix + "mode") or "crf"
    q, kbps, buf = spec.q_default, 2000, 0.5
    if mode == "crf":
        q = st.slider(f"{spec.q_name}  (lower = better quality, bigger file)", *spec.q_range, spec.q_default, key=prefix + "q" + codec)
    else:
        kbps = st.select_slider("Target bitrate", [100, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000], 2000,
                                format_func=lambda k: f"{k / 1000:g} Mb/s", key=prefix + "kbps")
        buf = st.select_slider("VBV buffer (burst allowance)", [0.1, 0.25, 0.5, 1.0, 2.0], 0.5, format_func=lambda b: f"{b:g} s", key=prefix + "buf",
                               help="Smaller = smoother bitrate and lower latency, but hard scenes lose quality.")
    preset = st.select_slider("Preset (speed ↔ efficiency)", E.PRESETS, "medium", key=prefix + "preset", disabled=not spec.has_preset)
    gop = st.select_slider("Keyframe every", [0.25, 0.5, 1.0, 2.0, 5.0, 10.0], 1.0, format_func=lambda g: f"{g:g} s", key=prefix + "gop", disabled=not spec.has_gop)
    zl = st.toggle("Low latency (-tune zerolatency)", False, key=prefix + "zl", help="-tune zerolatency: no B-frames, no lookahead, slice threads, so frames leave the encoder immediately.",
                   disabled=spec.encoder == "mjpeg")
    bf = st.slider("B-frames", 0, 8, 3, key=prefix + "bf", disabled=zl or spec.encoder not in ("libx264", "libx265"))
    c3, c4 = st.columns(2)
    scale = c3.select_slider("Resolution", [0.25, 0.5, 0.75, 1.0], 1.0, format_func=lambda s: f"{int(s * 100)} %", key=prefix + "scale")
    fps = c4.select_slider("Frame rate", [5, 10, 15, 20, 25, 30], 30, format_func=lambda f: f"{f} fps", key=prefix + "fps")
    return E.EncodeSettings(codec=codec, rate_mode=mode, quality=q, bitrate_kbps=kbps, buffer_s=buf, preset=preset, gop_s=gop, bframes=bf,
                            zerolatency=zl, scale=scale, fps=0 if fps == SRC.fps else fps)


tabs = st.tabs([":material/tune: Encode", ":material/compare: Compare", ":material/stacked_line_chart: Sweep", ":material/speed: Benchmark",
                ":material/timer: Latency budget", ":material/signal_wifi_bad: Packet loss", ":material/lan: Bandwidth",
                ":material/monitor_heart: Live monitor", ":material/description: Report", ":material/school: Learn"])

# ============================================================================= 1 · ENCODE
with tabs[0]:
    left, right = st.columns([1, 2.4], gap="large")
    with left:
        st.markdown("### Settings")
        S = settings_panel()
        want_vmaf = st.checkbox("Also compute VMAF", False, disabled=not caps.get("libvmaf"),
                                help="Needs an FFmpeg built with libvmaf." if not caps.get("libvmaf") else None)
    with right:
        with st.spinner(f"Encoding · {S.short()}"):
            try:
                R, error = E.encode(SRC, S, with_vmaf=want_vmaf), None
            except Exception as exc:  # shown to the user, not swallowed
                R, error = None, str(exc)
        if error:
            st.error(f"This combination failed to encode: {error}")
        else:
            remember(R)
            last = ss.get("last")
            if last and last["path"] != R.path:
                ss.prev = last
            ss.last = asdict(R); ss.last_src = SRC.sid
            prev = ss.get("prev")
            H = hold_for(S)
            ft = E.frame_table(R.path)
            frames = max(1, len(ft))
            cpu_ms = 1000 * R.cpu_s / frames
            cores_per_stream = cpu_ms * R.fps / 1000
            n_cores = os.cpu_count() or 1
            streams_cpu = n_cores * B.HEADROOM / max(cores_per_stream, 1e-6)
            rt = R.encode_fps / R.fps
            win = max(1, R.fps // 5)
            roll = ft.bytes.rolling(win, min_periods=1).sum() * 8 * R.fps / win / 1e6
            grade, gstat = ssim_grade(R.ssim, SSIM_FLOOR)

            st.markdown(f"<p style='text-align:center;margin:0'><b>{R.label}</b> · {R.width}×{R.height} @ {R.fps} fps</p>", unsafe_allow_html=True)
            chips([
                (f"{'✓' if rt >= 1 else '✗'} Real time ×{rt:.1f}", "good" if rt >= 1.5 else ("warn" if rt >= 1 else "bad")),
                (f"Quality: SSIM {R.ssim:.3f} · {grade}", gstat),
                (f"{'✓' if R.bitrate_mbps <= BUDGET else '✗'} {R.bitrate_mbps:.2f} of {BUDGET:g} Mb/s budget", "good" if R.bitrate_mbps <= BUDGET else "bad"),
                (f"Encoder hold {H['frames']} frames = {H['ms']:.0f} ms", "good" if H["ms"] <= 50 else ("warn" if H["ms"] <= 150 else "bad")),
                (f"≈ {streams_cpu:.1f} such streams fit this CPU", "good" if streams_cpu >= 8 else ("warn" if streams_cpu >= 1 else "bad")),
            ])
            p = prev or {}
            cards([
                ("File size", fmt_bytes(R.size_bytes), f"{SRC.seconds:.1f} s clip", "info", change(R.size_bytes, p.get("size_bytes"), False, lambda d: f"{d / 1e3:+.0f} kB")),
                ("Bitrate", f"{R.bitrate_mbps:.2f} Mb/s", f"peak 200 ms: {roll.max():.2f}", "good" if R.bitrate_mbps <= BUDGET else "bad",
                 change(R.bitrate_mbps, p.get("bitrate_mbps"), False, lambda d: f"{d:+.2f}")),
                ("Compression", f"{R.compression_ratio:,.0f} : 1", "vs raw 4:2:0", "info"),
                ("Bits per pixel", f"{R.bpp:.3f}", "use it in the Bandwidth tab", "info"),
                ("PSNR", f"{R.psnr:.1f} dB", "≥ 40 dB looks clean", "good" if R.psnr >= 40 else ("warn" if R.psnr >= 35 else "bad"),
                 change(R.psnr, p.get("psnr"), True, lambda d: f"{d:+.1f} dB")),
                ("SSIM", f"{R.ssim:.4f}", f"floor {SSIM_FLOOR:.2f} · {grade}", gstat, change(R.ssim, p.get("ssim"), True, lambda d: f"{d:+.4f}")),
                ("Encode speed", f"{R.encode_fps:,.0f} fps", f"×{rt:.1f} real time", "good" if rt >= 1.5 else ("warn" if rt >= 1 else "bad")),
                ("CPU per stream", f"{cores_per_stream:.2f} cores", f"{cpu_ms:.1f} CPU ms per frame", "good" if cores_per_stream <= 0.5 else ("warn" if cores_per_stream <= 1 else "bad")),
            ])
            if R.vmaf is not None:
                cards([("VMAF", f"{R.vmaf:.1f}", "≥ 90 is very good", "good" if R.vmaf >= 90 else "warn")], cols=3)

            v1, v2, v3, v4, v5 = st.tabs(["Frame compare", "Bitrate over time", "Quality over time", "Play side by side", "🧮 Show the math"])
            with v1:
                c1, c2, c3 = st.columns([1.6, 1.7, 1.2])
                idx = c1.slider("Frame", 0, SRC.frames - 1, min(SRC.frames // 2, SRC.frames - 1), key="frame_idx")
                view = c2.segmented_control("View", ["Side by side", "Diff ×8", "Zoom 3×"], default="Side by side") or "Side by side"
                fy = c3.slider("Zoom position (vertical %)", 0, 100, 55, disabled=view != "Zoom 3×")
                ref = E.grab_frame(SRC.mkv, idx, SRC); enc = E.grab_frame(R.path, idx, SRC)
                if view == "Diff ×8":
                    diff = np.clip(np.abs(ref.astype(int) - enc.astype(int)).mean(axis=2) * 8, 0, 255).astype(np.uint8)
                    a, b = st.columns(2)
                    a.image(enc, caption="Encoded", width="stretch")
                    b.image(diff, caption="Where the encoder threw information away (brighter = more error)", width="stretch")
                else:
                    if view == "Zoom 3×":
                        h, w = ref.shape[:2]; ch, cw = h // 3, w // 3
                        y0 = int((h - ch) * fy / 100); x0 = (w - cw) // 2
                        ref = ref[y0:y0 + ch, x0:x0 + cw].repeat(3, 0).repeat(3, 1); enc = enc[y0:y0 + ch, x0:x0 + cw].repeat(3, 0).repeat(3, 1)
                    a, b = st.columns(2)
                    a.image(ref, caption="Original (lossless reference)", width="stretch")
                    b.image(enc, caption=f"Encoded · frame PSNR {R.psnr_frames[min(idx, len(R.psnr_frames) - 1)]:.1f} dB", width="stretch")
            with v2:
                fig = go.Figure()
                for t in ("I", "P", "B"):
                    sel = ft[ft.type == t]
                    if len(sel):
                        fig.add_bar(x=sel.frame, y=sel.bytes / 1e3, name=f"{t}-frames", marker_color=TYPE_COL[t], width=0.85)
                fig.add_scatter(x=ft.frame, y=roll, name="Mb/s (200 ms window)", yaxis="y2", line=dict(color=GREEN, width=2))
                fig.add_hline(y=BUDGET, yref="y2", line_dash="dot", line_color=GRAY, annotation_text=f"budget {BUDGET:g} Mb/s", annotation_position="top left")
                fig_layout(fig, "Every frame's size — the spikes are what the tether must absorb", 360, barmode="overlay", xaxis_title="frame",
                           yaxis_title="kB per frame", yaxis2=dict(overlaying="y", side="right", title="Mb/s", showgrid=False, rangemode="tozero"))
                st.plotly_chart(fig, width="stretch")
                c = ft.type.value_counts()
                st.markdown(f"<p style='text-align:center'>I-frames: <b>{c.get('I', 0)}</b> · P: <b>{c.get('P', 0)}</b> · B: <b>{c.get('B', 0)}</b> · "
                            f"largest frame <b>{ft.bytes.max() / 1e3:.0f} kB</b> vs average <b>{ft.bytes.mean() / 1e3:.1f} kB</b></p>", unsafe_allow_html=True)
            with v3:
                fig = go.Figure()
                fig.add_scatter(y=R.psnr_frames, name="PSNR (dB)", line=dict(color=RED))
                fig.add_scatter(y=R.ssim_frames, name="SSIM", yaxis="y2", line=dict(color=CHAR))
                fig_layout(fig, "Quality of every frame", 340, xaxis_title="frame", yaxis_title="PSNR (dB)",
                           yaxis2=dict(overlaying="y", side="right", title="SSIM", showgrid=False))
                st.plotly_chart(fig, width="stretch")
                tip("Dips line up with motion, scene changes or the end of a long GOP. In bitrate-cap mode, quality is what gives way when the scene gets hard.")
            with v4:
                with st.spinner("Building a side-by-side preview…"):
                    st.video(str(E.browser_preview(R.path, SRC, side_by_side=True)))
                st.caption("Left: original · Right: encoded (re-wrapped as near-lossless H.264 so every browser can play it).")
            with v5:
                raw_bits = SRC.width * SRC.height * 12 * SRC.frames
                wire = R.bitrate_mbps * (1 + E.OVERHEAD["RTP/UDP"])
                rows = [
                    ("Raw bitrate", "W × H × 12 bits × fps", f"{SRC.width} × {SRC.height} × 12 × {SRC.fps}", f"{SRC.raw_mbps:,.0f} Mb/s"),
                    ("Encoded bitrate", "file size × 8 ÷ duration", f"{R.size_bytes:,} B × 8 ÷ {SRC.seconds:.1f} s", f"{R.bitrate_mbps:.3f} Mb/s"),
                    ("Compression ratio", "raw size ÷ encoded size", f"{raw_bits / 8 / 1e6:,.1f} MB ÷ {R.size_bytes / 1e6:.3f} MB", f"{R.compression_ratio:,.0f} : 1"),
                    ("Bits per pixel", "bitrate ÷ (W × H × fps)", f"{R.bitrate_mbps * 1e6:,.0f} ÷ ({R.width} × {R.height} × {R.fps})", f"{R.bpp:.4f}"),
                    ("Peak bitrate (200 ms)", "largest 200 ms window", f"{win} frames", f"{roll.max():.2f} Mb/s ({roll.max() / max(R.bitrate_mbps, 1e-9):.1f}× average)"),
                    ("Real-time factor", "encode fps ÷ video fps", f"{R.encode_fps:,.0f} ÷ {R.fps}", f"×{rt:.2f} ({'keeps up' if rt >= 1 else 'falls behind'})"),
                    ("CPU per frame", "CPU time ÷ frames", f"{R.cpu_s:.2f} s ÷ {frames}", f"{cpu_ms:.2f} ms"),
                    ("Cores for one live stream", "CPU ms per frame × fps ÷ 1000", f"{cpu_ms:.2f} × {R.fps} ÷ 1000", f"{cores_per_stream:.3f} cores"),
                    ("Streams this CPU can encode", f"cores × {B.HEADROOM:.0%} ÷ cores per stream", f"{n_cores} × {B.HEADROOM} ÷ {cores_per_stream:.3f}", f"{streams_cpu:.1f} streams"),
                    ("On the wire (RTP/UDP)", "bitrate × (1 + 5.3 % headers)", f"{R.bitrate_mbps:.3f} × 1.053", f"{wire:.3f} Mb/s"),
                    ("Streams the tether carries", f"link × {B.HEADROOM:.0%} ÷ on-the-wire", f"{LINK:g} × {B.HEADROOM} ÷ {wire:.3f}", f"{LINK * B.HEADROOM / max(wire, 1e-9):.0f} streams"),
                    ("Encoder hold latency", "frames held ÷ fps", f"{H['frames']} ÷ {R.fps}", f"{H['ms']:.0f} ms ({H['method']})"),
                    ("Recording size", "bitrate × 3600 ÷ 8", f"{R.bitrate_mbps:.3f} × 3600 ÷ 8", f"{R.bitrate_mbps * 450 / 1000:.2f} GB per hour · a 64 GB card holds {64 / max(R.bitrate_mbps * 0.45, 1e-9):,.0f} h"),
                ]
                st.dataframe(pd.DataFrame(rows, columns=["Quantity", "Formula", "With your numbers", "Result"]), hide_index=True, width="stretch")
                st.caption(f"CPU and speed are measured on this computer ({n_cores} logical cores). Run the lab on the ROV's computer for its real numbers.")

# ============================================================================= 2 · COMPARE
with tabs[1]:
    hist = pd.DataFrame([h for h in ss.history.values() if h["source"] == SRC.sid])
    if hist.empty:
        st.info("Encode something first — every encode is added here automatically.")
    else:
        hist["codec"] = hist.label.str.split(" · ").str[0]
        st.markdown("### Every run on this clip")
        ok = hist[(hist.bitrate_mbps <= BUDGET)]
        if len(ok):
            best = ok.sort_values("ssim", ascending=False).iloc[0]
            tip(f"Best quality within your <b>{BUDGET:g} Mb/s</b> budget: <b>{best.label}</b> → SSIM {best.ssim:.4f}, {best.bitrate_mbps:.2f} Mb/s, encodes at {best.encode_fps:.0f} fps.")
        else:
            tip(f"No run fits your {BUDGET:g} Mb/s budget yet — raise CRF, cap the bitrate or lower the resolution.")
        srt = hist.sort_values("bitrate_mbps")
        front = srt[srt.ssim >= srt.ssim.cummax()]   # Pareto front: no cheaper run has better quality
        fig = go.Figure()
        for codec, g in hist.groupby("codec"):
            fig.add_scatter(x=g.bitrate_mbps, y=g.ssim, mode="markers", name=codec, text=g.label,
                            marker=dict(size=12, color=CODEC_COL.get(codec, GRAY), line=dict(width=1, color=BG)),
                            hovertemplate="%{text}<br>%{x:.2f} Mb/s · SSIM %{y:.4f}<extra></extra>")
        if len(front) > 1:
            fig.add_scatter(x=front.bitrate_mbps, y=front.ssim, mode="lines", name="best trade-offs", line=dict(color=GRAY, dash="dot"))
        fig.add_vline(x=BUDGET, line_dash="dot", line_color=RED, annotation_text="your budget", annotation_position="top")
        fig.add_hline(y=SSIM_FLOOR, line_dash="dot", line_color=GREEN, annotation_text="quality floor", annotation_position="bottom right")
        lo = float(min(hist.ssim.min(), SSIM_FLOOR))
        fig_layout(fig, "Rate–quality: up and to the left is better", 420, xaxis_title="bitrate (Mb/s)", yaxis_title="SSIM",
                   xaxis_range=[0, max(float(hist.bitrate_mbps.max()), BUDGET) * 1.12], yaxis_range=[max(0.0, lo - (1 - lo) * 0.3), 1.0005])
        st.plotly_chart(fig, width="stretch")
        show = hist[["label", "bitrate_mbps", "size_bytes", "psnr", "ssim", "encode_fps", "cores", "compression_ratio"]].sort_values("bitrate_mbps")
        st.dataframe(show, hide_index=True, width="stretch", column_config={
            "label": "Settings", "bitrate_mbps": st.column_config.NumberColumn("Mb/s", format="%.2f"),
            "size_bytes": st.column_config.NumberColumn("Bytes", format="%d"), "psnr": st.column_config.NumberColumn("PSNR", format="%.1f"),
            "ssim": st.column_config.ProgressColumn("SSIM", min_value=0.8, max_value=1.0, format="%.4f"),
            "encode_fps": st.column_config.NumberColumn("Encode fps", format="%.0f"), "cores": st.column_config.NumberColumn("Cores", format="%.1f"),
            "compression_ratio": st.column_config.NumberColumn("Ratio", format="%.0f : 1")})
        c1, c2 = st.columns(2)
        c1.download_button("Download results (CSV)", show.to_csv(index=False), "encoding_lab_results.csv", width="stretch")
        if c2.button("Clear history", width="stretch"):
            ss.history = {}; st.rerun()

# ============================================================================= 3 · SWEEP
SWEEPS = {
    "Quality (CRF / q)": ("quality", None), "Target bitrate": ("bitrate_kbps", [250, 500, 1000, 2000, 4000, 8000]),
    "Preset": ("preset", ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"]),
    "Keyframe interval": ("gop_s", [0.25, 0.5, 1.0, 2.0, 5.0]), "Resolution": ("scale", [0.25, 0.5, 0.75, 1.0]),
    "Frame rate": ("fps", [5, 10, 15, 20, 30]), "Codec": ("codec", None),
}
LOOK_FOR = {
    "Quality (CRF / q)": "Bitrate roughly halves every +6 CRF (x264), while SSIM falls slowly at first and then quickly — find the knee.",
    "Target bitrate": "Diminishing returns: the step from 0.25 → 1 Mb/s buys far more quality than 4 → 8 Mb/s.",
    "Preset": "Slower presets cost much more CPU for a modest bitrate saving. On an SBC without a hardware encoder you live at the fast end.",
    "Keyframe interval": "Short GOPs cost bits but make camera switching and loss recovery fast (see the Packet loss tab).",
    "Resolution": "Fewer pixels = fewer bits, but detail is gone for good. Compare with changing the codec instead.",
    "Frame rate": "Halving fps does not halve the bitrate — consecutive frames get less similar, so each costs more.",
    "Codec": "Compare at the same quality, not the same setting number. Then check speed — and whether your board and browser support it.",
}
with tabs[2]:
    st.markdown("### Sweep one parameter, keep everything else fixed")
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        what = st.selectbox("Parameter to sweep", list(SWEEPS))
        base_s = E.EncodeSettings(**(ss.get("last", {}).get("settings") or asdict(E.EncodeSettings())))
        field, values = SWEEPS[what]
        spec = E.CODECS[base_s.codec]
        if field == "quality":
            lo_, hi_ = spec.q_range
            values = sorted({int(max(lo_, min(hi_, v))) for v in np.linspace(lo_ + (12 if spec.q_name == "CRF" else 0), hi_ - (6 if spec.q_name == "CRF" else 8), 6).round().astype(int)})
        if field == "codec":
            values = [c for c in E.CODECS if caps.get(E.CODECS[c].encoder)]
        chosen = st.multiselect("Values", values, default=values)
        st.caption(f"Base settings (from the Encode tab): {base_s.short()}")
        go_ = st.button("Run sweep", type="primary", width="stretch")
        tip(LOOK_FOR[what])
    with c2:
        if go_ and chosen:
            rows, bar = [], st.progress(0.0, "Encoding…")
            for i, v in enumerate(chosen):
                s = E.EncodeSettings(**{**asdict(base_s), field: v})
                if field == "bitrate_kbps":
                    s.rate_mode = "bitrate"
                if field == "quality":
                    s.rate_mode = "crf"
                if field == "codec":
                    s.quality = E.CODECS[v].q_default; s.rate_mode = "crf" if not E.CODECS[v].has_bitrate else s.rate_mode
                if field == "fps" and v == SRC.fps:
                    s.fps = 0
                r = E.encode(SRC, s); remember(r)
                rows.append({"value": str(v), **asdict(r)})
                bar.progress((i + 1) / len(chosen), f"{i + 1}/{len(chosen)} · {r.label}")
            ss.sweep = (what, pd.DataFrame(rows))
            st.rerun()  # so "Compare" (drawn earlier in this script) picks up the new encodes
        if "sweep" in ss:
            what_done, df = ss.sweep
            fig = go.Figure()
            fig.add_bar(x=df.value, y=df.bitrate_mbps, name="Bitrate (Mb/s)", marker_color=RED, text=df.bitrate_mbps.round(2), textposition="outside")
            fig.add_scatter(x=df.value, y=df.ssim, name="SSIM", yaxis="y2", mode="lines+markers", line=dict(color=CHAR, width=3), marker=dict(size=9))
            fig.add_hline(y=BUDGET, line_dash="dot", line_color=GRAY, annotation_text="budget", annotation_position="top left")
            fig_layout(fig, f"{what_done}: bitrate and quality", 380, xaxis_title=what_done, yaxis_title="Mb/s",
                       yaxis2=dict(overlaying="y", side="right", title="SSIM", showgrid=False))
            st.plotly_chart(fig, width="stretch")
            fig2 = go.Figure()
            fig2.add_bar(x=df.value, y=df.encode_fps, marker_color=GRAY, text=df.encode_fps.round(0), textposition="outside", name="encode fps")
            fig2.add_hline(y=30, line_dash="dot", line_color=RED, annotation_text="real time (30 fps)", annotation_position="top left")
            fig_layout(fig2, "Encoding speed on this computer", 300, xaxis_title=what_done, yaxis_title="frames / s", showlegend=False)
            st.plotly_chart(fig2, width="stretch")
        else:
            st.info("Pick a parameter and press **Run sweep**.")

# ============================================================================= 4 · BENCHMARK
with tabs[3]:
    st.markdown("### How much video can this computer handle?")
    tip("Run this tab <b>on the computer that will do the work</b> — the ROV's Raspberry Pi 5 / Jetson, and the pilot laptop. "
        "A laptop is several times faster than an SBC, so laptop numbers say nothing about the ROV.")
    info = B.system_info()
    cards([("Board", info["Board"][:28], info["Architecture"], "info"), ("CPU", f"{info['Logical cores']} cores", info["CPU"][:34], "info"),
           ("RAM", f"{info['RAM (GB)'] or '?'} GB", info["OS"][:30], "info"), ("FFmpeg", info["FFmpeg"].replace("ffmpeg version ", ""), f"Python {info['Python']}", "info")])

    b1, b2 = st.columns([1, 2.1], gap="large")
    with b1:
        st.markdown("#### Encoder capacity")
        res_opts = {360: "640×360", 540: "960×540", 720: "1280×720", 1080: "1920×1080"}
        res_sel = st.multiselect("Resolutions", list(res_opts), [540, 720, 1080], format_func=res_opts.get)
        pre_sel = st.multiselect("Presets", E.PRESETS[:6], ["ultrafast", "veryfast", "medium"])
        bcodec = st.selectbox("Codec", [c for c in E.CODECS if caps.get(E.CODECS[c].encoder)], key="bench_codec")
        bzl = st.toggle("Low latency (zerolatency)", True, key="bench_zl")
        bsec = st.slider("Test clip (s)", 2, 6, 3, key="bench_sec")
        run_b = st.button("Run capacity benchmark", type="primary", width="stretch")
        st.caption(f"Each setting is encoded twice: on ONE thread (clean cost per core) and on all threads. "
                   f"'Streams on this computer' = streams per core × {info['Logical cores']} cores × {B.HEADROOM:.0%} headroom.")
    with b2:
        if run_b and res_sel and pre_sel:
            rows, bar = [], st.progress(0.0, "Benchmarking…")
            combos = [(h, p) for h in res_sel for p in (pre_sel if E.CODECS[bcodec].has_preset else ["medium"])]
            for i, (h, p) in enumerate(combos):
                src_b = E.prepare_source(WORK, upload_path, bsec, h, 30, start_s)
                s = E.EncodeSettings(codec=bcodec, rate_mode="crf", quality=E.CODECS[bcodec].q_default, preset=p, zerolatency=bzl and bcodec != "MJPEG", bframes=0 if bzl else 3)
                c = asdict(B.encoder_capacity(src_b, s)); c["res"] = res_opts[h]; c["preset"] = p
                rows.append(c)
                bar.progress((i + 1) / len(combos), f"{res_opts[h]} · {p}")
            ss.capacity = rows; bar.empty()
        if ss.capacity:
            cdf = pd.DataFrame(ss.capacity)
            best = cdf.sort_values("streams_machine", ascending=False).iloc[0]
            at720 = cdf[cdf.height == 720]
            if len(at720):
                r = at720.sort_values("streams_machine", ascending=False).iloc[0]
                n = r.streams_machine
                verdict(f"This computer can encode ≈ {n:.1f} × 720p30 streams in real time ({r.preset}) — "
                        f"{'enough' if n >= 8 else 'NOT enough'} for 8 cameras" + ("" if n >= 8 else ", so let cameras encode or use hardware"),
                        "good" if n >= 8 else ("warn" if n >= 3 else "bad"))
            fig = go.Figure()
            for k, p in enumerate(cdf.preset.unique()):
                g = cdf[cdf.preset == p]
                fig.add_bar(x=g.res, y=g.streams_machine, name=p, marker_color=[RED, CHAR, "#E07A5F", AMBER, GRAY, BLUE][k % 6],
                            text=g.streams_machine.round(1), textposition="outside")
            fig.add_hline(y=8, line_dash="dot", line_color=GREEN, annotation_text="8 cameras", annotation_position="top left")
            fig_layout(fig, f"Real-time 30 fps streams this computer can encode ({B.HEADROOM:.0%} CPU)", 380, barmode="group",
                       xaxis_title="resolution", yaxis_title="streams")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(cdf[["res", "preset", "one_core_fps", "ms_per_frame", "streams_per_core", "streams_machine", "realtime_factor", "bitrate_mbps"]],
                         hide_index=True, width="stretch", column_config={
                             "res": "Resolution", "preset": "Preset", "one_core_fps": st.column_config.NumberColumn("fps on 1 core", format="%.0f"),
                             "ms_per_frame": st.column_config.NumberColumn("CPU ms / frame", format="%.1f"),
                             "streams_per_core": st.column_config.NumberColumn("Streams / core", format="%.2f"),
                             "streams_machine": st.column_config.NumberColumn("Streams on this computer", format="%.1f"),
                             "realtime_factor": st.column_config.NumberColumn("Real-time factor (all cores)", format="×%.1f"),
                             "bitrate_mbps": st.column_config.NumberColumn("Mb/s", format="%.2f")})
        else:
            st.info("Choose resolutions and presets, then press **Run capacity benchmark** (≈ 2–4 s per combination).")

    st.divider()
    h1, h2 = st.columns([1, 3], gap="large")
    with h1:
        st.markdown("#### Hardware encoders")
        if st.button("Probe hardware encoders", width="stretch"):
            ss.hw = B.hw_encoders()
        st.caption("Listed ≠ working: every encoder FFmpeg lists gets a real 1-second test encode. "
                   "The Jetson Nano's encoder is used through GStreamer (nvv4l2h264enc), not FFmpeg, so test it with hw_vs_sw.md.")
    with h2:
        if "hw" in ss:
            st.dataframe(pd.DataFrame(ss.hw), hide_index=True, width="stretch", column_config={
                "encoder": "Encoder", "hardware": "Hardware", "listed by FFmpeg": st.column_config.CheckboxColumn("Listed"), "test encode": "Test encode"})
        else:
            st.info("Press **Probe hardware encoders** (≈ 1 s).")
    st.divider()
    d2, d3 = st.columns(2, gap="large")
    with d2:
        st.markdown("#### Decode speed (pilot side)")
        if "last" in ss and ss.get("last_src") == SRC.sid:
            dec = decode_for(ss.last["path"])
            per_core = dec["fps"] / ss.last["fps"]
            cards([("Decode, 1 thread", f"{dec['fps']:,.0f} fps", f"{dec['ms_per_frame']:.1f} CPU ms / frame", "info"),
                   ("Streams per core", f"{per_core:.1f}", f"of {ss.last['width']}×{ss.last['height']}@{ss.last['fps']}", "good" if per_core >= 8 else "warn")], cols=2)
            st.caption("8 cameras = 8 decoders on the pilot laptop (browsers often decode in hardware; this measures software decode).")
        else:
            st.info("Encode something in the Encode tab first.")
    with d3:
        st.markdown("#### Encoder hold (latency by design)")
        if st.button("Compare defaults vs low latency", width="stretch"):
            ss.holdcmp = [(lbl, hold_for(s)) for lbl, s in [
                ("x264 medium (defaults)", E.EncodeSettings(preset="medium", bframes=3)),
                ("x264 medium, no B-frames", E.EncodeSettings(preset="medium", bframes=0)),
                ("x264 veryfast", E.EncodeSettings(preset="veryfast", bframes=3)),
                ("x264 veryfast + zerolatency", E.EncodeSettings(preset="veryfast", zerolatency=True))]]
        if "holdcmp" in ss:
            fig = go.Figure(go.Bar(x=[h["ms"] for _, h in ss.holdcmp], y=[l for l, _ in ss.holdcmp], orientation="h",
                                   marker_color=[RED if h["ms"] > 100 else GREEN for _, h in ss.holdcmp],
                                   text=[f"{h['frames']} fr · {h['ms']:.0f} ms" for _, h in ss.holdcmp], textposition="outside"))
            fig_layout(fig, "Delay the encoder adds before the first frame", 280, xaxis_title="ms", showlegend=False, yaxis=dict(autorange="reversed"),
                       xaxis=dict(range=[0, max(h["ms"] for _, h in ss.holdcmp) * 1.45 + 50]), margin=dict(l=200, r=20, t=55, b=45))
            st.plotly_chart(fig, width="stretch")
            st.caption(ss.holdcmp[0][1]["method"].capitalize() + ". Settings alone can add more than a second.")

# ============================================================================= 5 · LATENCY BUDGET
with tabs[4]:
    st.markdown("### Glass-to-glass latency budget")
    if "last" not in ss or ss.get("last_src") != SRC.sid:
        st.info("Encode something in the Encode tab first — the budget uses that encode's measured numbers.")
    else:
        L = ss.last; Ls = E.EncodeSettings(**L["settings"])
        Hh = hold_for(Ls); dec = decode_for(L["path"]); ftl = E.frame_table(L["path"])
        c1, c2 = st.columns([1, 2.2], gap="large")
        with c1:
            st.markdown(f"<div class='side'>Using your last encode:<br><b>{L['label']}</b><br>{L['width']}×{L['height']} @ {L['fps']} fps</div>", unsafe_allow_html=True)
            cap_fr = st.slider("Capture buffering (frames)", 1, 4, 1, help="Exposure + driver/V4L2 buffers. USB cameras often hold 1–2 frames.")
            net = st.slider("Network: switches + cable (ms)", 0.0, 20.0, 1.0, 0.5)
            jit = st.slider("Receiver jitter buffer (ms)", 0, 1000, 50, 10, help="VLC defaults to 1000 ms network caching; WebRTC adapts, typically tens of ms.")
            hz = st.select_slider("Pilot monitor refresh", [30, 60, 75, 120, 144], 60, format_func=lambda h: f"{h} Hz")
        bud = B.latency_budget(L["fps"], Hh["frames"], 1000 / max(L["encode_fps"], 1e-6), float(ftl.bytes.mean()), float(ftl.bytes.max()),
                               LINK, net, jit, dec["ms_per_frame"], hz, cap_fr)
        tot = sum(b["typical_ms"] for b in bud); worst = sum(b["worst_ms"] for b in bud)
        with c2:
            status = "good" if worst <= LAT_TARGET else ("warn" if tot <= LAT_TARGET else "bad")
            verdict(f"Typical ≈ {tot:.0f} ms · worst ≈ {worst:.0f} ms · target {LAT_TARGET} ms → "
                    + ("meets the target" if status == "good" else ("only the typical case meets it" if status == "warn" else "misses the target")), status)
            fig = go.Figure()
            for k, b in enumerate(bud):
                fig.add_bar(y=["worst", "typical"], x=[b["worst_ms"], b["typical_ms"]], orientation="h", name=b["stage"], marker_color=STAGE_COL[k % len(STAGE_COL)],
                            hovertemplate=f"{b['stage']}: %{{x:.1f}} ms<extra></extra>")
            fig.add_vline(x=LAT_TARGET, line_dash="dot", line_color=RED, annotation_text="target", annotation_position="top")
            fig_layout(fig, "Where the milliseconds go", 300, barmode="stack", xaxis_title="ms", legend=dict(orientation="h", y=-0.35, x=0.5, xanchor="center"))
            st.plotly_chart(fig, width="stretch")
            bdf = pd.DataFrame(bud)
            st.dataframe(bdf, hide_index=True, width="stretch", column_config={
                "stage": "Stage", "typical_ms": st.column_config.NumberColumn("Typical (ms)", format="%.1f"),
                "worst_ms": st.column_config.NumberColumn("Worst (ms)", format="%.1f"), "source": "Source"})
            big = max(bud, key=lambda b: b["typical_ms"])
            tip(f"The biggest stage is <b>{big['stage']}</b> ({big['typical_ms']:.0f} ms). "
                + ("Turn on <b>Low latency</b> in the Encode tab and watch it disappear." if "hold" in big["stage"].lower() else
                   "Shrink the receiver buffer (ffplay -fflags nobuffer, WebRTC) before buying hardware." if "jitter" in big["stage"].lower() else
                   "Measure it — then decide.")
                + " Confirm the total with a real glass-to-glass photo test (demos/01_why_streaming/clock.html).")

# ============================================================================= 6 · PACKET LOSS
with tabs[5]:
    st.markdown("### What happens when the tether drops packets?")
    c1, c2 = st.columns([1, 2.2], gap="large")
    with c1:
        variants = st.multiselect("Stream structure", ["GOP 0.5 s", "GOP 1 s", "GOP 2 s", "GOP 5 s", "Intra refresh (1 s)"], ["GOP 1 s", "GOP 5 s", "Intra refresh (1 s)"])
        loss_kb = st.slider("Data lost (kB)", 1, 64, 8, help="8 kB ≈ six 1316-byte UDP datagrams of MPEG-TS")
        loss_at = st.slider("Loss happens at (s)", 0.2, float(SRC.seconds) - 0.5, min(1.4, SRC.seconds - 0.6), 0.1)
        kb = st.select_slider("Stream bitrate", [500, 1000, 2000, 4000], 2000, format_func=lambda k: f"{k / 1000:g} Mb/s")
        run_loss = st.button("Simulate loss", type="primary", width="stretch")
        tip("Each stream is H.264, zero-latency, capped bitrate, in MPEG-TS — like a live UDP stream. We delete packets, decode, and score every frame against the original.")
    with c2:
        if run_loss and variants:
            with st.spinner("Encoding, damaging and decoding…"):
                ss.loss = {v: E.packet_loss_experiment(SRC, v, loss_kb, loss_at, kb) for v in variants}
                ss.loss_at = loss_at
        if "loss" in ss:
            Lo = ss.loss
            cards([(v, f"{r['damaged_s']:.2f} s", "with a broken picture", "good" if r["damaged_s"] <= 0.5 else ("warn" if r["damaged_s"] <= 1.5 else "bad"))
                   for v, r in Lo.items()], cols=min(5, max(3, len(Lo))))
            fig = go.Figure()
            palette = [RED, CHAR, "#E07A5F", AMBER, GREEN]
            for k, (v, r) in enumerate(Lo.items()):
                fig.add_scatter(x=np.arange(len(r["damaged"])) / SRC.fps, y=r["damaged"], name=v, line=dict(color=palette[k % 5], width=2))
            fig.add_vline(x=ss.loss_at, line_dash="dot", line_color=GRAY, annotation_text="packets lost")
            fig_layout(fig, "Per-frame quality after the loss (PSNR vs original)", 380, xaxis_title="time (s)", yaxis_title="PSNR (dB)")
            st.plotly_chart(fig, width="stretch")
            show_t = st.slider("Show the picture at (s)", 0.0, float(SRC.seconds) - 0.05, min(ss.loss_at + 0.4, SRC.seconds - 0.1), 0.05)
            cols = st.columns(len(Lo))
            for c, (v, r) in zip(cols, Lo.items()):
                c.image(E.grab_frame(r["decoded"], int(show_t * SRC.fps), SRC), caption=v, width="stretch")
            tip("Long GOPs keep predicting from a broken picture until the next I-frame. Intra refresh heals continuously and has no I-frame spikes. Camera switching obeys the same rule: no picture until an I-frame arrives.")
        else:
            st.info("Choose stream structures and press **Simulate loss**.")

# ============================================================================= 7 · BANDWIDTH
with tabs[6]:
    st.markdown("### Will our eight cameras fit the tether?")
    c1, c2, c3 = st.columns(3)
    headroom = c1.slider("Plan to use at most", 40, 95, 70, 5, format="%d %%")
    control = c2.number_input("Control + telemetry (Mb/s)", 0.0, 50.0, 1.0, 0.5)
    transport = c3.selectbox("Transport", list(E.OVERHEAD))
    st.caption(f"Tether throughput comes from the sidebar target: **{LINK:g} Mb/s** (measure it with iperf3). "
               "Bits per pixel: workshop defaults — calibrate with **your** footage via the button.")
    bc = st.columns(5)
    bpp = {k: bc[i].number_input(f"{k} bpp", 0.001, 2.0, ss.get(f"bpp_{k}", v), 0.005, format="%.3f", key=f"bppin_{k}") for i, (k, v) in enumerate(E.DEFAULT_BPP.items())}
    if bc[4].button("Use my last encode", width="stretch") and ss.get("last"):
        last = ss.last; k = last["label"].split(" · ")[0]
        ss[f"bpp_{k}"] = round(last["bitrate_mbps"] * 1e6 / (last["width"] * last["height"] * last["fps"]), 4)
        ss.pop(f"bppin_{k}", None); st.rerun()
    default = pd.DataFrame([
        ["Pilot", "H.264", "1920×1080", 30, True], ["Manipulator", "H.264", "1280×720", 30, True], ["Rear", "H.264", "640×360", 15, True],
        ["Aux 1", "H.264", "640×360", 15, True], ["Aux 2", "H.264", "640×360", 15, True], ["Aux 3", "MJPEG", "640×480", 15, True],
        ["Aux 4", "MJPEG", "640×480", 10, True], ["Aux 5", "MJPEG", "640×480", 10, False]], columns=["Camera", "Codec", "Resolution", "FPS", "Streaming"])
    res_list = ["320×180", "640×360", "640×480", "1280×720", "1920×1080", "3840×2160"]
    cams = st.data_editor(default, hide_index=True, width="stretch", num_rows="dynamic", column_config={
        "Codec": st.column_config.SelectboxColumn(options=list(E.DEFAULT_BPP)), "Resolution": st.column_config.SelectboxColumn(options=res_list),
        "FPS": st.column_config.NumberColumn(min_value=1, max_value=60, step=1), "Streaming": st.column_config.CheckboxColumn()}).dropna()

    def cam_rate(r):
        w, h = map(int, str(r.Resolution).split("×"))
        return E.camera_mbps(bpp[r.Codec], w, h, float(r.FPS)) * (1 + E.OVERHEAD[transport]) if r.Streaming else 0.0
    cams["Mb/s"] = cams.apply(cam_rate, axis=1)
    total = cams["Mb/s"].sum() + control
    plan = LINK * headroom / 100
    col, word = (GREEN, "FITS with headroom") if total <= plan else ((AMBER, "TIGHT — above your headroom") if total <= LINK else (RED, "DOES NOT FIT"))
    st.markdown(f'<div class="verdict" style="background:{col}">{word} · {total:.1f} Mb/s = {total / LINK:.0%} of measured throughput</div>', unsafe_allow_html=True)
    fig = go.Figure()
    pal = [RED, CHAR, "#E07A5F", GRAY, AMBER, GREEN, "#6D4C9F", BLUE, "#999"]
    for i, r in cams.reset_index(drop=True).iterrows():
        if r["Mb/s"] > 0:
            fig.add_bar(y=["tether"], x=[r["Mb/s"]], orientation="h", name=f"{r.Camera} ({r['Mb/s']:.1f})", marker_color=pal[i % len(pal)])
    fig.add_bar(y=["tether"], x=[control], orientation="h", name=f"control ({control:g})", marker_color="#5B9BD5")
    fig.add_vline(x=plan, line_dash="dot", line_color=GRAY, annotation_text=f"{headroom}% plan", annotation_position="top left")
    fig.add_vline(x=LINK, line_color=CHAR, annotation_text="measured", annotation_position="top left")
    fig_layout(fig, "Tether budget", 260, barmode="stack", xaxis_title="Mb/s on the wire", xaxis_range=[0, max(LINK, total) * 1.1])
    st.plotly_chart(fig, width="stretch")
    px_rate = sum(int(str(r.Resolution).split("×")[0]) * int(str(r.Resolution).split("×")[1]) * float(r.FPS) for _, r in cams.iterrows() if r.Streaming and r.Codec != "MJPEG")
    nano = 4 * 1920 * 1080 * 30
    tip(f"If a <b>Jetson Nano</b> encodes all non-MJPEG streams: {px_rate / 1e6:.0f} Mpx/s of its ≈ {nano / 1e6:.0f} Mpx/s hardware budget "
        f"(<b>{px_rate / nano:.0%}</b>). A <b>Raspberry Pi 5</b> has no hardware encoder — use the Benchmark tab on the Pi itself.")

# ============================================================================= 8 · LIVE MONITOR
with tabs[7]:
    st.markdown("### Live system monitor")
    st.caption("CPU per core, temperature, clock speed, Raspberry Pi throttling and network traffic, once per second. "
               "Run the lab on the ROV computer and start a stream to watch it work — this is the soak-test view.")
    on = st.toggle("Start monitoring", False, key="mon_on")

    def live_panel() -> None:
        if "mon" not in ss:
            ss.mon = B.SysMon(); ss.mon_hist = []
        smp = ss.mon.sample()
        ss.mon_hist = (ss.mon_hist + [smp])[-180:]
        tmax = smp["temp_max"]
        thr = smp["throttled"]
        busiest = max(smp["net"].items(), key=lambda kv: max(kv[1]), default=("—", (0.0, 0.0)))
        net_mbps = max(busiest[1])
        cards([("CPU total", f"{smp['cpu_total']:.0f} %", f"hottest core {max(smp['cores'], default=0):.0f} %",
                "good" if smp["cpu_total"] < 70 else ("warn" if smp["cpu_total"] < 90 else "bad")),
               ("Temperature", f"{tmax:.0f} °C" if tmax is not None else "n/a", "Pi throttles at 80 °C" if tmax is not None else "no sensor exposed",
                "info" if tmax is None else ("good" if tmax < 70 else ("warn" if tmax < 80 else "bad"))),
               ("Clock", f"{smp['freq_mhz']:,.0f} MHz" if smp["freq_mhz"] else "n/a", "drops when throttling", "info"),
               ("Throttled (Pi)", thr or "n/a", "0x0 = never" if thr else "vcgencmd not found", "info" if not thr else ("good" if thr == "0x0" else "bad")),
               ("Busiest link", f"{net_mbps:.2f} Mb/s", f"{busiest[0]} · {net_mbps / LINK:.0%} of {LINK:g}", "good" if net_mbps <= LINK * B.HEADROOM else "bad")], cols=5)
        h = pd.DataFrame([{"t": i, "CPU %": s["cpu_total"], "Temp °C": s["temp_max"]} for i, s in enumerate(ss.mon_hist)])
        g1, g2 = st.columns([2, 1])
        fig = go.Figure()
        fig.add_scatter(x=h.t, y=h["CPU %"], name="CPU %", line=dict(color=RED, width=2))
        if h["Temp °C"].notna().any():
            fig.add_scatter(x=h.t, y=h["Temp °C"], name="Temp °C", yaxis="y2", line=dict(color=AMBER, width=2))
        fig_layout(fig, "Last 3 minutes", 280, xaxis_title="sample (1 s)", yaxis=dict(title="CPU %", range=[0, 100]),
                   yaxis2=dict(overlaying="y", side="right", title="°C", showgrid=False))
        g1.plotly_chart(fig, width="stretch")
        fig2 = go.Figure(go.Bar(x=[f"core {i}" for i in range(len(smp["cores"]))], y=smp["cores"],
                                marker_color=[RED if v > 90 else (AMBER if v > 70 else GREEN) for v in smp["cores"]]))
        fig_layout(fig2, "Per core now", 280, yaxis=dict(range=[0, 100], title="%"), showlegend=False)
        g2.plotly_chart(fig2, width="stretch")

    if on:
        st.fragment(run_every=1.0)(live_panel)()
    else:
        st.info("Toggle **Start monitoring** to begin. Tip: start the Benchmark or a stream (demos/02_pipeline/sender.sh) and watch the cores fill up.")
    if ss.get("mon_hist"):
        mh = pd.DataFrame([{"time": s["time"], "cpu_total": round(s["cpu_total"], 1), "temp_max": s["temp_max"], "freq_mhz": s["freq_mhz"],
                            "throttled": s["throttled"], **{f"{k}_rx_mbps": round(v[0], 3) for k, v in s["net"].items()}} for s in ss.mon_hist])
        st.download_button("Download the recorded samples (CSV)", mh.to_csv(index=False), "monitor_log.csv")

# ============================================================================= 9 · REPORT
with tabs[8]:
    st.markdown("### Benchmark report")
    st.caption("Everything measured in this session — this computer, every encode on this clip, the capacity benchmark, encoder hold, decode speed and the latency budget — in one file you can paste into a GitHub issue or the team docs.")
    runs = [h for h in ss.history.values() if h["source"] == SRC.sid]
    bud_r = hold_r = dec_r = None
    if "last" in ss and ss.get("last_src") == SRC.sid:
        Ls = E.EncodeSettings(**ss.last["settings"]); hold_r = hold_for(Ls); dec_r = decode_for(ss.last["path"]); ftr = E.frame_table(ss.last["path"])
        bud_r = B.latency_budget(ss.last["fps"], hold_r["frames"], 1000 / max(ss.last["encode_fps"], 1e-6), float(ftr.bytes.mean()), float(ftr.bytes.max()),
                                 LINK, 1.0, 50, dec_r["ms_per_frame"], 60)
    md = B.report_markdown(B.system_info(), runs, ss.capacity, hold_r, bud_r, dec_r, ss.get("hw"))
    c1, c2 = st.columns(2)
    c1.download_button("Download report (Markdown)", md, "encoding_lab_report.md", type="primary", width="stretch")
    c2.download_button("Download all encodes (CSV)", pd.DataFrame(runs).drop(columns=["psnr_frames", "ssim_frames", "settings"], errors="ignore").to_csv(index=False),
                       "encoding_lab_runs.csv", width="stretch", disabled=not runs)
    with st.container(border=True):
        st.markdown(md.replace("\n## ", "\n#### ").replace("# ROV Encoding Lab: benchmark report", "### ROV Encoding Lab: benchmark report", 1))

# ============================================================================= 10 · LEARN
with tabs[9]:
    st.markdown("### What each knob and number means")
    learn = [
        ("Codec", "How pixels are compressed. H.264 is the universal default; H.265/AV1 save bits at some operating points but cost CPU and need decoder support; MJPEG is simple but large.", "Encode the same clip with each codec, then compare at equal SSIM in <b>Compare</b>."),
        ("CRF / quality", "Constant quality: the encoder spends as many bits as each scene needs. +6 CRF ≈ half the bitrate in x264. Bitrate jumps when the scene gets busy.", "Look at <b>Bitrate over time</b>: where are the peaks?"),
        ("Target bitrate + VBV", "A cap on the bitrate: what a fixed-capacity tether needs. Quality drops on hard scenes instead. A smaller buffer = smoother, lower latency.", "Set 1 Mb/s and watch <b>Quality over time</b> dip."),
        ("Preset", "How hard the encoder searches. Slower = fewer bits for the same quality, much more CPU, sometimes more latency.", "Run the <b>Benchmark</b> with three presets."),
        ("Keyframe interval (GOP)", "How often a full picture is sent. Short = quick joins and recovery, more bits. Long = efficient but fragile.", "Try GOP 0.25 s vs 10 s, then <b>Packet loss</b>."),
        ("B-frames & low latency", "B-frames use future frames, so the encoder must wait. Low-latency mode disables them and the lookahead — essential for piloting.", "Benchmark → <b>Compare defaults vs low latency</b>."),
        ("Real-time factor", "Encode fps ÷ video fps. Below ×1 the encoder falls behind: frames queue up, latency grows, frames drop.", "Read the chip at the top of the Encode tab."),
        ("Cores per stream & headroom", "CPU ms per frame × fps ÷ 1000. We plan to use only 70 % of the CPU (and of the tether) so spikes, heat and other software still fit.", "Open <b>Show the math</b>."),
        ("Encoder hold", "Frames the encoder keeps before releasing the first one. 30 frames at 30 fps = 1 s of delay that no faster network can remove.", "<b>Latency budget</b> tab, first rows."),
        ("Glass-to-glass latency", "From light hitting the lens to light leaving the pilot's screen — the only latency the pilot feels. The budget estimates it; a photo test measures it.", "demos/01_why_streaming/clock.html"),
        ("PSNR · SSIM · VMAF", "Objective quality against the original. Useful to compare settings consistently — but the pilot decides what is good enough.", "Use <b>Diff ×8</b>: where does the encoder throw detail away?"),
        ("Resolution & frame rate", "The bluntest tools: fewer pixels or frames means fewer bits but lost detail or smoothness. Try codec and rate control first.", "Compare 50 % resolution with switching MJPEG → H.264."),
    ]
    for row in range(0, len(learn), 2):
        cols = st.columns(2, gap="large")
        for c, (title, body, try_) in zip(cols, learn[row:row + 2]):
            c.markdown(f"<div class='side'><h4 style='color:{RED};margin:0 0 .3rem'>{title}</h4>{body}<br><br><i>Try it:</i> {try_}</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:{MUTED}'>Measure first. Compress smart. Stream only what the pilot needs.</p>", unsafe_allow_html=True)
