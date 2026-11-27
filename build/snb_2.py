"""Session notebook, part 2: Part 03 of the deck, how encoding works (slides 19–40)."""
from snb_common import md, code, part, exp

part("03", "How video encoding works", "19–40", "Open the encoder one step at a time, then turn its knobs.")

exp("21–22", "Digital video fundamentals", "Colour at half resolution: can you see it?", "4:2:0 saves half the data before any compression.", "live")
md(r"""
**Try it.** Switch between 4:4:4, 4:2:2 and 4:2:0 and compare the zoomed crops. Then tick **draw a thin red overlay before encoding**: that's the one case where colour subsampling hurts.
""")
code(r'''
FRAME_RGB = frame_png(SRC, 2.0, "chroma")[..., :3].astype(float)


def to_ycc(rgb):                                    # BT.601, full range, values 0..1
    y = rgb @ np.array([0.299, 0.587, 0.114])
    return y, (rgb[..., 2] - y) * 0.564 + 0.5, (rgb[..., 0] - y) * 0.713 + 0.5


def from_ycc(y, cb, cr):
    r = y + 1.403 * (cr - 0.5); b = y + 1.773 * (cb - 0.5); g = (y - 0.299 * r - 0.114 * b) / 0.587
    return np.clip(np.stack([r, g, b], -1), 0, 1)


def subsample(c, mode):
    """Average colour over 2×1 (4:2:2) or 2×2 (4:2:0) blocks, then stretch it back."""
    if mode == "4:4:4":
        return c
    fy, fx = (1, 2) if mode == "4:2:2" else (2, 2)
    h, w = c.shape[0] // fy * fy, c.shape[1] // fx * fx
    small = c[:h, :w].reshape(h // fy, fy, w // fx, fx).mean(axis=(1, 3))
    return np.repeat(np.repeat(small, fy, 0), fx, 1)


def chroma_view(mode, overlay, zoom):
    img = FRAME_RGB.copy()
    y0, x0 = int(0.50 * H), int(0.42 * W)
    if overlay:                                     # 1-pixel red lines, like a HUD drawn into the video
        img[y0 + 40, x0:x0 + 200] = [1, 0, 0]; img[y0:y0 + 120, x0 + 100] = [1, 0, 0]
        for k in range(100): img[y0 + 10 + k, x0 + 20 + k] = [1, 0, 0]
    y, cb, cr = to_ycc(img)
    out = from_ycc(y, subsample(cb, mode), subsample(cr, mode))
    bpp = {"4:4:4": 24, "4:2:2": 16, "4:2:0": 12}[mode]
    err = np.mean((out - img) ** 2); psnr = 99 if err == 0 else 10 * np.log10(1 / err)
    cards([("bits per pixel", f"{bpp}", f"{bpp / 24:.0%} of RGB"), ("PSNR vs original", f"{psnr:.1f} dB", "higher = closer"),
           ("data saved", f"{1 - bpp / 24:.0%}", "before any compression", True)])
    cy, cx, hh, ww = y0 + 40, x0 + 100, 130 // zoom, 220 // zoom      # centred where the red lines cross
    crop = lambda a: a[cy - hh // 2:cy + hh // 2, cx - ww // 2:cx + ww // 2]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, a, t in zip(axs, (img, out, np.clip(np.abs(out - img) * 6, 0, 1)), ("original", mode, "difference × 6")):
        ax.imshow(crop(a), interpolation="nearest"); ax.set_title(t, fontsize=10); ax.axis("off")
    plt.tight_layout(); plt.show()


panel("chroma", "Chroma subsampling", "Brightness keeps full resolution; colour is shared between pixels",
      {"mode": ("toggle", ["4:4:4", "4:2:2", "4:2:0"], "4:2:0", "scheme"),
       "zoom": ("options", [1, 2, 4], 2, "zoom"),
       "overlay": ("check", None, False, "draw a thin red overlay before encoding")}, chroma_view, live=True)
''')
md(r"""
**Look for**
- On the seabed you'll struggle to see any difference: our eyes see detail in brightness, not colour, and the water has already taken the red.
- The red lines go pink and smeared at 4:2:0. That's why overlays (depth, heading, boxes) are drawn on the pilot laptop *after* decoding.
""")

exp("23–25", "Prediction", "Find the block in the last frame", "Send a motion vector and a small correction instead of the block.", "live")
md(r"""
**Try it.** The cell cuts the frame into blocks and, for each block, searches the previous frame for the best match. With search range 0 there's no motion search at all (just "same as last frame"). Raise the range and watch the residual shrink. Then add sensor noise: the search can't remove it.
""")
code(r'''
PREV = gray(frame_png(SRC, 2.0, "mv0")); CUR = gray(frame_png(SRC, 2.0 + 1 / FPS, "mv1"))
MV_Y, MV_X, MV_H, MV_W = int(0.40 * H), int(0.30 * W), 192, 320          # the region we search in


def motion_search(prev, cur, block, reach):
    """Exhaustive block matching: for every block, the shift (dy, dx) within ±reach with the smallest error."""
    c = cur[MV_Y:MV_Y + MV_H, MV_X:MV_X + MV_W]
    nby, nbx = MV_H // block, MV_W // block
    best = np.full((nby, nbx), np.inf); vy = np.zeros((nby, nbx), int); vx = np.zeros((nby, nbx), int)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            p = prev[MV_Y + dy:MV_Y + dy + MV_H, MV_X + dx:MV_X + dx + MV_W]
            err = np.abs(c - p).reshape(nby, block, nbx, block).sum(axis=(1, 3))
            better = err < best
            best[better], vy[better], vx[better] = err[better], dy, dx
    pred = np.zeros_like(c)
    for by in range(nby):
        for bx in range(nbx):
            y, x = MV_Y + by * block + vy[by, bx], MV_X + bx * block + vx[by, bx]
            pred[by * block:(by + 1) * block, bx * block:(bx + 1) * block] = prev[y:y + block, x:x + block]
    return c, c - pred, vx, vy


def mv_view(block, reach, noise):
    rng = np.random.default_rng(0)
    prev = PREV + rng.normal(0, noise, PREV.shape); cur = CUR + rng.normal(0, noise, CUR.shape)
    c, resid, vx, vy = motion_search(prev, cur, block, reach)
    plain = np.abs(c - prev[MV_Y:MV_Y + MV_H, MV_X:MV_X + MV_W]).mean(); left = np.abs(resid).mean()
    common = pd.Series(list(zip(vx.ravel(), vy.ravel()))).value_counts().index[0]
    cards([("error without search", f"{plain:.1f}", "per pixel, 0..255"),
           ("error after search", f"{left:.1f}", f"{1 - left / plain:.0%} smaller", left < plain),
           ("most common vector", f"({common[0]}, {common[1]})", "the camera pans 3 px per frame"),
           ("blocks", f"{vx.size}", f"{block}×{block} pixels")])
    fig, axs = plt.subplots(1, 3, figsize=(14, 3.3))
    axs[0].imshow(c, cmap="gray", vmin=0, vmax=255)
    yy, xx = np.mgrid[0:vx.shape[0], 0:vx.shape[1]] * block + block / 2
    axs[0].quiver(xx, yy, vx, -vy, color=MIA_RED, angles="xy", scale_units="xy", scale=0.25, width=0.004)
    axs[0].set_title("current frame + motion vectors", fontsize=10)
    axs[1].imshow(np.abs(c - prev[MV_Y:MV_Y + MV_H, MV_X:MV_X + MV_W]), cmap="magma", vmin=0, vmax=40); axs[1].set_title("what's left without search", fontsize=10)
    axs[2].imshow(np.abs(resid), cmap="magma", vmin=0, vmax=40); axs[2].set_title("what's left after search (residual)", fontsize=10)
    for ax in axs: ax.axis("off")
    plt.tight_layout(); plt.show()


panel("mv", "Motion search", "Bright = what still has to be sent",
      {"block": ("options", [8, 16, 32], 16, "block size"),
       "reach": ("options", [0, 2, 4, 8, 12], 4, "search range (± px)"),
       "noise": ("options", [0, 2, 4, 8, 16], 0, "extra sensor noise (σ)")}, mv_view, live=True)
''')
md(r"""
**Look for**
- The vectors line up at about (3, 0): the clip pans 3 pixels per frame, and the search finds it.
- Larger search ranges find better matches but cost time. x264 presets mostly change *how hard* this search is (slide 25 and 38).
- Noise survives any search. Random detail has no match in the last frame, so it stays in the residual and costs bits (slide 23).
""")

exp(26, "Transform + quantize", "Where the bits are thrown away", "64 pixels become a few numbers; quantization is the only lossy step.", "live")
md(r"""
**Try it.** Start with the 8×8 block from slide 26. Raise the **step size**: more numbers turn to zero and the rebuilt block drifts from the original. Then try blocks from our clip.
""")
code(r'''
from scipy.fft import dctn, idctn

JPEG_Q = np.array([[16, 11, 10, 16, 24, 40, 51, 61], [12, 12, 14, 19, 26, 58, 60, 55], [14, 13, 16, 24, 40, 57, 69, 56],
                   [14, 17, 22, 29, 51, 87, 80, 62], [18, 22, 37, 56, 68, 109, 103, 77], [24, 35, 55, 64, 81, 104, 113, 92],
                   [49, 64, 78, 87, 103, 121, 120, 101], [72, 92, 95, 98, 112, 100, 103, 99]], float)
SLIDE_BLOCK = np.array([[90, 96, 102, 108, 114, 120, 166, 172], [93, 99, 105, 111, 117, 163, 169, 175],
                        [96, 102, 108, 114, 160, 166, 172, 178], [99, 105, 111, 117, 163, 169, 175, 181],
                        [102, 108, 114, 160, 166, 172, 178, 184], [105, 111, 117, 163, 169, 175, 181, 187],
                        [108, 114, 160, 166, 172, 178, 184, 190], [111, 157, 163, 169, 175, 181, 187, 193]], float)
CLIP_Y = gray(FRAME_RGB)
SPOTS = {"slide 26 (pipe edge)": None, "open water": (40, 300), "pipe edge in our clip": (int(0.58 * H) - 60, 640),
         "seabed texture": (650, 200)}


def dct_view(spot, step):
    blk = SLIDE_BLOCK if SPOTS[spot] is None else CLIP_Y[SPOTS[spot][0]:SPOTS[spot][0] + 8, SPOTS[spot][1]:SPOTS[spot][1] + 8]
    coef = dctn(blk - 128, norm="ortho")
    q = np.round(coef / (JPEG_Q * step))
    back = idctn(q * JPEG_Q * step, norm="ortho") + 128
    err = np.mean((back - blk) ** 2); psnr = 99 if err < 1e-9 else 10 * np.log10(255 ** 2 / err)
    kept = int((q != 0).sum())
    cards([("numbers kept", f"{kept} of 64", f"{64 - kept} zeros cost almost nothing"),
           ("block PSNR", f"{psnr:.1f} dB", "rebuilt vs original", psnr > 35),
           ("step size", f"× {step:g}", "of the JPEG table (+6 QP ≈ ×2)")])
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.6))
    for ax, a, t, cm in zip(axs, (blk, coef, q, back), ("1 · pixels", "2 · DCT: frequencies", "3 · quantized", "4 · rebuilt"),
                            ("gray", "RdBu_r", "RdBu_r", "gray")):
        lim = (0, 255) if cm == "gray" else (-np.abs(a).max() - 1e-9, np.abs(a).max() + 1e-9)
        ax.imshow(a, cmap=cm, vmin=lim[0], vmax=lim[1]); ax.set_title(t, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
        for (i, j), v in np.ndenumerate(a):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6.5, color="#111" if cm != "gray" or v > 110 else "#eee")
    plt.tight_layout(); plt.show()


panel("dct", "DCT and quantization", "Raise the step: more zeros, fewer bits, more error",
      {"spot": ("toggle", list(SPOTS), "slide 26 (pipe edge)", "block"),
       "step": ("options", [0.25, 0.5, 1, 2, 4, 8], 1, "step size")}, dct_view, live=True)
''')
md(r"""
**Look for**
- At step 1 the slide's block keeps 11 numbers and 53 zeros, the same as slide 26.
- Open water keeps almost nothing even at a small step: smooth areas are nearly free. Texture and edges keep many numbers.
- Each doubling of the step is about +6 QP in H.264, and roughly halves the bitrate.
""")

exp(28, "Frame types", "I, P and B frames, and the GOP", "I-frames are big and standalone; B-frames wait for the future.", "encode")
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
**Try it.** Change the keyframe interval and the number of B-frames. The bars are each frame's size, coloured by type.
""")
code(r'''
TYPE_COLOUR = {"I": MIA_RED, "P": PALETTE[0], "B": PALETTE[2]}


def types_view(gop_s, bframes, scenecut):
    g = max(1, round(gop_s * FPS))
    args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(g), "-keyint_min", str(g), "-bf", str(bframes),
            *([] if scenecut else ["-sc_threshold", "0"])]
    res = encode_cached(args, "types"); ft = frame_types(res["file"])
    kb = lambda t: ft[ft.type == t]["size"].mean() / 1e3 if (ft.type == t).any() else float("nan")
    cards([("I-frames", f"{int((ft.type == 'I').sum())}", f"one every {g / FPS:.2f} s"),
           ("average I", f"{kb('I'):.0f} kB", f"{kb('I') / kb('P'):.1f}× a P-frame"),
           ("average P", f"{kb('P'):.1f} kB", "predicted from the past"),
           ("average B", "none" if bframes == 0 else f"{kb('B'):.1f} kB", "waits for a future frame" if bframes else "no waiting"),
           ("bitrate", rate(res["bitrate"]), f"SSIM {res['ssim']:.3f}")])
    show = ft.iloc[:120]
    plt.figure(figsize=(12, 3.2))
    plt.bar(show.index, show["size"] / 1e3, color=[TYPE_COLOUR.get(t, GREY) for t in show.type], width=0.85)
    plt.xlabel("frame (decode order)"); plt.ylabel("kB"); plt.title("red = I · blue = P · green = B"); plt.tight_layout(); plt.show()


panel("types", "Frame types", "Keyframe interval and B-frames",
      {"gop_s": ("options", [0.25, 0.5, 1.0, 2.0, 4.0], 1.0, "keyframe every (s)"),
       "bframes": ("int", (0, 3, 1), 0, "B-frames"),
       "scenecut": ("check", None, False, "extra I-frame on a scene cut")}, types_view)
''')
md(r"""
**Look for**
- An I-frame is several times a P-frame (about 4× on the slide). Those spikes are what the tether must absorb every GOP.
- B-frames make the file smaller, but each one makes the encoder wait for a future frame. Live streams use 0.
- With scene-cut detection on, x264 adds an I-frame at the camera cut (frame ~120).
""")

exp(29, "Experiments 3 and 6", "Quality target or bitrate cap?", "CRF for recording, a capped bitrate for the live tether.", "encode")
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
Now the part that matters on a tether: what the bitrate does **over time**. Both encodes below have the same average.
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
code(r'''
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

panel("e3", "Rate control", "Quality target or bitrate cap: watch the peaks and the detail",
             {"mode": ("toggle", ["CRF (quality)", "Target bitrate (VBV)"], "CRF (quality)", ""),
              "crf": ("int", (12, 45, 1), 23, "CRF"),
              "target": ("options", [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0], 1.0, "bitrate cap (Mb/s)"),
              "buffer_s": ("options", [0.1, 0.25, 0.5, 1.0, 2.0], 0.5, "VBV buffer (s)")}, tune_rate)
''')
md(r"""
**Look for**
- CRF's peaks: the slide's run averaged 1.5 Mb/s but peaked at 2.6 Mb/s in 200 ms windows. A sediment cloud does the same thing exactly when the pilot needs the picture.
- The capped encode holds its ceiling and lets quality dip on hard frames instead. Shrink the VBV buffer: smoother bitrate, lower latency, worse hard frames.
""")

exp(30, "Why streamers obsess over bits", "What is 1 % of Netflix's bitrate worth?", "A Fermi estimate: change any factor you don't believe.", "live")
code(r'''
def netflix_view(hours_bn, gb_per_hour, usd_per_gb, saving_pct):
    eb = hours_bn * 1e9 * gb_per_hour / 1e9            # exabytes a year
    cost = hours_bn * 1e9 * gb_per_hour * usd_per_gb
    cards([("delivered", f"{eb:,.0f} EB / year", f"{hours_bn} billion hours × {gb_per_hour} GB"),
           ("delivery cost", f"${cost / 1e9:,.1f} B / year", f"at ${usd_per_gb}/GB (assumed)"),
           (f"{saving_pct} % fewer bits", f"${cost * saving_pct / 100 / 1e6:,.0f} M / year", "saved", True),
           ("our ROV", "1 viewer", "encoded once, watched once, live")])


panel("netflix", "Netflix, roughly", "191 B hours (2025) × GB per hour × cost per GB",
      {"hours_bn": ("int", (50, 300, 1), 191, "billion hours / year"),
       "gb_per_hour": ("options", [0.5, 1, 2, 3, 5, 7], 2, "GB per hour"),
       "usd_per_gb": ("options", [0.002, 0.005, 0.01, 0.02, 0.03, 0.05], 0.005, "$ per GB"),
       "saving_pct": ("int", (1, 20, 1), 1, "bitrate saved (%)")}, netflix_view, live=True)
''')
md(r"""
**Look for**
- With the slide's ranges, 1 % is worth roughly \$19–115 M a year. That's why Netflix spends huge CPU per encode: it's encoded once and watched millions of times.
- Our stream is encoded once and watched once, live. We do the opposite: spend bits to save latency and CPU.
""")

exp(32, "Choosing a codec", "The fair comparison: whole rate–quality curves", "Which codec is best depends on where you sit on the curve.", "run")
md(r"""
This cell encodes the clip at five quality levels per codec. It's the slowest cell in the notebook (a few minutes on a laptop); the results are cached. We use `-tune ssim` (metric-neutral tuning) so the encoders aren't optimising for how things look to people while we score them with SSIM.
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
print("Calibrated bits-per-pixel (used on slide 50):", {k: round(v, 4) for k, v in CODEC_BPP.items()})
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
**Try it.** Pick a quality target. The bars show the bitrate each codec needs to reach it, read off the curves above.
""")
code(r'''
SSIM_OPTIONS = sorted({round(x, 3) for x in np.linspace(e6.groupby("codec")["SSIM"].min().max() + 0.002,
                                                         e6.groupby("codec")["SSIM"].max().min() - 0.002, 8)})


def equal_view(target):
    rows = [(c, bitrate_at(g, "SSIM", target)) for c, g in e6.groupby("codec", sort=False)]
    ref = dict(rows).get("H.264 (x264 medium)", np.nan)
    cards([(c.split(" ")[0], rate(b) if b == b else "out of range", f"{b / ref:.2f}× H.264" if b == b and ref == ref else "")
           for c, b in rows])
    plt.figure(figsize=(8, 2.8))
    plt.barh([c for c, _ in rows], [b for _, b in rows], color=[MIA_RED, *PALETTE][:len(rows)], height=0.55)
    plt.gca().invert_yaxis(); plt.xlabel("Mb/s needed"); plt.title(f"Bitrate for SSIM {target}"); plt.tight_layout(); plt.show()


panel("equal", "Equal quality", "Same SSIM, different codecs",
      {"target": ("options", SSIM_OPTIONS, SSIM_OPTIONS[len(SSIM_OPTIONS) // 2], "SSIM target")}, equal_view, live=True)
''')
md(r"""
**Look for**
- The curves cross. At low quality AV1 needs far fewer bits than H.264; at high quality x264 holds up well on this clip.
- MJPEG needs several times more than everything else at any quality.
- On the ROV the deciding question is often not size but who can encode it in real time: the Pi 5 has no H.264 hardware encoder, the Jetson Nano does (slide 43).
""")

exp(33, "Codec ≠ container", "Pull the power during a recording", "Plain MP4 writes its index at the end; a power cut leaves nothing playable.", "encode")
md(r"""
**Try it.** The cell records the clip in real time into four containers and kills FFmpeg with `SIGKILL` after the time you choose, like a power cut. Then it checks what can still be played. (Ctrl-C would *not* be a fair test: it lets FFmpeg close the file cleanly.)
""")
code(r'''
import signal

CONTAINERS = {"MP4": ("mp4", []),
              "Fragmented MP4": ("mp4", ["-movflags", "+frag_keyframe+empty_moov+default_base_moof"]),
              "Matroska (MKV)": ("mkv", []),
              "MPEG-TS": ("ts", [])}


def power_cut_view(cut_after):
    rows = []
    for name, (ext, flags) in CONTAINERS.items():
        out = WORK / f"cut_{name.split()[0].lower()}.{ext}"
        out.unlink(missing_ok=True)
        p = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-re", *SRC_IN, "-c:v", "libx264", "-preset", "ultrafast",
                              "-g", "30", "-pix_fmt", "yuv420p", *flags, str(out)])
        time.sleep(cut_after); p.send_signal(signal.SIGKILL); p.wait()
        r = run([FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
                 "-of", "csv=p=0", str(out)], check=False)
        frames = int(r["stdout"].strip()) if r["rc"] == 0 and r["stdout"].strip().isdigit() else 0
        rows.append({"container": name, "file size": f"{out.stat().st_size / 1e3:.0f} kB" if out.exists() else "none",
                     "plays?": "yes" if frames else "NO", "seconds you get back": round(frames / FPS, 1)})
    cards([(r["container"], r["plays?"], f"{r['seconds you get back']} s of {cut_after} s", r["plays?"] == "yes") for r in rows])
    display(pd.DataFrame(rows).style.hide(axis="index"))


panel("cut", "Power cut", "Real time recording, killed without warning",
      {"cut_after": ("options", [1.0, 2.0, 3.0, 4.0], 2.0, "cut the power after (s)")}, power_cut_view)
''')
md(r"""
**Look for**
- The plain MP4 has data in it but doesn't play: its index (the `moov` atom) was never written. "moov atom not found" is the error you'd see.
- Fragmented MP4, MKV and MPEG-TS play up to about the last second. Record in one of those during the dive, then remux to MP4 if you need it: `ffmpeg -i dive.mkv -c copy dive.mp4` (seconds, no quality loss). Experiment E15 does this on the ROV.
""")

exp("34–35", "MJPEG on the ROV", "The resolution trap", "Shrinking MJPEG is free if the camera does it, and expensive if we do.", "encode")
md(r"""
We pretend `work/camera_720p.mkv` is what a USB camera sends in its 720p MJPEG mode. **Try it:** pick the size the pilot needs, then compare three ways to get it:

1. **Ask the camera** for that size and just copy it (`-c:v copy`).
2. **Resize on the ROV**: decode the 720p JPEGs, scale, encode JPEG again (what an OpenCV resize or the Python `mjpeg-streamer` does).
3. **Resize once, but encode H.264** instead of a smaller MJPEG.
""")
code(r'''
CAMERA = WORK / "camera_720p.mkv"
if not CAMERA.exists():
    run([FFMPEG, "-y", "-loglevel", "error", *SRC_IN, "-c:v", "mjpeg", "-q:v", "3", "-pix_fmt", "yuvj420p", str(CAMERA)])
TRAP_SIZES = {"1280×720": (1280, 720), "640×360": (640, 360), "320×180": (320, 180)}


def core_pct(r):
    """Share of one CPU core needed to keep up at 30 fps."""
    return r["cpu_s"] / N_FRAMES * FPS * 100


def trap_view(size, mjpeg_q):
    w, h = TRAP_SIZES[size]
    native = WORK / f"camera_{w}x{h}.mkv"        # what the camera would send if we asked it for this size
    if not native.exists():
        run([FFMPEG, "-y", "-loglevel", "error", *SRC_IN, "-vf", f"scale={w}:{h}", "-c:v", "mjpeg", "-q:v", "3",
             "-pix_fmt", "yuvj420p", str(native)])
    a = run([FFMPEG, "-y", "-loglevel", "error", "-i", str(native), "-c:v", "copy", str(WORK / "trap_copy.mkv")])
    b_out, c_out = WORK / f"trap_mjpeg_{w}_{mjpeg_q}.mkv", WORK / f"trap_h264_{w}.mp4"
    b = run([FFMPEG, "-y", "-loglevel", "error", "-i", str(CAMERA), "-vf", f"scale={w}:{h}", "-c:v", "mjpeg",
             "-q:v", str(mjpeg_q), "-pix_fmt", "yuvj420p", str(b_out)])
    c = run([FFMPEG, "-y", "-loglevel", "error", "-i", str(CAMERA), "-vf", f"scale={w}:{h}", "-c:v", "libx264",
             "-preset", "veryfast", "-tune", "zerolatency", "-crf", "23", "-pix_fmt", "yuv420p", str(c_out)])
    paths = {"1 · camera makes it, copy": (a, native), "2 · decode → scale → JPEG": (b, b_out), "3 · decode → scale → H.264": (c, c_out)}
    rows = {k: (core_pct(r), probe(p)["bitrate_mbps"]) for k, (r, p) in paths.items()}
    cards([(k.split(" · ")[1], f"{cpu:.1f} % of a core", rate(mb), cpu < 5) for k, (cpu, mb) in rows.items()])
    fig, axs = plt.subplots(1, 2, figsize=(12, 2.8))
    names = list(rows)
    axs[0].barh(names, [v[0] for v in rows.values()], color=[GOOD, BAD, PALETTE[0]]); axs[0].set_xlabel("% of one core at 30 fps")
    axs[1].barh(names, [v[1] for v in rows.values()], color=[GOOD, BAD, PALETTE[0]]); axs[1].set_xlabel("Mb/s on the tether")
    for ax in axs: ax.invert_yaxis()
    axs[1].set_yticks([]); plt.tight_layout(); plt.show()


panel("trap", "The resolution trap", "Where you shrink the picture decides what it costs",
      {"size": ("toggle", list(TRAP_SIZES), "640×360", "size the pilot needs"),
       "mjpeg_q": ("int", (2, 15, 1), 5, "JPEG quality for path 2 (q:v)")}, trap_view)
''')
md(r"""
**Look for**
- Path 1 costs about 1 % of a core: nothing is decoded or encoded. Check which sizes your camera makes itself: `v4l2-ctl -d /dev/video0 --list-formats-ext`.
- Path 2 costs many times more, per camera, and the Python library repeats the encode for every viewer.
- If the camera can't make the size you need, path 3 is the better transcode: one H.264 encode, several times fewer bits than a smaller MJPEG.
""")

exp(38, "Experiment 4", "Encoder presets: CPU against bits", "Slower presets search harder; after veryfast the savings get small.", "encode")
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
code(r'''
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
    ax.plot(e4["cpu_ms_per_frame"], e4["bitrate_Mb/s"], "o-", color="#b5b5b5", label="all presets (above)")
    ax.plot([ms], [res["bitrate"]], "o", ms=13, color=PALETTE[1], label=f"your setting: {preset}{' + zerolatency' if zerolatency else ''}")
    ax.set_xscale("log"); ax.set_xlabel("CPU time per frame (ms, log)"); ax.set_ylabel("bitrate at CRF 23 (Mb/s)")
    ax.set_title("Where your setting sits on the speed–efficiency curve"); ax.legend(fontsize=8); plt.tight_layout(); plt.show()

panel("e4", "Encoder speed", "Same CRF, different preset: CPU cost versus bits",
             {"preset": ("options", PRESETS, "veryfast", "preset"),
              "zerolatency": ("check", None, False, "-tune zerolatency (no B-frames, no lookahead)")}, tune_preset)
''')
md(r"""
**Look for**
- CPU time per frame is the number that transfers between machines: measure it on the SBC, multiply by fps and streams, compare with the free cores.
- `zerolatency` changes more than speed: it removes look-ahead and B-frames, which is up to a second of delay (slide 49).
""")

exp(39, "Experiment 5", "Packet loss and the keyframe interval", "Damage lasts until the next I-frame; intra refresh heals without the spike.", "encode")
md(r"""
We delete a few kB from an MPEG-TS stream (as a lost burst of UDP packets would), decode it, and measure how long the picture stays broken. First at three loss positions for three settings, then in a panel where you choose.
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
code(r'''
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

panel("e5", "Keyframes and packet loss", "Shorter GOP or intra refresh: how fast does the picture heal?",
             {"gop_s": ("options", [0.25, 0.5, 1.0, 2.0, 3.0, 5.0], 1.0, "keyframe every (s)"),
              "loss_kb": ("int", (1, 40, 1), 8, "data lost (kB)"),
              "loss_at": ("float", (0.5, 4.5, 0.1), 1.4, "loss at (s)"),
              "intra_refresh": ("check", None, False, "intra refresh instead of I-frames")}, tune_gop)
''')
md(r"""
**Look for**
- GOP 150 can stay broken for seconds; GOP 30 and intra refresh recover in well under a second. Slide 39: 0.6 s vs 2.2 s on average, 3.6 s worst.
- Intra refresh has no I-frame spikes: the biggest frame is much smaller.
- "Camera switching takes two seconds" is often a two-second GOP: a new viewer waits for the next I-frame.
""")

exp(40, "Experiment 6", "PSNR, SSIM, and your own eyes", "Metrics compare settings. Pilots decide what's good enough.", "live")
md(r"""
**Try it.** Damage the frame in different ways and compare what the two metrics say with what you see. A small brightness shift is harmless to a pilot; a blur that wipes out the detail is not.
""")
code(r'''
from scipy.ndimage import gaussian_filter

REF_Y = CLIP_Y.copy()


def psnr_np(a, b):
    mse = np.mean((a - b) ** 2); return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def ssim_np(a, b, sigma=1.5):
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = gaussian_filter(a, sigma), gaussian_filter(b, sigma)
    s_a = gaussian_filter(a * a, sigma) - mu_a ** 2; s_b = gaussian_filter(b * b, sigma) - mu_b ** 2
    s_ab = gaussian_filter(a * b, sigma) - mu_a * mu_b
    return float((((2 * mu_a * mu_b + c1) * (2 * s_ab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (s_a + s_b + c2))).mean())


def metric_view(brightness, blur, noise, blocks):
    img = REF_Y.copy()
    if blocks > 1:
        h, w = img.shape[0] // blocks * blocks, img.shape[1] // blocks * blocks
        small = img[:h, :w].reshape(h // blocks, blocks, w // blocks, blocks).mean(axis=(1, 3))
        img[:h, :w] = np.repeat(np.repeat(small, blocks, 0), blocks, 1)
    if blur:
        img = gaussian_filter(img, blur)
    if noise:
        img = img + np.random.default_rng(0).normal(0, noise, img.shape)
    img = np.clip(img + brightness, 0, 255)
    cards([("PSNR", f"{psnr_np(REF_Y, img):.1f} dB", "pixel by pixel"), ("SSIM", f"{ssim_np(REF_Y, img):.3f}", "local structure"),
           ("your eyes", "?", "does the detail survive?")])
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.4))
    for ax, a, t in zip(axs, (REF_Y, img), ("original", "damaged")):
        ax.imshow(a[300:560, 560:1020], cmap="gray", vmin=0, vmax=255); ax.set_title(t, fontsize=10); ax.axis("off")
    plt.tight_layout(); plt.show()


panel("metric", "Fool the metrics", "Brightness, blur, noise and blocks",
      {"brightness": ("int", (-30, 30, 2), 8, "brightness shift"), "blur": ("options", [0, 0.5, 1.0, 1.5, 2.5], 0, "blur (σ px)"),
       "noise": ("options", [0, 3, 6, 12], 0, "noise (σ)"), "blocks": ("options", [1, 4, 8, 16], 1, "blockiness (px)")}, metric_view, live=True)
''')
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
**Look for**
- A brightness shift of 8 drops PSNR a lot while SSIM hardly moves. A blur of 1.5 px does the opposite damage to the detail.
- VMAF is the best match to viewers for TV and film, but nobody trained it on ROV tasks. For us the final test is the pilot (experiments E24 and E25).
""")

exp(40, "Activity 3", "The blind test", "Rank five clips by quality, guess the bitrates, then reveal.", "encode")
md(r"""
**Try it.** Press **Encode**: you get five crops of the same frame at five hidden bitrates, labelled A to E in random order. Rank them and guess each bitrate. Then tick **reveal** and press Encode again (it's cached, so it's instant). Change the round number for a new set.
""")
code(r'''
def blind_view(round_no, reveal):
    rng = np.random.default_rng(round_no)
    crfs = sorted(rng.choice(np.arange(18, 47, 2), 5, replace=False).tolist())
    clips = [(crf, encode_cached(["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf)], "blind")) for crf in crfs]
    order = rng.permutation(5)
    y0, x0 = int(0.48 * H), int(0.40 * W)
    fig, axs = plt.subplots(1, 5, figsize=(16, 3))
    for ax, letter, k in zip(axs, "ABCDE", order):
        ax.imshow(frame_png(clips[k][1]["file"], 2.0, f"blind_{letter}")[y0:y0 + 180, x0:x0 + 320]); ax.set_title(letter, fontsize=14, fontweight="bold"); ax.axis("off")
    plt.tight_layout(); plt.show()
    if reveal:
        rows = [{"clip": letter, "CRF": clips[k][0], "bitrate": rate(clips[k][1]["bitrate"]),
                 "PSNR (dB)": round(clips[k][1]["psnr"], 1), "SSIM": round(clips[k][1]["ssim"], 3)} for letter, k in zip("ABCDE", order)]
        display(pd.DataFrame(rows).sort_values("SSIM", ascending=False).style.hide(axis="index"))
    else:
        note("Rank A–E from best to worst and write a bitrate guess under each. Then tick reveal.")


panel("blind", "Blind test", "Five hidden bitrates, one frame",
      {"round_no": ("int", (1, 20, 1), 1, "round"), "reveal": ("check", None, False, "reveal the answers")}, blind_view)
''')
