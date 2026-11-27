"""Session notebook, part 4: diagnostics (slides 54–61) and the final challenge (slide 62)."""
from snb_common import md, code, part, exp

part("05", "Diagnostics", "54–61", "One cause, one stage. Measure before you change anything.")

exp("54 · 72", "Where is the problem?", "Latency drift: a queue that only grows", "30 fps in, 29.7 fps out: 10 ms more delay every second.", "live")
md(r"""
**Try it.** Frames arrive at the camera's rate and leave at the display's rate. If they arrive even slightly faster, a queue grows and nobody notices until the pilot is seconds behind. Then put a limit on the queue.
""")
code(r'''
def drift_view(camera_fps, display_fps, queue_limit, minutes):
    t = np.linspace(0, minutes * 60, 600)
    surplus = max(camera_fps - display_fps, 0)                   # frames per second that pile up
    waiting = surplus * t
    if queue_limit != "no limit":
        waiting = np.minimum(waiting, queue_limit)
    latency = 33 + waiting * 1000 / display_fps
    dropped = surplus * minutes * 60 - waiting[-1]
    cards([("delay after", f"{latency[-1] / 1000:.2f} s", f"{minutes} min into the dive", latency[-1] < 150),
           ("growth", f"{surplus * 1000 / display_fps:.0f} ms / s" if queue_limit == "no limit" else "capped",
            "while the queue is unlimited"),
           ("frames dropped", f"{dropped:,.0f}", "the cure: drop old frames, keep new ones")])
    plt.figure(figsize=(10, 3)); plt.plot(t / 60, latency, color=MIA_RED)
    plt.xlabel("minutes"); plt.ylabel("delay (ms)"); plt.title("The picture the pilot sees falls behind"); plt.tight_layout(); plt.show()


panel("drift", "Latency drift", "A rate mismatch you can't see until it's seconds long",
      {"camera_fps": ("options", [25, 29.97, 30, 30.3], 30, "frames in (fps)"), "display_fps": ("options", [25, 29.7, 29.97, 30, 60], 29.7, "frames shown (fps)"),
       "queue_limit": ("options", ["no limit", 1, 2, 5], "no limit", "queue limit (frames)"), "minutes": ("int", (1, 30, 1), 10, "dive length (min)")}, drift_view, live=True)
''')
md(r"""
**Look for**
- 0.3 frames per second of surplus is invisible on any fps counter, and it's still 6 seconds of delay after 10 minutes.
- A queue of 1–2 frames that drops the oldest frame keeps the delay flat. Every queue in the pipeline needs a limit.
""")

exp(73, "Field guide", "A frozen picture that looks live", "The fps counter keeps saying 30 while the frame on screen gets older.", "live")
md(r"""
**Try it.** The stream stops for a moment (a crashed encoder, a camera dropping off USB). The renderer keeps redrawing the last frame, so the fps counter never moves. Only the **age of the frame** shows the freeze. Choose when the STALE badge should appear.
""")
code(r'''
def stale_view(freeze_at, freeze_len, threshold_ms):
    t = np.arange(0, 10, 1 / 60)                                  # the screen refreshes at 60 Hz
    captures = np.arange(0, 10, 1 / 30)
    captures = captures[(captures < freeze_at) | (captures >= freeze_at + freeze_len)]
    last = captures[np.searchsorted(captures, t, side="right") - 1]
    age = (t - last) * 1000
    warned = age > threshold_ms
    blind = (age[(t >= freeze_at) & (t < freeze_at + freeze_len)] <= threshold_ms).sum() / 60
    cards([("fps counter", "30.0", "during the whole freeze", False),
           ("worst frame age", f"{age.max():,.0f} ms", "what the pilot actually saw"),
           ("STALE shown", "never" if not warned.any() else f"after {threshold_ms} ms", "", warned.any()),
           ("driving on an old picture, unwarned", f"{blind:.2f} s", "", blind < 0.6)])
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.plot(t, age, color=PALETTE[0], label="age of the frame on screen")
    ax.axhline(threshold_ms, color=MIA_RED, ls="--", label=f"STALE after {threshold_ms} ms")
    ax.fill_between(t, 0, age.max() * 1.05, where=warned, color=MIA_RED, alpha=0.12, label="badge visible")
    ax.set_xlabel("time (s)"); ax.set_ylabel("ms"); ax.legend(fontsize=8, loc="upper left"); plt.tight_layout(); plt.show()


panel("stale", "Stale frame", "Show the frame's age, not just the fps",
      {"freeze_at": ("float", (1, 7, 0.5), 3, "freeze starts (s)"), "freeze_len": ("options", [0.2, 0.5, 1, 2, 3], 2, "freeze lasts (s)"),
       "threshold_ms": ("options", [100, 250, 500, 1000, 3000], 500, "STALE after (ms)")}, stale_view, live=True)
''')
md(r"""
**Look for**
- The field guide's rule: STALE after 500 ms without a new frame, LOST after a few seconds. Experiment E14 (`kill -STOP` on the encoder) checks whether our GUI does it.
""")

exp(57, "Measure latency three ways", "Your glass-to-glass readings", "Ten photos of the ms clock: report the median and the worst.", "live")
md(r"""
**Try it.** Type your ten readings from experiment E1 (clock on the screen minus clock in the video, in ms), separated by commas.
""")
code(r'''
def g2g_view(readings):
    try:
        v = np.array([float(x) for x in readings.replace(";", ",").replace(" ", ",").split(",") if x.strip()])
    except ValueError:
        print("Numbers only, separated by commas."); return
    if len(v) < 3:
        print("Type at least three readings."); return
    med, p95, worst = np.median(v), np.percentile(v, 95), v.max()
    cards([("readings", f"{len(v)}", "10 is the minimum for a report"),
           ("median", f"{med:.0f} ms", "target ≤ 150", med <= 150), ("p95", f"{p95:.0f} ms", "1 in 20 is worse"),
           ("worst", f"{worst:.0f} ms", "target ≤ 250", worst <= 250)])
    plt.figure(figsize=(9, 1.8)); plt.scatter(v, np.zeros_like(v), s=60, color=PALETTE[0], alpha=0.8)
    for x_, lab in ((150, "150"), (250, "250")): plt.axvline(x_, color=MIA_RED, ls="--", lw=1)
    plt.axvline(med, color="#111", lw=2); plt.yticks([]); plt.xlabel("ms (black = median, red = targets)"); plt.tight_layout(); plt.show()


panel("g2g", "Glass-to-glass readings", "Median and worst, never one number",
      {"readings": ("text", None, "126, 131, 118, 142, 129, 135, 121, 160, 127, 133", "readings (ms)")}, g2g_view, live=True)
''')

exp(61, "The checklist", "Run the health check", "Check in pipeline order. The first ❌ is usually the cause.", "run")
md(r"""
`docs/debug/rov_healthcheck.sh` runs 25 of the debug checklist's 45 checks on the ROV computer in about ten seconds. It only makes sense on the ROV, so this cell prints the command unless you start Jupyter there with `RUN_ON_ROV=1` (add `TOPSIDE=<ip>` and `CAMS=<n>`).
""")
code(r'''
HEALTH = Path("../../docs/debug/rov_healthcheck.sh").resolve()
if os.environ.get("RUN_ON_ROV") == "1" and HEALTH.exists():
    args = ["--md", *(["--top", os.environ["TOPSIDE"]] if os.environ.get("TOPSIDE") else []),
            *(["--cams", os.environ["CAMS"]] if os.environ.get("CAMS") else [])]
    display(Markdown(run(["bash", str(HEALTH), *args], check=False)["stdout"]))
else:
    print("On the ROV computer:\n")
    print(f"    sudo bash {HEALTH.relative_to(HEALTH.parents[2]) if HEALTH.exists() else 'docs/debug/rov_healthcheck.sh'} --top <topside IP> --cams <N>\n")
    print("Paste the --md output into the bug report. Full checklist: docs/debug/ROV_Debug_Checklist.md")
''')

# =================================================================================================== PART 06
part("06", "Putting it together", "62", "Measure → stop wasting bits → stream smart → design latency → design failure → verify.")

exp(62, "A practical optimization strategy", "Design the eight-camera system", "Every requirement is checked against the numbers measured above.", "live")
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
The design above fails on purpose. **Try it:** fix it with the panel. Resolution is the last lever you should reach for, not the first.
""")
code(r'''
def design_view(pilot, manip, aux, gop_s, intra_refresh, zerolatency, jitter_ms, board, throughput):
    res_fps = lambda s: (s.split(" @ ")[0], int(s.split(" @ ")[1]))
    (pr, pf), (mr, mf), (ar, af) = res_fps(pilot), res_fps(manip), res_fps(aux)
    design = {"transport": "RTP/UDP", "gop_s": gop_s, "intra_refresh": intra_refresh,
              "encoder_delay_frames": 0 if zerolatency else 40, "jitter_buffer_ms": jitter_ms,
              "cameras": [{"role": "pilot", "codec": "H.264", "res": pr, "fps": pf},
                          {"role": "manipulator", "codec": "H.264", "res": mr, "fps": mf}] +
                         [{"role": "aux", "codec": "H.264", "res": ar, "fps": af} for _ in range(6)]}
    evaluate(design, throughput_mbps=throughput, budget_name=board)


STREAM_CHOICES = [f"{r} @ {f}" for r in RES for f in (5, 10, 15, 20, 25, 30)]
panel("design", "Your design", "Seven requirements, checked live",
      {"pilot": ("dropdown", STREAM_CHOICES, "1920×1080 @ 30", "pilot camera"), "manip": ("dropdown", STREAM_CHOICES, "1920×1080 @ 30", "manipulator"),
       "aux": ("dropdown", STREAM_CHOICES, "1920×1080 @ 30", "each aux camera (6)"),
       "gop_s": ("options", [0.5, 1.0, 2.0, 5.0], 2.0, "keyframe every (s)"), "jitter_ms": ("options", [20, 40, 60, 100, 200], 200, "jitter buffer (ms)"),
       "board": ("dropdown", list(ENCODER_BUDGETS), "Jetson Nano hardware encoder", "who encodes"),
       "throughput": ("options", [94, 940], 94, "measured throughput (Mb/s)"),
       "intra_refresh": ("check", None, False, "intra refresh"), "zerolatency": ("check", None, False, "-tune zerolatency")}, design_view, live=True)
''')
md(r"""
**Your deliverable (one page):** the design that passes, why each choice, the numbers it rests on, and which of them you still have to measure on the real ROV. The ROV experiments (`docs/experiments/ROV_Experiments.md`) are where those numbers come from.
""")

exp(62, "Engineering log", "What this run measured", "Paste these into your team's log.", "run")
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
