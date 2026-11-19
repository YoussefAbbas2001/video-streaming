# Notebook builder — part 2: Experiments 5–8.
from nb_part1 import md, code

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 5 — GOP, keyframes, and what happens when packets are lost

**Question.** How often should the encoder send a full picture (I-frame), and why does it matter on a tether?

**Theory.**

* **I-frame (intra):** coded using only itself — like a JPEG. Big. A decoder can start here.
* **P-frame (predicted):** coded as *differences* from earlier frames, using motion vectors. Small.
* **B-frame (bi-predicted):** may also reference a *future* frame — so the encoder must wait for that future frame → **adds latency**. Live low-latency streams usually disable B-frames.
* **GOP (Group of Pictures):** the run of frames from one I-frame to the next. `-g 30` at 30 FPS = one I-frame per second.

Three consequences for an ROV:

| GOP length | Bitrate | Joining a stream / switching camera | Recovery after packet loss |
|---|---|---|---|
| **Short** (e.g. 0.5–1 s) | higher (more big I-frames) | fast — wait ≤ 1 GOP for the next I-frame | fast — the next I-frame repairs the picture |
| **Long** (e.g. 5–10 s) | lower | slow — black/grey screen for up to 5–10 s | slow — smeared, broken picture until the next I-frame |

Worst-case wait to start decoding a new stream:  $t_{\text{join}} \le \dfrac{\text{GOP}}{f}$ (unless the receiver can request a keyframe — RTSP/WebRTC players can, via RTCP PLI/FIR).

**Commands.** We force a fixed GOP with `-g N -keyint_min N -sc_threshold 0` (the last flag disables extra I-frames at scene cuts so the comparison is clean). We also run one encode with a long GOP and **scene-cut detection enabled** (x264's default) to see the encoder insert an I-frame by itself at t = 4 s.
""")

code(r'''
GOPS = [10, 30, 60, 150]
rows, ftypes = [], {}
def gop_encode(name, extra):
    out = WORK / f"e5_{name}.mp4"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", "medium",
         "-crf", "23", *extra, "-pix_fmt", "yuv420p", "-an", str(out)])
    return out
for g in GOPS:
    out = gop_encode(f"g{g}", ["-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0"])
    ft = frame_types(out); ftypes[f"GOP {g}"] = ft; p = probe(out)
    rows.append({"variant": f"GOP {g} (fixed)", "I-frames": int((ft.type == "I").sum()), "bitrate_Mb/s": p["bitrate_mbps"],
                 "avg_I_kB": ft[ft.type == "I"]["size"].mean() / 1e3, "avg_P_kB": ft[ft.type == "P"]["size"].mean() / 1e3,
                 "avg_B_kB": ft[ft.type == "B"]["size"].mean() / 1e3, "worst_join_wait_s": g / FPS})
out = gop_encode("g300_scenecut", ["-g", "300"])           # long GOP, scene-cut detection ON (default)
ft = frame_types(out); ftypes["GOP 300 + scenecut"] = ft; p = probe(out)
rows.append({"variant": "GOP 300 + scene-cut detection", "I-frames": int((ft.type == "I").sum()), "bitrate_Mb/s": p["bitrate_mbps"],
             "avg_I_kB": ft[ft.type == "I"]["size"].mean() / 1e3, "avg_P_kB": ft[ft.type == "P"]["size"].mean() / 1e3,
             "avg_B_kB": ft[ft.type == "B"]["size"].mean() / 1e3, "worst_join_wait_s": 300 / FPS})
e5 = pd.DataFrame(rows)
display(e5.style.format({"bitrate_Mb/s": "{:.2f}", "avg_I_kB": "{:.1f}", "avg_P_kB": "{:.1f}", "avg_B_kB": "{:.1f}",
                         "worst_join_wait_s": "{:.1f}"}).hide(axis="index"))
i_frames = ftypes["GOP 300 + scenecut"].index[ftypes["GOP 300 + scenecut"].type == "I"].tolist()
print("GOP 300 + scenecut — I-frames at frame numbers:", i_frames, "(the scene cut is at frame 118–120)")
''')

code(r'''
ft = ftypes["GOP 30"].iloc[:96]
colors = {"I": PALETTE[1], "P": PALETTE[0], "B": PALETTE[2]}
fig, ax = plt.subplots(figsize=(11, 3.6))
for t in ("I", "P", "B"):
    sel = ft[ft.type == t]
    ax.bar(sel.index, sel["size"] / 1e3, color=colors[t], width=0.85, label=f"{t}-frames")
ax.set_xlabel("frame number (decode order)"); ax.set_ylabel("compressed size (kB)")
ax.set_title("GOP 30: the I-frame spikes every second are what a live link must absorb"); ax.legend()
plt.tight_layout(); plt.show()
''')

md(r"""
### 5.1 Simulating packet loss on the tether

Now we break things on purpose. We stream-encode three variants as **MPEG-TS** (the container used for UDP streaming), with **no B-frames** (`-tune zerolatency`) and a **capped bitrate**, as a live ROV stream would be:

1. **GOP 30** — an I-frame every second.
2. **GOP 150** — an I-frame every 5 seconds.
3. **Periodic intra refresh** — *no* I-frames at all after the first. Instead, a vertical column of intra-coded blocks sweeps across the picture over 30 frames, so the image "heals" continuously. This removes the I-frame bitrate spikes, which is why it is popular in low-latency links (drones, video conferencing).

Then we **delete 42 consecutive MPEG-TS packets** (≈ 6 UDP datagrams, ≈ 8 kB), decode the damaged file, and measure PSNR of every frame against the original. We repeat the loss at three different moments (1.4 s, 2.5 s, 3.3 s), because recovery depends on *where in the GOP or refresh cycle* the loss lands.
""")

code(r'''
LOSS_T = 1.4                       # the loss we plot and look at
LOSS_TIMES = [1.4, 2.5, 3.3]       # repeat at three positions — one loss point is an anecdote, not a measurement
DROP_TS_PACKETS = 42               # 6 UDP datagrams × 7 TS packets
VARIANTS = {
    "GOP 30 (I-frame every 1 s)":   ["-g", "30", "-keyint_min", "30", "-sc_threshold", "0"],
    "GOP 150 (I-frame every 5 s)":  ["-g", "150", "-keyint_min", "150", "-sc_threshold", "0"],
    "Intra refresh over 30 frames": ["-g", "30", "-sc_threshold", "0", "-x264-params", "intra-refresh=1"],
}

def damage_seconds(clean, damaged):
    """Duration between the first and last frame that is > 3 dB worse than the undamaged encode."""
    n = min(len(clean), len(damaged)); bad = np.where(clean[:n] - damaged[:n] > 3)[0]
    return (bad.max() - bad.min() + 1) / FPS if len(bad) else 0.0

loss, rows = {}, []
for label, extra in VARIANTS.items():
    tag = re.sub(r"\W+", "_", label)[:20]
    ts = WORK / f"e5_{tag}.ts"
    # -threads 1: multi-threaded x264 with a capped bitrate is not bit-exact between runs; one thread makes this reproducible
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, "-c:v", "libx264", "-preset", "veryfast",
         "-tune", "zerolatency", "-threads", "1", "-b:v", "2000k", "-maxrate", "2000k", "-bufsize", "700k", *extra,
         "-pix_fmt", "yuv420p", "-an", "-f", "mpegts", str(ts)])
    pk = packets(ts); start_pts = pk["pts"].min(); data = ts.read_bytes()
    _, _, pf_clean = quality(ts, SRC, per_frame=True)
    durations = []
    for k, t_loss in enumerate(LOSS_TIMES):
        pos = int(pk.loc[(pk["pts"] - start_pts - t_loss).abs().idxmin(), "pos"]); pos -= pos % 188   # TS packet boundary
        damaged = WORK / f"e5_{tag}_damaged{k}.ts"
        damaged.write_bytes(data[:pos] + data[pos + 188 * DROP_TS_PACKETS:])
        dec = WORK / (f"e5_{tag}_decoded.mkv" if k == 0 else f"e5_{tag}_decoded{k}.mkv")
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(damaged), "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(dec)])
        _, _, pf_dam = quality(dec, SRC, per_frame=True)
        durations.append(damage_seconds(pf_clean, pf_dam))
        if k == 0: loss[label] = {"clean": pf_clean, "damaged": pf_dam, "ts": ts}
    rows.append({"variant": label, **{f"loss at {t}s": d for t, d in zip(LOSS_TIMES, durations)},
                 "mean damaged (s)": np.mean(durations), "worst (s)": np.max(durations)})
e5_loss = pd.DataFrame(rows)
display(e5_loss.style.format({c: "{:.2f}" for c in e5_loss.columns if c != "variant"}).hide(axis="index"))

fig, ax = plt.subplots(figsize=(11, 4.2))
for k, (label, d) in enumerate(loss.items()):
    ax.plot(np.arange(len(d["damaged"])) / FPS, d["damaged"], label=label, color=PALETTE[k], lw=1.6)
ax.axvline(LOSS_T, color="#52514e", ls=":", lw=1); ax.text(LOSS_T + 0.05, 12, "packets lost here", fontsize=8, color="#52514e")
ax.set_ylim(10, None); ax.set_xlabel("time (s)"); ax.set_ylabel("per-frame PSNR vs original (dB)")
ax.set_title(f"Recovery after losing {DROP_TS_PACKETS} TS packets (~{DROP_TS_PACKETS*188/1000:.0f} kB) at t = {LOSS_T} s"); ax.legend(loc="lower right")
plt.tight_layout(); plt.show()
''')

code(r'''
# What the pilot sees 0.5 s after the loss, and the bitrate smoothness of intra refresh
fig, axs = plt.subplots(1, 3, figsize=(13, 2.7))
for ax, (label, d) in zip(axs, loss.items()):
    tag = re.sub(r"\W+", "_", label)[:20]; png = WORK / f"e5_{tag}_after.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(LOSS_T + 0.5), "-i", str(WORK / f"e5_{tag}_decoded.mkv"), "-frames:v", "1", str(png)])
    ax.imshow(plt.imread(png)); ax.set_title(label, fontsize=9); ax.axis("off")
plt.suptitle(f"Frame at t = {LOSS_T + 0.5:.1f} s (0.5 s after the loss)", fontweight="bold"); plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(11, 3.4))
for k, label in enumerate(["GOP 30 (I-frame every 1 s)", "Intra refresh over 30 frames"]):
    pk = packets(loss[label]["ts"]); ax.plot(np.arange(len(pk)) / FPS, pk["size"] / 1e3, label=label, color=PALETTE[[0, 2][k]], lw=1.3)
ax.set_xlabel("time (s)"); ax.set_ylabel("frame size (kB)"); ax.set_title("Intra refresh spreads the I-frame cost over many frames")
ax.legend(); plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation.**

* With a **long GOP**, a single burst of loss corrupts the picture for seconds: the decoder keeps predicting from a broken reference. With a **short GOP**, the damage lasts at most until the next I-frame. **Intra refresh** heals progressively, within about one refresh period (here 0.5–0.7 s for a 30-frame refresh at 30 FPS) — *and* it has no I-frame bitrate spikes.
* Look at the GOP 150 row: the damage lasts until the next I-frame at t = 5 s (3.6 s for the loss at 1.4 s). For the loss at 2.5 s it stopped earlier, at the camera **cut** at t ≈ 4 s, because that frame is coded almost entirely with intra blocks. Being rescued by a lucky scene change is not a design — plan for the worst case.
* The short-GOP cost is bitrate (the table above). On a reliable, short, wired tether with little loss, 1–2 s GOPs are a common compromise; if you see loss, shorten the GOP or use intra refresh — and **find the cause of the loss** (Diagnostic Checklist).
* **Switching cameras** in the pilot UI has the same physics: a player that starts a new stream mid-GOP shows nothing until an I-frame arrives. If camera switching "takes a second or two", your GOP is probably 1–2 s long. Options: shorter GOP, request a keyframe on switch, or keep a decoder running per camera (substreams!).

### Exercises
1. Change `DROP_TS_PACKETS` to 7 (a single UDP datagram). Is the damage still visible?
2. Why does TCP (e.g. RTSP-over-TCP, HTTP) not show this kind of corruption — and what does it show instead when the link is congested? *(Hint: retransmission → growing delay → frozen video.)*
3. Your pilot complains: "When I switch to the rear camera it takes about 2 seconds to appear." Write down two hypotheses and the measurement that would distinguish them.
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 6 — Measuring quality objectively: PSNR, SSIM, VMAF

**Question.** "It looks fine to me" is not a measurement. How do professionals put a number on video quality — and when should we not trust that number?

### PSNR — Peak Signal-to-Noise Ratio
For an 8-bit image $I$ (original) and $K$ (compressed), both $W \times H$:

$$
\text{MSE} = \frac{1}{WH}\sum_{x,y}\big(I(x,y)-K(x,y)\big)^2, \qquad
\text{PSNR} = 10\log_{10}\frac{255^2}{\text{MSE}} \;\; [\text{dB}]
$$

* Higher is better. Rough guide for 8-bit video: < 30 dB clearly degraded, 35–40 dB good, > 45 dB nearly transparent.
* +6 dB ≈ halving the average pixel error. PSNR is cheap, simple, and **blind to how humans see**: every pixel error counts the same, whether it is in a smooth gradient or invisible in texture.

### SSIM — Structural Similarity
SSIM compares local windows of the two images on three things humans notice: brightness ($\mu$), contrast ($\sigma$), and structure (correlation $\sigma_{xy}$):

$$
\text{SSIM}(x,y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2+\mu_y^2+C_1)(\sigma_x^2+\sigma_y^2+C_2)}
$$

averaged over all windows. 1.0 = identical. Values above ~0.95 are usually good; SSIM is much more sensitive to blur and blocking than PSNR.

### VMAF — Video Multi-method Assessment Fusion
Netflix's metric: several elementary features (detail loss, visual information fidelity, motion) are fused by a machine-learning model **trained on human opinion scores** for TV/film viewing. 0–100 scale. It correlates best with human opinion *for entertainment content on a TV*. It needs FFmpeg built with `libvmaf`.

### Limitations — read this twice
* All three are **full-reference** metrics: they need the original. On the live ROV you don't have it; you measure in the lab, then choose settings.
* They measure *fidelity to the original*, not *usefulness to the pilot*. A pilot needs to read a gauge, see a crack, judge distance. A metric trained on movies does not know that.
* Underwater footage (noise, particles, haze) can be scored "badly" by PSNR simply because the encoder removed sensor noise — which may actually look *better*.
* So: **use metrics to compare settings; use pilots to decide what is good enough.**
""")

code(r'''
CURVES = {
    # Metric-neutral tuning: -tune ssim (x264/x265) and tune=1 (PSNR) for SVT-AV1 — see the note below.
    "H.264 (x264 medium)":  ("libx264",   [18, 23, 28, 33, 38], lambda q: ["-c:v", "libx264", "-preset", "medium", "-tune", "ssim", "-crf", str(q), "-pix_fmt", "yuv420p"], "mp4"),
    "H.265 (x265 medium)":  ("libx265",   [18, 23, 28, 33, 38], lambda q: ["-c:v", "libx265", "-preset", "medium", "-tune", "ssim", "-crf", str(q), "-pix_fmt", "yuv420p", "-x265-params", "log-level=error"], "mp4"),
    "MJPEG":                ("mjpeg",     [2, 4, 8, 16, 31],    lambda q: ["-c:v", "mjpeg", "-q:v", str(q), "-pix_fmt", "yuvj420p"], "mkv"),
    "AV1 (SVT-AV1 p8)":     ("libsvtav1", [24, 32, 40, 48, 56], lambda q: ["-c:v", "libsvtav1", "-preset", "8", "-crf", str(q), "-svtav1-params", "tune=1", "-pix_fmt", "yuv420p"], "mkv"),
}
rows = []
for codec, (enc, qs, mk, ext) in CURVES.items():
    if not HAS.get(enc): print("skip", codec); continue
    for q in qs:
        out = WORK / f"e6_{enc}_{q}.{ext}"
        if not out.exists():
            run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *SRC_IN, *mk(q), "-an", str(out)])
        p = probe(out); psnr, ssim = quality(out, SRC)
        rows.append({"codec": codec, "q": q, "bitrate_Mb/s": p["bitrate_mbps"], "PSNR_dB": psnr, "SSIM": ssim, "file": out})
e6 = pd.DataFrame(rows)

fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
for k, (codec, g) in enumerate(e6.groupby("codec", sort=False)):
    for ax, m in zip(axs, ("PSNR_dB", "SSIM")):
        ax.plot(g["bitrate_Mb/s"], g[m], "o-", color=PALETTE[k], label=codec)
for ax, m in zip(axs, ("PSNR (dB)", "SSIM")):
    ax.set_xscale("log"); ax.xaxis.set_major_formatter(FuncFormatter(mbps_fmt)); ax.set_xlabel("bitrate (Mb/s, log)"); ax.set_ylabel(m); ax.legend()
axs[0].set_title("The fair way to compare codecs: whole curves"); axs[1].set_title("Same data, SSIM")
plt.tight_layout(); plt.show()
''')

md(r"""
> **Why `-tune ssim`?** By default x264, x265 and SVT-AV1 use *psychovisual* optimisations (psy-RD, adaptive quantization) that make video look better to people but deliberately *lower* PSNR/SSIM. If you compare codecs with a metric while each encoder optimises for something else, you are measuring the tuning, not the codec. So for this comparison every encoder is tuned for the metric. For the pilot's live view you would normally keep the default (subjective) tuning.

**Reading the curves:** a curve that is further **left** reaches the same quality with fewer bits. The horizontal distance between two curves at the same quality is the bitrate saving — this is the idea behind the industry's **BD-rate** (Bjøntegaard delta rate) metric.

Below we interpolate each curve to find the bitrate needed for the same quality — we use the SSIM that x264 reaches at its default CRF 23 as the target — and express it as **bits per pixel** — the number we will reuse to size the eight-camera system in Experiment 7.
""")

code(r'''
def bitrate_at(g, metric, target):
    g = g.sort_values(metric)
    if not (g[metric].min() <= target <= g[metric].max()): return np.nan
    return float(np.exp(np.interp(target, g[metric], np.log(g["bitrate_Mb/s"]))))

# Two operating points: a constrained-tether point (SSIM 0.96) and the quality x264 reaches at its default CRF 23.
lo = e6.groupby("codec")["SSIM"].min().max(); hi = e6.groupby("codec")["SSIM"].max().min()
ssim_crf23 = float(e6[(e6.codec == "H.264 (x264 medium)") & (e6.q == 23)].SSIM.iloc[0])   # x264 CRF 23, tune ssim
SSIM_TARGET = round(float(np.clip(ssim_crf23, lo + 0.001, hi - 0.001)), 3)
SSIM_LOW = round(float(np.clip(0.96, lo + 0.001, hi - 0.001)), 3)
rows = []
for codec, g in e6.groupby("codec", sort=False):
    r_lo, r_hi = bitrate_at(g, "SSIM", SSIM_LOW), bitrate_at(g, "SSIM", SSIM_TARGET)
    rows.append({"codec": codec, f"Mb/s @ SSIM {SSIM_LOW}": r_lo, f"Mb/s @ SSIM {SSIM_TARGET}": r_hi,
                 "bits_per_pixel (high)": r_hi * 1e6 / (W * H * FPS)})
equal_q = pd.DataFrame(rows)
for col_ in (f"Mb/s @ SSIM {SSIM_LOW}", f"Mb/s @ SSIM {SSIM_TARGET}"):
    ref = equal_q.loc[equal_q.codec.str.startswith("H.264"), col_].iloc[0]
    equal_q["vs H.264 " + col_.split("@ ")[1]] = equal_q[col_] / ref
display(equal_q.style.format({c: ("{:.2f}×" if c.startswith("vs") else "{:.4f}" if "bits" in c else "{:.2f}") for c in equal_q.columns if c != "codec"}).hide(axis="index"))
CODEC_BPP = dict(zip(equal_q.codec.str.split(" ").str[0], equal_q["bits_per_pixel (high)"]))   # e.g. {"H.264": 0.045, ...}
print("Calibrated bits-per-pixel (used in Experiment 7):", {k: round(v, 4) for k, v in CODEC_BPP.items()})
''')

code(r'''
# Visual comparison: zoom into the pipeline area of one frame
T_SHOW, CROP = 2.0, "crop=400:225:620:330"
picks = [("Original (lossless)", SRC, None)]
def pick(codec, q):
    r = e6[(e6.codec == codec) & (e6.q == q)].iloc[0]; return (f"{codec.split(' ')[0]} q={q}\n{r['bitrate_Mb/s']:.2f} Mb/s · PSNR {r.PSNR_dB:.1f} · SSIM {r.SSIM:.3f}", r.file, r)
picks += [pick("H.264 (x264 medium)", 23), pick("H.264 (x264 medium)", 38), pick("MJPEG", 16), pick("MJPEG", 4)]
low = e3[(e3["mode"] != "CRF")].iloc[0]
picks.append((f"H.264 capped {low.setting}\nPSNR {low.PSNR_dB:.1f} · SSIM {low.SSIM:.3f}", low.file, None))
fig, axs = plt.subplots(2, 3, figsize=(13, 5.6))
for ax, (title, path, _) in zip(axs.flat, picks):
    png = WORK / f"e6_crop_{Path(str(path)).stem}.png"
    run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(T_SHOW), "-i", str(path), "-frames:v", "1", "-vf", CROP, str(png)])
    ax.imshow(plt.imread(png), interpolation="nearest"); ax.set_title(title, fontsize=8.5); ax.axis("off")
plt.suptitle("Same frame, same crop — look at the pipe edges, the particles and the gradients", fontweight="bold")
plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation — the curves cross.** On this clip, AV1 needs *far fewer* bits than H.264 at the low-bitrate (tight-tether) end, and H.265 is roughly level with H.264 there and only pulls ahead at even lower bitrates; at the high-quality end x264 is as good or better than both. Published comparisons on natural camera footage usually report larger savings for H.265 and AV1; our synthetic clip (a rigid texture panning by whole pixels, plus noise) happens to suit H.264's tools well. Two lessons:

1. **"Which codec is better?" has no answer without an operating point and content.** On a tight tether you live at the left of these curves — exactly where the newer codecs gain most (if your hardware can encode them in real time).
2. **Repeat this experiment with your own footage** (`ROV_SOURCE`) before choosing. Then check that the encoder exists in hardware on your SBC and that the pilot's browser can decode it — compression efficiency is only one of four constraints.

For sizing the eight-camera system (Experiment 7) we use the conservative high-quality point.
""")

md(r"""
### 6.1 When metrics disagree with your eyes

We take one frame and apply three distortions to it — then ask PSNR and SSIM to rank them.
""")

code(r'''
from scipy.ndimage import gaussian_filter
png = WORK / "e6_ref_frame.png"
run([FFMPEG, "-y", "-loglevel", "error", "-ss", "2.0", "-i", str(SRC), "-frames:v", "1", "-vf", "format=gray", str(png)])
ref_y = (plt.imread(png)[..., 0] if plt.imread(png).ndim == 3 else plt.imread(png)) * 255.0

def psnr_np(a, b):
    mse = np.mean((a - b) ** 2); return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)

def ssim_np(a, b, sigma=1.5):
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = gaussian_filter(a, sigma), gaussian_filter(b, sigma)
    s_a = gaussian_filter(a * a, sigma) - mu_a ** 2; s_b = gaussian_filter(b * b, sigma) - mu_b ** 2
    s_ab = gaussian_filter(a * b, sigma) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + C1) * (2 * s_ab + C2)) / ((mu_a ** 2 + mu_b ** 2 + C1) * (s_a + s_b + C2))
    return float(m.mean())

rng = np.random.default_rng(0)
tests = {"Original": ref_y,
         "Brighter by 8 levels\n(harmless to a pilot)": np.clip(ref_y + 8, 0, 255),
         "Blurred (σ = 1.5 px)\n(fine detail is gone)": gaussian_filter(ref_y, 1.5),
         "Gaussian noise (σ = 6)": np.clip(ref_y + rng.normal(0, 6, ref_y.shape), 0, 255)}
fig, axs = plt.subplots(1, 4, figsize=(14, 2.9))
for ax, (name, img) in zip(axs, tests.items()):
    ax.imshow(img[300:560, 560:1020], cmap="gray", vmin=0, vmax=255)
    ax.set_title(name if name == "Original" else f"{name}\nPSNR {psnr_np(ref_y, img):.1f} dB · SSIM {ssim_np(ref_y, img):.3f}", fontsize=8.5)
    ax.axis("off")
plt.tight_layout(); plt.show()
''')

md(r"""
**Interpretation.** PSNR punishes the harmless brightness shift heavily but forgives the blur that removed real detail; SSIM gets that ranking closer to human judgement. Neither knows that, for a pilot, the blur might hide a crack, and the noise might hide nothing important. **Metrics are for comparing settings consistently; pilots decide what is acceptable.** (Activity 3 in the workshop turns this into a blind test.)
""")

code(r'''
if HAS["libvmaf"]:
    for q in (23, 38):
        f = e6[(e6.codec == "H.264 (x264 medium)") & (e6.q == q)].iloc[0].file
        r = run([FFMPEG, "-hide_banner", "-i", str(f), "-i", str(SRC), "-lavfi", "[0:v][1:v]libvmaf", "-f", "null", "-"])
        print(f"x264 CRF {q}: VMAF =", re.search(r"VMAF score: ([\d.]+)", r["stderr"]).group(1))
else:
    print("VMAF is not available in this FFmpeg build (no 'libvmaf' filter).")
    print("To try it: install an FFmpeg build with --enable-libvmaf (e.g. the static builds linked from ffmpeg.org),")
    print("then run:  ffmpeg -i distorted.mp4 -i reference.mkv -lavfi \"[0:v][1:v]libvmaf\" -f null -")
''')

md(r"""
### Exercises
1. Find the x264 CRF at which **your pilots** can no longer read a depth gauge or a number painted on a prop in a recorded clip. What is its SSIM? Now you have a *requirement* backed by a measurement.
2. Where on the rate–quality chart is MJPEG most competitive? Why could MJPEG still be the right choice for one specific camera on your ROV?
3. Compute the bitrate saving of H.265 vs H.264 at your SSIM target. Does it justify the extra encoding cost on your SBC — and can your topside **browser** decode H.265?
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 7 — The eight-camera ROV simulator

**Question.** Given N cameras, codecs and a tether, does the system fit — with headroom?

**Model.**

$$
R_{\text{camera}} \approx \text{bpp}_{\text{codec}} \times W \times H \times f \times \Big(\tfrac{P_{\text{ref}}}{W H}\Big)^{0.25},
\qquad
R_{\text{wire}} = R_{\text{camera}} \times (1 + \text{overhead}),
\qquad
U = \frac{\sum R_{\text{wire}}}{C_{\text{link}}}
$$

* $\text{bpp}_{\text{codec}}$ comes from **Experiment 6** (bits per pixel at equal, high quality on *our* clip — recalibrate with your footage). **Real camera footage usually needs more bits than our synthetic clip**: if the pilot view needs, say, 4–6 Mb/s at 1080p30 in your measurements, use that.
* The $(P_{\text{ref}}/WH)^{0.25}$ term is a **rule of thumb**: larger frames need slightly fewer bits per pixel because blocks are more predictable. It is an approximation — the experiment to verify it is in the exercises.
* **Protocol overhead.** Ethernet adds 38 bytes per frame on the wire (preamble 8, header 14, FCS 4, inter-frame gap 12), IPv4 adds 20, UDP 8, RTP 12. With a 1500-byte MTU: $1538/1460 \approx 1.053$ → **~5 %**. MPEG-TS over UDP adds its own 4-byte header per 188-byte packet → **~7 %**. TCP-based streams also generate ACK traffic in the reverse direction.
* **Headroom.** Don't plan above **~70 % sustained utilization**: I-frame bursts (Experiment 5), retransmissions, telemetry, control traffic and measurement error all need space. Planning at 95 % means you will be congested at peaks.

> **Important:** the control link (thrusters, manipulator, telemetry) usually shares the same tether. Video must never starve control. That is an *architectural* requirement, not a tuning detail.
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

md(r"""
### 7.1 Try it yourself

Change the camera mix in the panel below: the verdict updates instantly. To describe your exact vehicle, edit `my_design` in the next cell.
""")

code(r'''
def explore(n_main=1, main_res="1920×1080", main_fps=30, n_sub=7, sub_res="640×360", sub_fps=15,
            codec="H.264", link_mbps=100, transport="RTP/UDP"):
    s = simulate("custom", [(n_main, codec, main_res, main_fps), (n_sub, codec, sub_res, sub_fps)], transport)
    u = s["wire_Mb/s"] / link_mbps
    fig, ax = plt.subplots(figsize=(8, 1.6))
    ax.barh([0], [s["wire_Mb/s"]], color=STATUS[verdict(s["wire_Mb/s"], link_mbps)], height=0.5)
    ax.axvline(link_mbps * HEADROOM, ls="--", color="#52514e", lw=1); ax.axvline(link_mbps, color="#52514e", lw=1.5)
    ax.set_xlim(0, max(link_mbps, s["wire_Mb/s"]) * 1.15); ax.set_yticks([])
    ax.set_title(f"{s['wire_Mb/s']:.1f} Mb/s on the wire = {u:.0%} of {link_mbps} Mb/s → {verdict(s['wire_Mb/s'], link_mbps)}")
    plt.tight_layout(); plt.show()

try:
    import ipywidgets as wdg
    wdg.interact(explore, n_main=(0, 8), main_res=list(RES), main_fps=(5, 60, 5), n_sub=(0, 8), sub_res=list(RES),
                 sub_fps=(1, 30, 1), codec=list(CODEC_BPP), link_mbps=[100, 1000], transport=list(OVERHEAD))
except ImportError:
    print("ipywidgets not installed — using the static version below.")
explore()
''')

code(r'''
# EXERCISE: describe YOUR vehicle here (count, codec, resolution, fps) and run the cell.
my_design = [(1, "H.264", "1280×720", 30), (3, "H.264", "640×360", 15), (4, "MJPEG", "320×180", 5)]
r = simulate("my design", my_design); print(r, "→", verdict(r["wire_Mb/s"], 100), "on 100 Mb/s")
''')

md(r"""
### Exercises
1. Measure `ethtool eth0 | grep Speed` on **both ends** of your tether. Is it 100 or 1000 Mb/s? Then run `iperf3` across it (Diagnostic Checklist §3). Use the **measured** throughput as `LINK`, not the nominal one.
2. Test the $(\cdot)^{0.25}$ rule: encode the reference at 640×360 and 1920×1080 with the same CRF and compare the measured bits per pixel.
3. How many Mb/s does your **control and telemetry** traffic need? Add it to the budget.
""")

# ---------------------------------------------------------------------------
md(r"""
---
## Experiment 8 — Main streams, substreams, and priorities

**Question.** Does every camera need full quality all the time?

**Idea.** Professional multi-camera systems (CCTV recorders, broadcast, industrial ROVs) encode each camera **twice**:

* a **main stream** — high resolution and frame rate, used when the camera is on the big screen or recorded;
* a **substream** — small and cheap, used for the thumbnail grid.

The pilot looks at one or two cameras at a time. The other six only need to answer *"is something happening there?"* — which a 640×360@15 picture answers very well.

Most IP cameras can produce a main stream and a substream themselves. If your SBC encodes, it can produce both from one capture (GStreamer `tee`, or FFmpeg with two outputs) — at the cost of encoder capacity (Experiment 10).
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

md(r"""
### 8.1 Camera priorities and dynamic adjustment

A better system does not use fixed bitrates at all. It decides, every second or so, **how to spend the available budget**, guided by priorities:

1. Every *active* camera first gets its **minimum** bitrate, in priority order. If even the minimums do not fit, the lowest-priority cameras are **paused** (and the UI must show that clearly — see the UX section!).
2. Leftover budget is given to cameras in priority order, up to each camera's **maximum**.

Below, the tether capacity drops (e.g. a damaged connector forces 100 → 40 → 20 Mb/s), and the allocator protects the pilot's view.
""")

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
**Interpretation.** With fixed bitrates, a link drop congests **all** cameras at once — including the one the pilot is driving with. With priority allocation, the pilot's camera stays sharp, auxiliary cameras degrade gracefully, and some pause *visibly*. This needs (a) encoders whose bitrate can be changed at runtime (most hardware encoders and x264 via its API can; many IP cameras can via their HTTP/ONVIF API), (b) a measurement of available throughput (RTCP receiver reports, WebRTC's congestion control, or periodic probing), and (c) a UI that tells the truth about what each camera is doing.

### Exercises
1. Choose the priorities for **your** mission tasks. Does the "pilot main camera" change during the mission?
2. What should happen to a paused camera in the UI? Write an acceptance criterion for it.
3. Which component in your system would run `allocate()` — the SBC, the topside laptop, or the browser? Justify.
""")
