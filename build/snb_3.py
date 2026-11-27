"""Session notebook, part 3: Part 04 of the deck, hardware, protocols and latency (slides 41–53)."""
from snb_common import md, code, part, exp

part("04", "Hardware, protocols and latency", "41–53", "Who does the work, how the bits travel, and where the milliseconds go.")

exp(42, "Who does the work?", "Is the hardware encoder really there?", "Listed is not working: always try a one-second encode.", "run")
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
**Look for**
- An encoder in `ffmpeg -encoders` only means FFmpeg was built with it. On a laptop without the GPU, every hardware encoder above fails.
- On a Jetson Nano the encoder is used through GStreamer (`nvv4l2h264enc`), not upstream FFmpeg. On a Raspberry Pi 5 there is no H.264 hardware encoder at all.
""")

exp("43–45", "Jetson Nano vs Raspberry Pi 5", "How many streams can the ROV computer encode?", "Measure one core here, then compare with the boards.", "run")
md(r"""
First we measure how many frames per second **one core of this computer** encodes with x264 (PyAV if installed, otherwise FFmpeg with one thread).
""")
code(r'''
from fractions import Fraction
try:
    import av
    HAVE_AV = True
except ImportError:
    HAVE_AV = False
    print("PyAV is not installed (pip install av): using FFmpeg with one thread instead.")

src_frames = []
if HAVE_AV:
    with av.open(str(SRC)) as cont:
        for i, fr in enumerate(cont.decode(video=0)):
            src_frames.append(fr.reformat(format="yuv420p"))
            if i >= 89:
                break
''')
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
**Try it.** Now plan the ROV computer. The Jetson Nano's encoder is rated 4 × 1080p30 (NVIDIA). The Pi 5 has no encoder; Raspberry Pi's April 2026 white paper measured 0.62–0.9 of one Cortex-A76 core per 1080p30 low-latency stream. These are vendor numbers, not ours: soak-test before you buy (slide 45).
""")
code(r'''
BOARD_RES = {"640×360": (640, 360), "1280×720": (1280, 720), "1920×1080": (1920, 1080)}
P1080 = 1920 * 1080 * 30


def board_view(board, streams, res, fps, pi_core_cost, free_cores):
    w, h = BOARD_RES[res]; px = streams * w * h * fps
    if board == "Jetson Nano":
        load = px / (4 * P1080); fit = int(4 * P1080 // (w * h * fps)); detail = "share of the hardware encoder"
    elif board == "Raspberry Pi 5":
        need = px / P1080 * pi_core_cost; load = need / free_cores
        fit = int(free_cores / (w * h * fps / P1080 * pi_core_cost)); detail = f"{need:.1f} of {free_cores} free cores"
    else:
        load, fit, detail = 0.0, 99, "the computer only forwards packets"
    cards([("load", f"{load:.0%}", detail, load <= 0.7),
           ("streams that fit", "any" if fit >= 99 else f"{fit}", f"{res} @ {fps} fps"),
           ("verdict", "OK" if load <= 0.7 else ("tight" if load <= 1 else "over"), "plan for 70 % or less", load <= 0.7)])
    plt.figure(figsize=(9, 1.4)); plt.barh([0], [min(load, 2) * 100], color=GOOD if load <= 0.7 else (PALETTE[3] if load <= 1 else BAD), height=0.5)
    plt.axvline(70, ls="--", color="#52514e"); plt.axvline(100, color="#52514e"); plt.xlim(0, 200); plt.yticks([])
    plt.xlabel("% of the encoding budget (dashed = 70 %)"); plt.tight_layout(); plt.show()


panel("board", "Encoder budget", "Who encodes decides which board wins",
      {"board": ("toggle", ["Jetson Nano", "Raspberry Pi 5", "Cameras encode themselves"], "Jetson Nano", "who encodes"),
       "streams": ("int", (1, 8, 1), 8, "streams"), "res": ("options", list(BOARD_RES), "1280×720", "resolution"),
       "fps": ("options", [10, 15, 30], 30, "fps"), "pi_core_cost": ("options", [0.62, 0.76, 0.9], 0.76, "Pi 5 cores per 1080p30"),
       "free_cores": ("options", [1.0, 2.0, 2.5, 3.0, 3.5], 2.5, "Pi 5 cores free for video")}, board_view, live=True)
''')
md(r"""
**Look for**
- Eight 720p30 streams fit the Nano's encoder (9 × 720p30 is its limit). On a Pi 5 the same job needs far more cores than it has.
- If the cameras encode themselves, the board only forwards packets, and the Pi 5's faster CPU becomes the better choice.
- Also watch out for the Jetson **Orin** Nano: no hardware video encoder at all.
""")

exp(46, "Reliability lesson from 2023", "Read the throttle flags", "The stream died from heat; the Pi tells you if it has throttled.", "live")
md(r"""
**Try it.** On a Raspberry Pi run `vcgencmd get_throttled` and paste the value here (for example `0x50005`). `0x0` means nothing ever happened. To log it every second during a soak test:

```bash
while true; do echo "$(date +%T) $(vcgencmd measure_temp) $(vcgencmd get_throttled)"; sleep 1; done | tee soak.log
```
""")
code(r'''
THROTTLE_BITS = {0: "under-voltage now", 1: "CPU frequency capped now", 2: "throttled now", 3: "soft temperature limit now",
                 16: "under-voltage has happened since boot", 17: "frequency capping has happened", 18: "throttling has happened",
                 19: "soft temperature limit has happened"}


def throttle_view(value):
    try:
        v = int(value.strip().split("=")[-1], 0)
    except ValueError:
        print("Type a value like 0x50005."); return
    rows = [{"bit": b, "meaning": m, "set?": "YES" if v >> b & 1 else "no"} for b, m in THROTTLE_BITS.items()]
    power, heat = v & 0x10001, v & 0xE000E
    cards([("value", hex(v), "0x0 = nothing ever happened", v == 0),
           ("power", "problem" if power else "OK", "supply sagged below 4.63 V" if power else "no under-voltage", not power),
           ("heat / clocks", "problem" if heat else "OK", "the CPU slowed itself down" if heat else "never throttled", not heat)])
    display(pd.DataFrame(rows).style.hide(axis="index"))
    if power:
        note("Fix the power first: a separate regulated 5 V for the computer and cameras, thicker and shorter wires.")
    elif heat:
        note("Heat path to the hull (thermal pad → aluminium plate → hull → water), less software encoding, soak-test 30 min.")


panel("throttle", "Throttle flags", "Decode vcgencmd get_throttled",
      {"value": ("text", None, "0x50005", "get_throttled value")}, throttle_view, live=True)
''')

exp(47, "Getting bits to the browser", "TCP or UDP when packets get lost?", "UDP loses a little and never waits. TCP never loses and waits.", "live")
md(r"""
**Try it.** This is a **simulation**, not a measurement. Video flows at a fixed rate over a link. With UDP, a lost packet damages the picture until the next keyframe, but the delay never changes. With TCP, a lost packet holds everything behind it until it's resent; the queue then drains with whatever spare capacity the link has. Push the stream close to the link speed and watch what TCP does.
""")
code(r'''
def transport_view(link, stream, loss_pct, rtt_ms, retransmit, gop_s):
    dt, seconds = 0.01, 60
    n = int(seconds / dt); rng = np.random.default_rng(4)
    pkts = stream * 1e6 / 8 / 1316 * dt                          # packets per step
    losses = rng.poisson(pkts * loss_pct / 100, n)
    stall = 3 * rtt_ms / 1000 if retransmit.startswith("fast") else 0.2
    backlog, blocked_until, tcp = 0.0, -1.0, np.empty(n)
    damaged = np.zeros(n, bool); next_key = np.ceil(np.arange(n) * dt / gop_s) * gop_s
    for i in range(n):
        t = i * dt
        if losses[i]:
            blocked_until = max(blocked_until, t + stall)
            damaged[i:int(next_key[i] / dt) + 1] = True             # UDP: broken until the next keyframe
        arrive = stream * 1e6 * dt
        sent = 0.0 if t < blocked_until else min(link * 1e6 * dt, backlog + arrive)
        backlog += arrive - sent
        tcp[i] = rtt_ms / 2 + backlog / (link * 1e6) * 1000
    t = np.arange(n) * dt
    if stream >= link:
        note("The video is bigger than the link. UDP would drop the excess every second; TCP queues it and the delay never stops growing.")
    cards([("UDP delay", f"{rtt_ms / 2:.1f} ms", "constant"),
           ("UDP picture damaged", f"{damaged.mean():.1%}", "of the time, until each next keyframe", damaged.mean() < 0.02),
           ("TCP delay, median", f"{np.median(tcp):,.0f} ms", "queue behind lost packets"),
           ("TCP delay, worst", f"{tcp.max():,.0f} ms", "in this minute", tcp.max() < 150)])
    fig, ax = plt.subplots(figsize=(12, 3.4))
    ax.plot(t, tcp, color=PALETTE[0], label="TCP: delay"); ax.axhline(rtt_ms / 2, color=MIA_RED, label="UDP: delay")
    ax.fill_between(t, 0, np.where(damaged, ax.get_ylim()[1] if tcp.max() > 1 else 1, 0), color=MIA_RED, alpha=0.12, step="mid", label="UDP: picture damaged")
    ax.set_xlabel("time (s)"); ax.set_ylabel("ms"); ax.set_title("SIMULATION: one minute of video"); ax.legend(loc="upper left", fontsize=8)
    plt.tight_layout(); plt.show()


panel("transport", "TCP vs UDP", "Same link, same loss, two transports",
      {"link": ("options", [10, 20, 50, 100], 20, "link (Mb/s)"), "stream": ("float", (1, 19, 0.5), 8, "video (Mb/s)"),
       "loss_pct": ("options", [0, 0.01, 0.05, 0.1, 0.5, 1.0], 0.1, "packet loss (%)"),
       "rtt_ms": ("options", [1, 5, 20, 50], 5, "round trip (ms)"),
       "gop_s": ("options", [0.5, 1.0, 2.0, 5.0], 1.0, "keyframe every (s)"),
       "retransmit": ("toggle", ["fast retransmit (3 × RTT)", "timeout (200 ms)"], "timeout (200 ms)", "TCP resends after")}, transport_view, live=True)
''')
md(r"""
**Look for**
- With UDP the delay is flat; loss shows up as damaged moments that end at the next keyframe (so a short GOP matters, slide 39).
- With TCP nothing is damaged, but every loss adds a pause. When the video uses most of the link, the queue never catches up: that's the "latency that grows during the dive".
- That's why the pilot stream uses RTP over UDP or WebRTC, and never HLS.
""")

exp(48, "Experiment 9 estimate", "Build your own latency budget", "FPS is not latency: a perfect 30 fps stream can be two seconds late.", "live")
md(r"""
**Try it.** Pick each stage the way our system is set up today, then fix the biggest bar first. These are **estimates** built from typical values and our one measured number (x264 defaults hold 41 frames). Measure the real total with the ms-clock photo (slide 57, experiment E1).
""")
code(r'''
ENCODER_HOLD = {"x264 zerolatency (0 frames)": 0, "MJPEG (0 frames)": 0, "x264 defaults (41 frames)": 41}
PLAYER = {"low-delay player (0 ms)": 0, "VLC default cache (1,000 ms)": 1000, "HLS in a browser (≈ 6,000 ms)": 6000}
SCREEN = {"monitor 60 Hz (≈ 17 ms)": 17, "TV in game mode (≈ 25 ms)": 25, "TV, normal mode (≈ 100 ms)": 100}


def budget_view(fps, encoder, encode_ms, network_ms, jitter_ms, player, decode_ms, screen):
    stages = {"capture": 1000 / fps, "encode": ENCODER_HOLD[encoder] * 1000 / fps + encode_ms, "network": network_ms,
              "jitter buffer": jitter_ms, "player cache": PLAYER[player], "decode": decode_ms, "display": SCREEN[screen]}
    total = sum(stages.values()); worst = max(stages, key=stages.get)
    cards([("glass-to-glass", f"{total:,.0f} ms", "target ≤ 150 ms", total <= 150),
           ("biggest stage", worst, f"{stages[worst]:,.0f} ms: fix this first"),
           ("network share", f"{network_ms / total:.0%}", "the cable is rarely the problem")])
    fig, ax = plt.subplots(figsize=(12, 3.2)); left = 0
    for k, (name, v) in enumerate(stages.items()):
        ax.barh(0, v, left=left, color=[MIA_RED, *PALETTE][k % 9], edgecolor="white", height=0.5, label=f"{name}: {v:,.0f} ms")
        left += v
    ax.axvline(150, color="#111", ls="--", lw=1); ax.text(150, 0.32, " target 150 ms", fontsize=8)
    ax.set_ylim(-0.4, 0.45); ax.set_xlim(0, max(left, 160) * 1.03); ax.set_yticks([])
    ax.set_xlabel("glass-to-glass, ms (ESTIMATE)"); ax.set_title(f"≈ {left:,.0f} ms from the camera to the pilot's eye")
    fig.legend(ncol=4, fontsize=8.5, loc="lower center", frameon=False); fig.subplots_adjust(left=0.03, right=0.98, top=0.85, bottom=0.42)
    plt.show()


panel("budget", "Latency budget", "Where the milliseconds go",
      {"encoder": ("toggle", list(ENCODER_HOLD), "x264 defaults (41 frames)", "encoder"),
       "player": ("toggle", list(PLAYER), "VLC default cache (1,000 ms)", "player"),
       "screen": ("toggle", list(SCREEN), "TV in game mode (≈ 25 ms)", "screen"),
       "fps": ("options", [15, 25, 30, 60], 30, "camera fps"), "encode_ms": ("int", (1, 40, 1), 9, "encode time (ms)"),
       "network_ms": ("options", [1, 3, 10, 30], 3, "network (ms)"), "jitter_ms": ("options", [0, 15, 30, 50, 100, 200], 50, "jitter buffer (ms)"),
       "decode_ms": ("int", (1, 30, 1), 8, "decode (ms)")}, budget_view, live=True)
''')
md(r"""
**Look for**
- The default setup on the slide is about 2.4 s; zerolatency + a low-delay player + game mode gets it near 130 ms. The cable is a few ms either way.
- Check the pipeline in this order: player buffer, encoder hold, screen, then everything else.
""")

exp(49, "Experiment 9 measured", "How many frames does the encoder hold?", "x264 defaults hold about a second; zerolatency holds none.", "run")
code(r'''
ENC_CONFIGS = {
    "x264 medium (defaults)":                 {"preset": "medium"},
    "x264 medium, no B-frames":               {"preset": "medium", "bf": "0"},
    "x264 medium, no B-frames, no lookahead": {"preset": "medium", "bf": "0", "x264-params": "rc-lookahead=0:sync-lookahead=0"},
    "x264 ultrafast":                         {"preset": "ultrafast"},
    "x264 veryfast + tune zerolatency":       {"preset": "veryfast", "tune": "zerolatency"},
}
enc_delay = {}
if HAVE_AV:
    for label, opts in ENC_CONFIGS.items():
        ctx = av.CodecContext.create("libx264", "w")
        ctx.width, ctx.height, ctx.pix_fmt = W, H, "yuv420p"
        ctx.time_base = Fraction(1, FPS); ctx.framerate = Fraction(FPS, 1); ctx.options = dict(opts)
        first_out, times = None, []
        for i, fr in enumerate(src_frames):
            fr.pts = i
            t0 = time.perf_counter(); pkts = ctx.encode(fr); times.append(time.perf_counter() - t0)
            if pkts and first_out is None:
                first_out = i
        ctx.encode(None)
        held = first_out if first_out is not None else len(src_frames)
        enc_delay[label] = {"frames held before first output": held, "delay from holding (ms)": held * 1000 / FPS,
                            "time per encode() call (ms)": 1000 * np.mean(times[10:])}
    display(pd.DataFrame(enc_delay).T.style.format("{:.0f}", subset=["frames held before first output", "delay from holding (ms)"])
            .format("{:.1f}", subset=["time per encode() call (ms)"]))
else:
    print("Needs PyAV (pip install av). The slide's numbers: defaults held 41 frames (≈ 1,367 ms), zerolatency 0.")
''')
md(r"""
The other half of latency is on the receiver: the **jitter buffer**. **Try it:** a bigger buffer means fewer late frames and more delay.
""")
code(r'''
def jitter_view(jitter_ms, spike_pct, buffer_ms):
    rng = np.random.default_rng(1); n = 30 * 120
    delay = 2 + rng.gamma(2.0, jitter_ms / 2, n) + np.where(rng.random(n) < spike_pct / 100, rng.uniform(30, 80, n), 0)
    buffers = np.arange(0, 151, 5); late = [(delay > b).mean() * 100 for b in buffers]
    cards([("late frames", f"{(delay > buffer_ms).mean():.1%}", "arrive after the buffer gave up", (delay > buffer_ms).mean() < 0.01),
           ("latency added", f"{buffer_ms} ms", "every frame waits this long"),
           ("p95 network delay", f"{np.percentile(delay, 95):.0f} ms", "size the buffer near this")])
    plt.figure(figsize=(9, 3.2)); plt.plot(buffers, late, "o-", color=PALETTE[0], ms=4)
    plt.axvline(buffer_ms, color=MIA_RED, ls="--"); plt.xlabel("jitter buffer (ms)"); plt.ylabel("late frames (%)")
    plt.title("Smoothness costs latency"); plt.tight_layout(); plt.show()


panel("jitter", "Jitter buffer", "Two minutes of simulated frame arrivals",
      {"jitter_ms": ("options", [1, 3, 6, 10, 20], 3, "everyday jitter (ms)"), "spike_pct": ("options", [0, 0.5, 1, 2, 5], 2, "frames hit by a spike (%)"),
       "buffer_ms": ("int", (0, 150, 5), 40, "buffer (ms)")}, jitter_view, live=True)
''')
md(r"""
**Look for**
- Each preset holds a different number of frames; `zerolatency` holds 0. That one flag is worth about a second.
- On a clean tether a 30–60 ms buffer is usually enough. Wi-Fi hops and congested switches push it up.
""")

exp(50, "Experiment 8", "Eight cameras on one tether", "Main streams for what the pilot watches, substreams for the rest.", "live")
md(r"""
First the budget for whole configurations (bits per pixel calibrated from the codec curves above), then a panel to try your own.
""")
code(r'''
P_REF = W * H
OVERHEAD = {"RTP/UDP": 1538 / 1460 - 1, "MPEG-TS/UDP": (1382 / 1316) * (188 / 184) - 1,
            "WebRTC (SRTP/UDP)": 0.07, "MJPEG over HTTP (TCP)": 0.06}
RES = {"320×180": (320, 180), "640×360": (640, 360), "640×480": (640, 480), "1280×720": (1280, 720), "1920×1080": (1920, 1080)}

def cam_mbps(codec, res, fps):
    w, h = RES[res]
    return CODEC_BPP[codec] * w * h * fps * (P_REF / (w * h)) ** 0.25 / 1e6

def simulate(name, cams, transport="RTP/UDP"):
    """cams: list of (count, codec, resolution, fps). Returns total on-the-wire Mb/s."""
    total = sum(n * cam_mbps(c, r, f) for n, c, r, f in cams)
    return {"scenario": name, "video_Mb/s": total, "wire_Mb/s": total * (1 + OVERHEAD[transport]), "transport": transport}

SCENARIOS = [
    simulate("8 × MJPEG 640×480@30 (a common student setup)", [(8, "MJPEG", "640×480", 30)], "MJPEG over HTTP (TCP)"),
    simulate("8 × MJPEG 1280×720@30", [(8, "MJPEG", "1280×720", 30)], "MJPEG over HTTP (TCP)"),
    simulate("8 × MJPEG 1920×1080@30", [(8, "MJPEG", "1920×1080", 30)], "MJPEG over HTTP (TCP)"),
    simulate("8 × H.264 1280×720@30", [(8, "H.264", "1280×720", 30)]),
    simulate("8 × H.264 1920×1080@30", [(8, "H.264", "1920×1080", 30)]),
    simulate("1 main H.264 1080p30 + 7 subs 640×360@15", [(1, "H.264", "1920×1080", 30), (7, "H.264", "640×360", 15)]),
    simulate("2 main 1080p30 + 2 subs + 4 thumbnails 320×180@5", [(2, "H.264", "1920×1080", 30), (2, "H.264", "640×360", 15), (4, "H.264", "320×180", 5)]),
]
if "H.265" in CODEC_BPP:
    SCENARIOS.append(simulate("8 × H.265 1920×1080@30", [(8, "H.265", "1920×1080", 30)]))
sim = pd.DataFrame(SCENARIOS)
LINK = 100; HEADROOM = 0.70
def verdict(x, link=LINK):
    return "OVER capacity" if x > link else ("Above 70 % — tight" if x > HEADROOM * link else "OK")
sim["on 100 Mb/s"] = sim["wire_Mb/s"].apply(lambda x: verdict(x, 100))
sim["on 1 Gb/s"] = sim["wire_Mb/s"].apply(lambda x: verdict(x, 1000))
display(sim.style.format({"video_Mb/s": "{:.1f}", "wire_Mb/s": "{:.1f}"}).hide(axis="index"))
''')
code(r'''
STATUS = {"OK": "#2e7d32", "Above 70 % — tight": "#ed8b00", "OVER capacity": CRITICAL}
fig, ax = plt.subplots(figsize=(11, 4.6))
y = np.arange(len(sim))
ax.barh(y, sim["wire_Mb/s"], color=[STATUS[v] for v in sim["on 100 Mb/s"]], height=0.6)
for yi, (v, s) in enumerate(zip(sim["wire_Mb/s"], sim["on 100 Mb/s"])):
    ax.text(v * 1.05, yi, f"{v:.1f} Mb/s · {s}", va="center", fontsize=8.5)
for x_, lab, ls in ((LINK * HEADROOM, "70 % of a 100 Mb/s link", ":"), (LINK, "100 Mb/s link", "-"), (1000 * HEADROOM, "70 % of a 1 Gb/s link", "--")):
    ax.axvline(x_, color="#52514e", ls=ls, lw=1.2, label=lab)
ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
ax.set_yticks(y, sim["scenario"]); ax.invert_yaxis(); ax.set_xscale("log"); ax.xaxis.set_major_formatter(FuncFormatter(mbps_fmt))
ax.set_xlabel("aggregate on-the-wire bitrate (Mb/s, log)"); ax.set_title("Eight cameras: which configurations fit a 100 Mb/s tether?")
ax.set_xlim(right=sim["wire_Mb/s"].max() * 6); plt.tight_layout(); plt.show()
''')
code(r'''
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

panel("e7", "Eight-camera budget", "Instant calculation: change anything and the verdict updates",
             {"n_main": ("int", (0, 8, 1), 1, "main streams"), "main_res": ("options", list(RES), "1920×1080", "main resolution"),
              "main_fps": ("int", (5, 60, 5), 30, "main fps"), "n_sub": ("int", (0, 8, 1), 7, "substreams"),
              "sub_res": ("options", list(RES), "640×360", "sub resolution"), "sub_fps": ("int", (1, 30, 1), 15, "sub fps"),
              "codec": ("options", list(CODEC_BPP), "H.264", "codec"), "link_mbps": ("options", [100, 1000], 100, "link (Mb/s)"),
              "transport": ("options", list(OVERHEAD), "RTP/UDP", "transport")}, explore, live=True)
''')
code(r'''
# EXERCISE: describe YOUR vehicle here (count, codec, resolution, fps) and run the cell.
my_design = [(1, "H.264", "1280×720", 30), (3, "H.264", "640×360", 15), (4, "MJPEG", "320×180", 5)]
r = simulate("my design", my_design); print(r, "→", verdict(r["wire_Mb/s"], 100), "on 100 Mb/s")
''')
md(r"""
Now real substreams: we encode a main stream, a substream and a thumbnail and look at them at the size of a tile on the pilot's screen.
""")
code(r'''
STREAMS = {
    "main 1280×720@30, 2.5 Mb/s":  (1280, 720, 30, 2500),
    "sub 640×360@15, 0.4 Mb/s":    (640, 360, 15, 400),
    "thumb 320×180@10, 0.12 Mb/s": (320, 180, 10, 120),
}
rows = {}
for label, (w, h, fps, kb) in STREAMS.items():
    out = WORK / f"e8_{w}x{h}.mp4"
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-vf", f"scale={w}:{h}:flags=area,fps={fps}",
             "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-b:v", f"{kb}k", "-maxrate", f"{kb}k",
             "-bufsize", f"{kb // 2}k", "-g", str(fps), "-pix_fmt", "yuv420p", "-an", str(out)])
    p = probe(out); psnr, ssim = quality(out, SRC)   # scored after upscaling back to 1280×720
    rows[label] = {"bitrate_Mb/s": p["bitrate_mbps"], "SSIM (upscaled to 720p)": ssim, "file": out}
e8 = pd.DataFrame(rows).T
display(e8.drop(columns="file").astype(float).style.format("{:.3f}"))

fig, axs = plt.subplots(1, 3, figsize=(13, 2.6))
for ax, (label, row) in zip(axs, rows.items()):
    png = WORK / f"e8_{Path(str(row['file'])).stem}.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", "2.0", "-i", str(row["file"]), "-frames:v", "1", str(png)])
    ax.imshow(plt.imread(png)); ax.set_title(label, fontsize=9); ax.axis("off")
plt.suptitle("Shown at the SAME display size — a thumbnail tile on the pilot screen", fontweight="bold"); plt.tight_layout(); plt.show()
''')
code(r'''
m, s, t = (float(e8.iloc[i]["bitrate_Mb/s"]) for i in range(3))
strategies = {"8 × main (everything full quality)": 8 * m, "1 main + 7 sub": m + 7 * s, "2 main + 6 sub": 2 * m + 6 * s,
              "1 main + 3 sub + 4 thumbnails": m + 3 * s + 4 * t}
fig, ax = plt.subplots(figsize=(9, 3.2))
ax.barh(list(strategies), list(strategies.values()), color=PALETTE[0], height=0.55)
for yi, v in enumerate(strategies.values()):
    ax.text(v, yi, f"  {v:.1f} Mb/s ({v / strategies['8 × main (everything full quality)']:.0%})", va="center", fontsize=9)
ax.invert_yaxis(); ax.set_xlabel("aggregate video bitrate (Mb/s) — measured streams"); ax.set_title("Stream strategy for 8 cameras")
ax.set_xlim(right=max(strategies.values()) * 1.35); plt.tight_layout(); plt.show()
''')
code(r'''
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

panel("e8", "Design a substream", "How small can a thumbnail stream be before it stops being useful?",
             {"width": ("options", [256, 320, 426, 512, 640, 854, 960], 640, "width (16:9)"),
              "fps": ("int", (2, 30, 1), 15, "fps"),
              "kbps": ("options", [60, 100, 150, 250, 400, 600, 1000], 400, "bitrate (kb/s)")}, tune_substream)
''')
md(r"""
**Look for**
- 1 main + 7 substreams needs roughly a quarter of "everything at full quality" (slide 50: 5.4 vs 19.8 Mb/s).
- A substream only has to answer "is something happening there?" When the pilot makes a camera big, switch it to the main stream.
""")

exp(51, "Camera selection", "Share a shrinking tether", "Give every camera its minimum by priority, then top up.", "live")
code(r'''
def allocate(budget, cams):
    """cams: list of dicts with name, priority (1 = highest), min, max (Mb/s). Returns {name: Mb/s} (0 = paused)."""
    alloc = {c["name"]: 0.0 for c in cams}; order = sorted(cams, key=lambda c: c["priority"]); left = budget
    for c in order:                                    # pass 1: minimums, highest priority first
        if left >= c["min"]: alloc[c["name"]] = c["min"]; left -= c["min"]
    for c in order:                                    # pass 2: top up to max, highest priority first
        if alloc[c["name"]] > 0:
            add = min(c["max"] - alloc[c["name"]], left); alloc[c["name"]] += add; left -= add
    return alloc

CAMS = ([{"name": "Pilot main camera", "priority": 1, "min": 1.5, "max": 8.0},
         {"name": "Manipulator camera", "priority": 2, "min": 0.8, "max": 5.0}] +
        [{"name": f"Aux camera {i}", "priority": 3 + i, "min": 0.15, "max": 1.0} for i in range(1, 7)])
t = np.arange(0, 40, 0.5)
capacity = np.where(t < 10, 100, np.where(t < 20, 40, np.where(t < 30, 20, np.where(t < 33, 6, 100))))
budget = capacity * HEADROOM / (1 + OVERHEAD["RTP/UDP"]) - 1.0     # 1 Mb/s reserved for control + telemetry
series = pd.DataFrame([allocate(b, CAMS) for b in budget], index=t)
groups = {"Pilot main camera": series["Pilot main camera"], "Manipulator camera": series["Manipulator camera"],
          "6 aux cameras (total)": series.filter(like="Aux").sum(axis=1)}
fig, ax = plt.subplots(figsize=(11, 4))
ax.stackplot(t, *groups.values(), labels=groups.keys(), colors=PALETTE[:3], edgecolor="white", linewidth=0.8)
ax.plot(t, budget, color="#0b0b0b", lw=1.5, ls="--", label="video budget (70 % of link, minus control)")
paused = series.filter(like="Aux").eq(0).sum(axis=1)
for tt, n in zip(t[::4], paused.values[::4]):
    if n: ax.text(tt, 1.5, f"{n} paused", fontsize=7, rotation=90, color="#52514e")
ax.set_xlabel("time (s)"); ax.set_ylabel("Mb/s"); ax.set_title("Priority-based allocation while the tether degrades")
ax.legend(loc="upper right", fontsize=8); plt.tight_layout(); plt.show()
''')
md(r"""
**Try it.** Shrink the link and see who keeps their bits. Tick **gripping** to make the manipulator camera priority 1.
""")
code(r'''
def share_view(link_mbps, gripping):
    cams = [dict(c) for c in CAMS]
    if gripping:
        cams[1]["priority"] = 0.5
    budget = max(link_mbps * HEADROOM / (1 + OVERHEAD["RTP/UDP"]) - 1.0, 0)
    alloc = allocate(budget, cams)
    paused = [k for k, v in alloc.items() if v == 0]
    cards([("video budget", rate(budget), "70 % of the link, minus 1 Mb/s for control"),
           ("pilot camera", rate(alloc["Pilot main camera"]), "min 1.5 · max 8", alloc["Pilot main camera"] > 0),
           ("manipulator", rate(alloc["Manipulator camera"]), "priority 1 while gripping" if gripping else "priority 2"),
           ("paused", f"{len(paused)}", "shown as PAUSED on the pilot screen", len(paused) == 0)])
    names = list(alloc)
    plt.figure(figsize=(10, 3.2))
    plt.barh(names, [alloc[k] for k in names], color=[GREY if alloc[k] == 0 else (MIA_RED if i < 2 else PALETTE[0]) for i, k in enumerate(names)])
    for i, k in enumerate(names):
        if alloc[k] == 0: plt.text(0.05, i, "PAUSED", va="center", fontsize=8, color=GREY)
    plt.gca().invert_yaxis(); plt.xlabel("Mb/s"); plt.tight_layout(); plt.show()


panel("share", "Priority allocator", "The tether degrades; the pilot camera stays sharp",
      {"link_mbps": ("options", [2, 4, 6, 10, 20, 40, 100], 20, "link (Mb/s)"), "gripping": ("check", None, False, "manipulator is gripping")}, share_view, live=True)
''')

exp(52, "Streaming for computer vision", "What compression does to corners", "Feature trackers (SLAM, photogrammetry) need the corners the encoder throws away.", "encode")
md(r"""
**Try it.** We find the 200 strongest corners in the original frame (Shi–Tomasi, the kind ORB and SLAM use), then look for them again after encoding. Raise the CRF and watch them disappear.
""")
code(r'''
from scipy.ndimage import sobel, maximum_filter
from scipy.spatial import cKDTree


def corners(g, n=200):
    """The n strongest Shi–Tomasi corners: points where the image changes in two directions."""
    ix, iy = sobel(g, 1), sobel(g, 0)
    a, b, c = gaussian_filter(ix * ix, 1.5), gaussian_filter(iy * iy, 1.5), gaussian_filter(ix * iy, 1.5)
    resp = (a + b) / 2 - np.sqrt(((a - b) / 2) ** 2 + c * c)
    ys, xs = np.nonzero((resp == maximum_filter(resp, 9)) & (resp > 0))
    top = np.argsort(resp[ys, xs])[::-1][:n]
    return np.stack([ys[top], xs[top]], 1)


REF_CORNERS = corners(REF_Y)


def cv_view(crf):
    res = encode_cached(["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-crf", str(crf)], "cv")
    dec = gray(frame_png(res["file"], 2.0, "cv"))
    found = corners(dec)
    d, _ = cKDTree(found).query(REF_CORNERS)
    kept = d <= 2
    cards([("bitrate", rate(res["bitrate"]), f"CRF {crf}"), ("SSIM", f"{res['ssim']:.3f}", "looks fine to a viewer?"),
           ("corners kept", f"{kept.mean():.0%}", "within 2 px of the original", kept.mean() >= 0.8)])
    plt.figure(figsize=(11, 6.2)); plt.imshow(dec, cmap="gray", vmin=0, vmax=255)
    plt.scatter(REF_CORNERS[kept, 1], REF_CORNERS[kept, 0], s=22, facecolors="none", edgecolors=GOOD, label="kept")
    plt.scatter(REF_CORNERS[~kept, 1], REF_CORNERS[~kept, 0], s=22, marker="x", color=BAD, label="lost")
    plt.legend(loc="lower right"); plt.axis("off"); plt.tight_layout(); plt.show()


panel("cv", "Corners after compression", "Green = still found · red = lost",
      {"crf": ("int", (16, 46, 2), 30, "CRF")}, cv_view)
''')
md(r"""
**Look for**
- SSIM can still look respectable while a large share of the corners is gone. A metric for viewers isn't a metric for algorithms.
- Rules from slide 52: run CV next to the raw frames when you can; otherwise give CV its own stream with more bits, no B-frames and timestamps.
""")
