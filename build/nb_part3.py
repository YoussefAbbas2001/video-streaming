# Notebook builder — part 3: Experiments 9–11 and wrap-up.
from nb_part1 import md, code

md(r"""
---
## Experiment 9 — Latency: where does the time go?

**Question.** Why does the pilot see the gripper close *after* they pressed the button?

### Four words that are often confused

| Term | Meaning | Unit | Analogy (a conveyor belt of boxes) |
|---|---|---|---|
| **Frame rate (FPS)** | how many frames arrive per second | frames/s | how many boxes reach you per second |
| **Throughput / bitrate** | how many bits per second are delivered | Mb/s | total weight of boxes per second |
| **Bandwidth / capacity** | how many bits per second the link *could* carry | Mb/s | how wide the belt is |
| **Latency** | how long one frame takes from the scene to the screen | ms | how long one box spends on the belt |

A system can deliver a perfect 30 FPS **and** be two seconds late — the belt is just long. For piloting, **latency is usually more important than FPS**: humans can steer at 15 FPS with 100 ms of latency, but struggle at 60 FPS with 800 ms.

### The latency chain

$$
L_{\text{glass-to-glass}} = L_{\text{capture}} + L_{\text{encode}} + L_{\text{packetize}} + L_{\text{network}} + L_{\text{jitter buffer}} + L_{\text{decode}} + L_{\text{render}} + L_{\text{display}}
$$

Typical contributors (to be **measured**, not assumed):

* **Capture:** exposure + sensor readout + USB/driver buffering. Often ~1 frame (33 ms at 30 FPS) or more; V4L2 drivers may queue several buffers.
* **Encode:** for x264 this is dominated by *how many frames the encoder holds back* (lookahead, B-frames, frame threads). We measure this below.
* **Network:** over a short wired tether this is tiny (< 1 ms per hop) *unless* queues build up because the link is congested — then it can grow to hundreds of ms.
* **Jitter buffer:** the receiver deliberately waits so that late packets still arrive in time. Players for "normal" video default to large buffers (VLC's network caching default is 1000 ms; HLS players typically buffer several seconds).
* **Decode, render, display:** a few ms to decode; then the browser/OS compositor and the monitor's refresh add ~1–2 display frames.
""")

md(r"""
### 9.1 Measuring encoder delay frame by frame (PyAV)

We feed frames into x264 **one at a time** and count how many frames go in before the first compressed packet comes out. That count × frame time is the latency the encoder adds by *design*, regardless of how fast the CPU is.
""")

code(r'''
try:
    import av
    HAVE_AV = True
except ImportError:
    HAVE_AV = False
    print("PyAV not installed (pip install av) — skipping the frame-by-frame measurement; the budget below uses typical values.")

ENC_CONFIGS = {
    "x264 medium (defaults)":                 {"preset": "medium"},
    "x264 medium, no B-frames":               {"preset": "medium", "bf": "0"},
    "x264 medium, no B-frames, no lookahead": {"preset": "medium", "bf": "0", "x264-params": "rc-lookahead=0:sync-lookahead=0"},
    "x264 ultrafast":                         {"preset": "ultrafast"},
    "x264 veryfast + tune zerolatency":       {"preset": "veryfast", "tune": "zerolatency"},
}
enc_delay = {}
if HAVE_AV:
    src_frames = []
    with av.open(str(SRC)) as cont:
        for i, fr in enumerate(cont.decode(video=0)):
            src_frames.append(fr.reformat(format="yuv420p"))
            if i >= 89: break
    for label, opts in ENC_CONFIGS.items():
        ctx = av.CodecContext.create("libx264", "w")
        ctx.width, ctx.height, ctx.pix_fmt = W, H, "yuv420p"
        ctx.time_base = Fraction(1, FPS); ctx.framerate = Fraction(FPS, 1); ctx.options = dict(opts)
        first_out, times = None, []
        for i, fr in enumerate(src_frames):
            fr.pts = i
            t0 = time.perf_counter(); pkts = ctx.encode(fr); times.append(time.perf_counter() - t0)
            if pkts and first_out is None: first_out = i
        ctx.encode(None)  # flush
        held = (first_out if first_out is not None else len(src_frames))
        enc_delay[label] = {"frames held before first output": held, "delay from buffering (ms)": held * 1000 / FPS,
                            "mean time per encode() call (ms)": 1000 * np.mean(times[10:])}
    e9 = pd.DataFrame(enc_delay).T
    display(e9.style.format({"frames held before first output": "{:.0f}", "delay from buffering (ms)": "{:.0f}",
                             "mean time per encode() call (ms)": "{:.1f}"}))
''')

md(r"""
**Interpretation.** With default settings x264 holds back tens of frames (rate-control lookahead, B-frame decisions, frame-level threading) — that is often **more than a second of latency added by configuration alone**. `-tune zerolatency` disables lookahead and B-frames and switches to slice-based threading, so a frame comes out (almost) as soon as it goes in. Hardware encoders (Jetson's NVENC block) have their own low-latency settings — check the encoder's properties with `gst-inspect-1.0 nvv4l2h264enc`.

### 9.2 The jitter buffer trade-off

Packets do not arrive at perfectly regular intervals: queues in the switch, the SBC's network stack and the laptop all add variable delay (**jitter**). A receiver that displays frames *as soon as they arrive* shows stutter; one that waits too long adds latency. We simulate a tether with mostly small jitter and occasional 30–80 ms spikes (e.g. a CPU burst on the SBC).
""")

code(r'''
rng = np.random.default_rng(1)
n = 30 * 120                                             # two minutes at 30 FPS
base = 2.0                                                # ms, wire + switching
jitter = rng.gamma(2.0, 1.5, n)                           # small, everyday jitter
spikes = np.where(rng.random(n) < 0.02, rng.uniform(30, 80, n), 0)   # 2 % of frames hit a spike
delay = base + jitter + spikes
buffers = np.arange(0, 101, 5)
late_pct = [(delay > b).mean() * 100 for b in buffers]
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.plot(buffers, late_pct, "o-", color=PALETTE[0])
ax.set_xlabel("jitter buffer / playout delay (ms)"); ax.set_ylabel("frames that arrive too late (%)")
ax.set_title("Every millisecond of buffer buys smoothness and costs latency"); ax.set_ylim(bottom=0)
for b in (10, 40, 80):
    ax.annotate(f"{(delay > b).mean()*100:.1f} % late", (b, (delay > b).mean()*100), textcoords="offset points", xytext=(8, 8), fontsize=8)
plt.tight_layout(); plt.show()
''')

md(r"""
### 9.3 A latency budget for three pipelines — **ESTIMATE**

The numbers below are **typical orders of magnitude, not measurements of your system**. The encoder value of the H.264 pipelines comes from 9.1 when PyAV is available. The point is to see *which stage dominates* each design — then go and measure it (9.4).
""")

code(r'''
enc_default = enc_delay.get("x264 medium (defaults)", {}).get("delay from buffering (ms)", 1300)
enc_zl = enc_delay.get("x264 veryfast + tune zerolatency", {}).get("mean time per encode() call (ms)", 10)
STAGES = ["capture", "encode", "packetize + network", "jitter buffer", "decode", "render + display"]
BUDGETS = {   # ms — ESTIMATES (see text)
    "MJPEG over HTTP, browser <img>":           [33, 10, 3, 15, 5, 25],
    "H.264 x264 defaults → RTSP player (1 s cache)": [33, enc_default, 3, 1000, 8, 25],
    "H.264 zerolatency → WebRTC / RTP (≈50 ms buffer)": [33, enc_zl, 3, 50, 8, 25],
}
fig, ax = plt.subplots(figsize=(11, 3.6))
for i, (name, vals) in enumerate(BUDGETS.items()):
    left = 0
    for k, v in enumerate(vals):
        ax.barh(i, v, left=left, color=PALETTE[k], height=0.55, edgecolor="white", linewidth=1.5, label=STAGES[k] if i == 0 else None)
        left += v
    ax.text(left + 15, i, f"≈ {left:,.0f} ms", va="center", fontsize=9, fontweight="bold")
ax.set_yticks(range(len(BUDGETS)), BUDGETS.keys()); ax.invert_yaxis(); ax.set_xlabel("glass-to-glass latency (ms) — ESTIMATE")
ax.set_xlim(right=max(sum(v) for v in BUDGETS.values()) * 1.18)
ax.set_title("Which stage dominates? (HLS would add several more seconds — never use it for piloting)")
ax.legend(ncol=6, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22)); plt.tight_layout(); plt.show()
''')

md(r"""
### 9.4 How to measure glass-to-glass latency on the real ROV (no special equipment)

1. On the **topside laptop**, open a millisecond clock (e.g. a full-screen stopwatch web page, or run `python3 -c "import time; [print(f'{time.time()%100:7.3f}', end='\r') for _ in iter(int, 1)]"` in a large-font terminal).
2. Point one ROV camera **at that screen** (on deck, before the dive).
3. Put the ROV's video window **next to** the clock on the same screen.
4. Take a photo of the screen with a phone. The difference between the real clock and the clock *inside the video* is the glass-to-glass latency.
5. Repeat ≥ 10 times, for each camera and each configuration. Report the **median and the worst value**, not the best.

Variants: do it with 1 camera streaming, then all 8 — if latency jumps, you have found a congestion or CPU problem. Do it while the thrusters run at full power — if it jumps, suspect power/USB issues.

### Exercises
1. Which stage dominates *your* current system? Make a hypothesis, then measure.
2. Why does TCP-based streaming feel fine on the bench and become laggy during a mission? *(Hint: what happens to the TCP send buffer when the link briefly slows down?)*
3. Write a non-functional requirement for latency that is testable. (Example: "Glass-to-glass latency of the pilot camera ≤ 200 ms median and ≤ 300 ms worst case over 10 measurements, with all cameras streaming.")
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 10 — Hardware encoding

**Question.** Can the onboard computer encode in hardware, and how much does that change?

### What the two boards actually have (verified against vendor documentation — see References)

| | **NVIDIA Jetson Nano** (2019, Maxwell) | **Raspberry Pi 5** (BCM2712) |
|---|---|---|
| Hardware **encoder** | ✅ H.264 and H.265: up to 4K30 · 4× 1080p30 · 9× 720p30 *(NVIDIA spec)* | ❌ **none** — H.264 encoding is done in software (libx264) on the Cortex-A76 CPU *(Raspberry Pi white paper, 2026)* |
| Hardware **decoder** | ✅ H.264/H.265: up to 4K60 · 8× 1080p30 | ✅ **HEVC (H.265) only**, 4Kp60. No H.264 hardware decode |
| How to use the encoder | **GStreamer**: `nvv4l2h264enc`, `nvv4l2h265enc` (L4T Accelerated GStreamer). Also the Jetson Multimedia API (V4L2 M2M) | `libx264` via FFmpeg, GStreamer `x264enc`, or `rpicam-vid` (which uses libav/libx264 on Pi 5) |
| FFmpeg hardware encode | ❌ Upstream FFmpeg does **not** use the Nano's encoder. Community patches exist (`jetson-ffmpeg`, `h264_nvmpi`); NVIDIA's own FFmpeg package supports accelerated **decode** | ❌ (nothing to accelerate) |
| Software it runs | JetPack 4.x (Ubuntu 18.04). The Nano is supported up to JetPack 4.6.x | Raspberry Pi OS (Debian Bookworm/Trixie) |

> ⚠️ **Jetson Nano ≠ Jetson Orin Nano.** The newer *Orin* Nano has **no hardware video encoder**; NVIDIA states 1080p30 encoding is done with 1–2 CPU cores. Check which board you actually have: `cat /etc/nv_tegra_release` (L4T R32 = Nano/JetPack 4; R35/R36 = Orin).

**Measured Raspberry Pi 5 data point** (Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5-series computers*, 2026): a single 1080p30 libx264 encode needed roughly **62–90 % of one core** in a low-latency (`ultrafast` + zerolatency) configuration and **98–153 %** in a higher-quality (`superfast`) configuration, depending on bitrate. The paper does **not** test multiple simultaneous streams or thermal behaviour — that is your experiment.

### Deciding where to encode

| Option | Good when | Watch out for |
|---|---|---|
| **In the camera** (IP cameras, UVC cameras with built-in H.264) | Cameras already produce H.264/H.265 with substreams; the SBC only forwards | You depend on the camera's encoder settings and quirks; check GOP, bitrate control and latency options |
| **On the SBC — hardware** (Jetson Nano) | USB cameras delivering raw/MJPEG; ≤ 4× 1080p30 or ≤ 9× 720p30 total | Shared encoder capacity; MJPEG input must be **decoded first** (Jetson has an `nvjpegdec`/`nvv4l2decoder` path for that) |
| **On the SBC — software** (Raspberry Pi 5, Orin Nano) | A few streams at modest resolution, `ultrafast` + zerolatency | CPU budget for control software; **thermal throttling** in a sealed enclosure |
| **On the topside laptop** | Re-encoding for recording or for the browser (e.g. transcoding to a codec the browser decodes) | It does not help the tether at all — the bits already crossed it |

### 10.1 What can *this* machine do?
""")

code(r'''
def board_model():
    for f in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
        try: return Path(f).read_text(errors="ignore").strip("\x00\n ")
        except Exception: pass
    return platform.processor() or platform.machine()
IS_JETSON = Path("/etc/nv_tegra_release").exists()
MODEL = board_model(); IS_PI5 = "Raspberry Pi 5" in MODEL
print(f"Machine: {MODEL} | Jetson: {IS_JETSON} | Raspberry Pi 5: {IS_PI5} | cores: {CPU_CORES}")
if IS_JETSON: print(Path("/etc/nv_tegra_release").read_text().strip())

# Try each hardware encoder FFmpeg knows about with a 1-second test pattern. Being listed ≠ working!
TRY = {"h264_nvenc (NVIDIA desktop GPU)": ["-c:v", "h264_nvenc"],
       "h264_qsv (Intel Quick Sync)": ["-c:v", "h264_qsv"],
       "h264_vaapi (Intel/AMD via VA-API)": ["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi"],
       "h264_v4l2m2m (V4L2 mem2mem, e.g. Raspberry Pi 4)": ["-c:v", "h264_v4l2m2m"]}
rows = []
for name, args in TRY.items():
    pre = args[:2] if args[0] == "-vaapi_device" else []; post = args[2:] if pre else args
    r = run([FFMPEG, "-hide_banner", "-loglevel", "error", *pre, "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
             "-t", "1", *post, "-f", "null", "-"], check=False)
    rows.append({"encoder": name, "listed in ffmpeg -encoders": HAS.get(name.split()[0], False),
                 "works on this machine": r["rc"] == 0, "error (first line)": "" if r["rc"] == 0 else (r["stderr"].strip().splitlines() or ["?"])[0][:90]})
display(pd.DataFrame(rows).style.hide(axis="index"))
print("→ An encoder appearing in `ffmpeg -encoders` only means FFmpeg was COMPILED with it. Always run a test encode.")
''')

md(r"""
### 10.2 Software encoding capacity — the measurement you should repeat on the SBC

We encode frames with x264 (`ultrafast` and `veryfast`, both with `zerolatency`) on **one thread**, timing only the encoder, and measure how many frames per second one core sustains. Dividing by 30 FPS gives "how many 720p30 streams per core" — an *upper bound*, because real systems also capture, packetize, and run control software, and because a hot SBC throttles.
""")

code(r'''
def one_core_fps(w, h, preset="ultrafast", n=60):
    """Frames per second that ONE thread of x264 sustains at w×h (encode time only)."""
    if HAVE_AV:
        frames = [f.reformat(width=w, height=h, format="yuv420p") for f in src_frames[:n]]
        ctx = av.CodecContext.create("libx264", "w"); ctx.width, ctx.height, ctx.pix_fmt = w, h, "yuv420p"
        ctx.time_base = Fraction(1, FPS); ctx.framerate = Fraction(FPS, 1); ctx.thread_count = 1
        ctx.options = {"preset": preset, "tune": "zerolatency", "b": "2500k"}
        t0 = time.perf_counter()
        for i, fr in enumerate(frames):
            fr.pts = i; ctx.encode(fr)
        ctx.encode(None); return n / (time.perf_counter() - t0)
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-vf", f"scale={w}:{h}", "-c:v", "libx264",
             "-preset", preset, "-tune", "zerolatency", "-threads", "1", "-b:v", "2500k", "-f", "null", "-"])
    return N_FRAMES / r["wall_s"]          # fallback: includes scaling cost
cap = []
for (w, h) in ((640, 360), (1280, 720), (1920, 1080)):
    for pr in ("ultrafast", "veryfast"):
        fps1 = one_core_fps(w, h, pr)
        cap.append({"resolution": f"{w}×{h}", "preset": pr, "fps on ONE core": fps1, "30-FPS streams per core (upper bound)": fps1 / 30,
                    f"streams on {max(CPU_CORES-1,1)} spare cores": fps1 / 30 * max(CPU_CORES - 1, 1)})
display(pd.DataFrame(cap).style.format({"fps on ONE core": "{:.0f}", "30-FPS streams per core (upper bound)": "{:.1f}",
                                         f"streams on {max(CPU_CORES-1,1)} spare cores": "{:.1f}"}).hide(axis="index"))
''')

md(r"""
### 10.3 Platform-specific instructions (run these on the board, in a terminal)

#### Jetson Nano (JetPack 4.x) — *requires the hardware*
```bash
cat /etc/nv_tegra_release                 # confirm L4T R32.x (Jetson Nano)
gst-inspect-1.0 | grep -E "nvv4l2|omx"    # list NVIDIA encoder/decoder elements
gst-inspect-1.0 nvv4l2h264enc             # every property: bitrate, iframeinterval, preset-level, maxperf-enable...

# USB camera (MJPEG) → hardware JPEG decode → hardware H.264 encode → RTP/UDP to the topside laptop
gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 ! image/jpeg,width=1280,height=720,framerate=30/1 ! \
  nvv4l2decoder mjpeg=1 ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' ! \
  nvv4l2h264enc bitrate=2500000 iframeinterval=30 insert-sps-pps=true maxperf-enable=1 ! \
  h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=192.168.2.1 port=5600 sync=false

sudo tegrastats                           # watch NVENC / NVDEC activity, CPU load, temperatures
sudo jetson_clocks                        # (optional) lock clocks to max for benchmarking
```
Test each of 1, 2, 4, 6, 8 simultaneous pipelines and record `tegrastats` — you will find where the encoder or the USB bus saturates.

#### Raspberry Pi 5 — *requires the hardware; software encoding only*
```bash
cat /proc/device-tree/model; vcgencmd measure_temp; vcgencmd get_throttled   # 0x0 = never throttled
v4l2-ctl --list-devices; v4l2-ctl -d /dev/video0 --list-formats-ext           # what the USB camera can output

# USB camera (MJPEG) → software decode → x264 low latency → RTP/UDP
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2500k -maxrate 2500k -bufsize 1250k -g 30 \
  -pix_fmt yuv420p -f rtp rtp://192.168.2.1:5600

# If the camera itself can output H.264 (some UVC cameras can), DON'T re-encode — just forward:
ffmpeg -f v4l2 -input_format h264 -video_size 1920x1080 -framerate 30 -i /dev/video0 -c:v copy -f rtp rtp://192.168.2.1:5600
```
While N streams run, record `top` (or `htop`) and `vcgencmd measure_temp` every few seconds **inside the closed enclosure**. A Pi 5 without active cooling throttles under sustained load.

#### Development laptop / PC with a GPU
```bash
ffmpeg -hide_banner -encoders | grep -E "nvenc|qsv|vaapi|amf|videotoolbox"
ffmpeg -i work/source.mkv -c:v h264_nvenc -preset p1 -tune ll -b:v 2500k out_nvenc.mp4      # NVIDIA
ffmpeg -i work/source.mkv -c:v h264_qsv -preset veryfast -b:v 2500k out_qsv.mp4             # Intel
ffmpeg -i work/source.mkv -c:v h264_videotoolbox -b:v 2500k out_vt.mp4                       # macOS
```

### Exercises
1. On your SBC, find the maximum number of simultaneous 720p30 streams that run for **10 minutes** without dropped frames, without throttling, and with ≥ 1 CPU core free. That number is a real engineering constraint.
2. If your USB cameras deliver MJPEG, the SBC must *decode* before it can re-encode. Measure the cost of decode alone: `ffmpeg -f v4l2 -input_format mjpeg ... -i /dev/video0 -f null -`.
3. Would you choose a Jetson Nano or a Raspberry Pi 5 for an 8-camera ROV? Which measurements would change your mind?
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 11 — Final optimization challenge

> **Scenario.** You have **eight cameras**, a tether with **100 Mb/s** negotiated link speed (measured `iperf3` throughput: 94 Mb/s), an onboard computer with **limited encode capacity**, and a pilot who needs **responsive video** for docking, manipulation and inspection tasks.

**Requirements**

| ID | Requirement | Type |
|---|---|---|
| R1 | The pilot camera is ≥ 1280×720 at ≥ 25 FPS | functional / quality |
| R2 | The manipulator camera is ≥ 1280×720 at ≥ 20 FPS whenever the gripper is in use | functional |
| R3 | All eight cameras remain *visible* (at least as thumbnails ≥ 5 FPS) | functional |
| R4 | Total video ≤ 70 % of measured throughput, leaving ≥ 2 Mb/s for control/telemetry | non-functional |
| R5 | Total encode load ≤ the onboard encoder budget you choose below | non-functional |
| R6 | Estimated glass-to-glass latency of the pilot camera ≤ 200 ms | non-functional |
| R7 | Recovery from a packet-loss burst within ≤ 1 s | non-functional |

**Your task.** Edit `design` below, run `evaluate(design)`, iterate until all checks pass, and then — most importantly — **write a short justification of each choice, citing the measurements from Experiments 3–10.** A configuration that passes the checker but cannot be justified does not pass the challenge.
""")

code(r'''
ENCODER_BUDGETS = {   # pixel-rate budgets (pixels/s). Jetson Nano: 4×1080p30 ≈ 9×720p30 ≈ 249 Mpx/s (NVIDIA spec).
    "Jetson Nano hardware encoder": 4 * 1920 * 1080 * 30,
    # Raspberry Pi 5: ~0.65–0.9 core per 1080p30 ultrafast (RPi white paper). Assume 2.5 cores free for video, 0.8 core/1080p30:
    "Raspberry Pi 5 software (2.5 cores, ultrafast)": 2.5 / 0.8 * 1920 * 1080 * 30,
    "Cameras encode themselves (IP cameras)": float("inf"),
}

def evaluate(design, throughput_mbps=94, budget_name="Jetson Nano hardware encoder"):
    rows, ok = [], True
    total = sum(cam_mbps(c["codec"], c["res"], c["fps"]) for c in design["cameras"]) * (1 + OVERHEAD[design["transport"]])
    px_rate = sum(RES[c["res"]][0] * RES[c["res"]][1] * c["fps"] for c in design["cameras"] if c.get("encoded_on_sbc", True))
    pilot = next(c for c in design["cameras"] if c["role"] == "pilot"); manip = next(c for c in design["cameras"] if c["role"] == "manipulator")
    def check(rid, cond, detail):
        nonlocal ok; ok &= bool(cond); rows.append({"req": rid, "pass": "✅" if cond else "❌", "detail": detail})
    check("R1", RES[pilot["res"]][1] >= 720 and pilot["fps"] >= 25, f"pilot {pilot['res']}@{pilot['fps']}")
    check("R2", RES[manip["res"]][1] >= 720 and manip["fps"] >= 20, f"manipulator {manip['res']}@{manip['fps']}")
    check("R3", len(design["cameras"]) == 8 and all(c["fps"] >= 5 for c in design["cameras"]), f"{len(design['cameras'])} cameras, min fps {min(c['fps'] for c in design['cameras'])}")
    check("R4", total <= 0.7 * throughput_mbps and throughput_mbps - total >= 2, f"{total:.1f} Mb/s on the wire = {total/throughput_mbps:.0%} of {throughput_mbps}")
    check("R5", px_rate <= ENCODER_BUDGETS[budget_name], f"{px_rate/1e6:.0f} Mpx/s vs budget {ENCODER_BUDGETS[budget_name]/1e6:.0f} Mpx/s ({budget_name})")
    lat = 33 + design["encoder_delay_frames"] * 1000 / pilot["fps"] + 3 + design["jitter_buffer_ms"] + 8 + 25
    check("R6", lat <= 200, f"≈ {lat:.0f} ms (ESTIMATE: capture 33 + encoder hold + network 3 + buffer + decode 8 + display 25)")
    check("R7", design["gop_s"] <= 1.0 or design.get("intra_refresh", False), f"GOP {design['gop_s']} s, intra refresh: {design.get('intra_refresh', False)}")
    display(pd.DataFrame(rows).style.hide(axis="index"))
    print("ALL CHECKS PASS — now write the justification!" if ok else "Not yet — iterate.")
    return ok

# A deliberately naive starting design (it fails). Improve it.
design = {
    "transport": "RTP/UDP", "gop_s": 2.0, "intra_refresh": False, "encoder_delay_frames": 40, "jitter_buffer_ms": 200,
    "cameras": [{"role": "pilot", "codec": "H.264", "res": "1920×1080", "fps": 30},
                {"role": "manipulator", "codec": "H.264", "res": "1920×1080", "fps": 30}] +
               [{"role": "aux", "codec": "H.264", "res": "1920×1080", "fps": 30} for _ in range(6)],
}
evaluate(design)
''')

md(r"""
**Deliverable for each team (1 page):**

1. The final `design` and the `evaluate()` output.
2. For each requirement: *which measurement* supports your choice (cite the experiment and the number).
3. The **biggest risk** in your design and the test that would expose it on the real ROV.
4. What you would measure **first** on the actual vehicle to validate the model (hint: link speed, encoder capacity under heat, real bits-per-pixel of your cameras).

**Scoring (Activity 5 rubric, summarized):** correctness of the numbers (25 %), quality of justification from measurements (35 %), risk identification and test plan (25 %), clarity (15 %).

---
## What to take back to the ROV

1. **Find out what you actually have** — USB or IP cameras, which codec, which protocol, which link speed. (Diagnostic Checklist.)
2. **Compression beats resolution cuts.** Moving from MJPEG to H.264 typically saves far more bandwidth than halving the resolution.
3. **Plan on peaks, not averages.** Use capped rate control for live video; keep ≥ 30 % headroom.
4. **Not every camera needs full quality all the time.** Main streams + substreams + priorities.
5. **Latency is designed.** Zero-latency encoder settings, short buffers, UDP-based transport, no HLS for piloting.
6. **Know your silicon.** Jetson Nano: hardware H.264/H.265 encoder via GStreamer. Raspberry Pi 5: software encoding only. Orin Nano: no encoder.
7. **Measure everything twice** — once in this notebook, once on the vehicle, inside the closed enclosure, with everything running.
""")

code(r'''
# Summary of key numbers measured in this run (paste into your team's engineering log)
summary = {
    "machine": MODEL, "ffmpeg": run([FFMPEG, "-hide_banner", "-version"])["stdout"].splitlines()[0],
    "raw 1080p30 RGB24 (Mb/s)": round(raw_mbps(1920, 1080, 30, 24)),
    "H.264 CRF23 clip bitrate (Mb/s)": round(float(e3[(e3['mode']=='CRF') & (e3['setting']=='crf 23')]['bitrate_Mb/s'].iloc[0]), 2),
    f"SSIM target used": SSIM_TARGET,
    "bits/pixel at target": {k: round(v, 4) for k, v in CODEC_BPP.items()},
    "x264 default encoder hold (frames)": enc_delay.get("x264 medium (defaults)", {}).get("frames held before first output"),
    "x264 zerolatency hold (frames)": enc_delay.get("x264 veryfast + tune zerolatency", {}).get("frames held before first output"),
}
(WORK / "summary.json").write_text(json.dumps(summary, indent=2, default=str)); print(json.dumps(summary, indent=2, default=str))
''')
