# Presenter Script — *Engineering Better ROV Systems*

**For:** the presenter (you).  **Deck:** `presentation/MIA_Robotics_Workshop.pptx` (82 slides, speaker notes on every slide).
**Companion files:** `Workshop_Design.md` (agenda, objectives, unknowns), the **ROV Encoding Lab** (`../encoding_lab/`, run `streamlit run app.py`), `student_materials/`, `workshop_activities/`, `ux_materials/`, and the presenter-only `referee/` folder (kept in the presenter's Drive, not in the team repo).

How to use this script:
- Each block has **Objective · Duration · Slides**, then **How to open**, **What to explain**, **Emphasise**, **Real-world examples**, **Ask the room** (with expected answers), **Misconceptions**, and **Transition**.
- Lines in *“quotes”* are phrasings you can use as-is. Adapt them, don't recite them.
- ⏱ marks a natural place to check time. 🧪 marks a live Encoding Lab demo. 🎯 marks an activity.
- The numbers quoted were measured on a 2-core laptop with the synthetic clip. **Re-measure them in the Encoding Lab the night before** (and on the team's own footage if you get it: sidebar → Upload your own video) and update any number that differs.

### The session runs on the Encoding Lab, not the notebook

Every demo is done live in the **ROV Encoding Lab**. Where this script names a notebook experiment, use the matching Lab tab:

| Notebook experiment | Encoding Lab |
|---|---|
| 1 · Raw bandwidth | sidebar (raw 4:2:0 Mb/s) + Encode → 🧮 Show the math |
| 2 · Codecs and the FFmpeg command | Encode: codec selector; Compare section at the bottom |
| 3 · CRF vs bitrate cap | Encode: Rate control + Bitrate over time; Sweep → Quality / Target bitrate |
| 4 · Encoder parameters | Sweep → Preset, Keyframe interval, Resolution, Frame rate |
| 5 · Packet loss and GOP | Bandwidth budget → Packet-loss lab (and the *Broken picture* card in Plan the budget) |
| 6 · Quality metrics | Encode → Frame compare (Diff ×8, Zoom), Quality over time (VMAF under More) |
| 7 · Bandwidth planning | Bandwidth budget → Plan the budget (start from *What we fly now*, then switch the tether to powerline) |
| 8 · Substreams and priorities | Bandwidth budget (edit the camera table, read *Cheapest ways to make it fit*) + Live camera → Output size |
| 9 · Latency | Encode → latency graph; Live camera (x264 with Low latency off, then on); Bandwidth budget → Measure this computer → Compare defaults vs low latency |
| 10 · What this machine can do | Bandwidth budget → Measure this computer (then pick *This computer (benchmarked)* in Plan the budget) |
| 11 · Take it to the ROV | Report + `docs/streaming/jetson-nano-vs-pi5.md` |
| *(new)* MJPEG passthrough vs resize, NVENC | Live camera |

---

## Before the session — checklist

- [ ] Send the **questionnaire** (Workshop_Design.md §6.5) to the team lead a week before. Even partial answers change the conversation.
- [ ] Start the Encoding Lab on the presenter laptop (`streamlit run encoding_lab/app.py`). Run one encode in Encode, run Bandwidth budget → Measure this computer once, and press **Start** once in Live camera with the laptop camera (Windows and macOS ask for camera permission the first time). Keep it open on the Encode tab.
- [ ] Open the deck in **Presenter View** (speaker notes visible).
- [ ] Click through the deck once. Every content slide **builds on click** (title and kicker stay; each card, chart or recipe fades in on the next click, at most 8 clicks per slide). The presenter view shows the next step. To change the grouping, edit `build/add_click_builds.py` and rebuild (`node build/build_deck.js`).
- [ ] Print: Activity 1 cards, Activity 2 answer sheets, the Testing Competition Guide, the UX scenario and A3 sheets, the Diagnostic Checklist (one per subsystem owner), the Cheat Sheet (one per student).
- [ ] Copy `workshop_activities/testing_competition_code/` to every team laptop; check `python -m pytest -q` passes (7 tests).
- [ ] Prepare Activity 3 clips: copy the five encodes listed in `Activity_Instructions.md` (Activity 3) by encoding them in the Encoding Lab's Encode tab (they are saved under `encoding_lab/.lab_work/`), rename them A–E, keep the answer key.
- [ ] If possible: bring the real ROV, tether, and the topside laptop. Ask for SSH access to the SBC.
- [ ] Replace the title slide image with a photo of **their** ROV if you have one.

---

# SESSION 1 — VIDEO ENGINEERING (≈ 3 h 50 min incl. two 10-min breaks)

## 1.1 Opening — why this session exists

**Objective:** Establish credibility, set the mindset ("measure first"), and connect the day to points in the MATE competition.
**Duration:** 10 min · **Slides:** 1–6

**How to open (slide 1).** Don't start with your CV. Start with their pain:

> *“Hands up if you've ever driven the ROV and the video lagged, froze, or turned to mush at exactly the wrong moment.”*

Wait. Most hands go up. Then:

> *“Today is about turning those moments into numbers — and the numbers into decisions.”*

**Slide 2 — bench-ready to mission-ready.** Introduce yourself in two sentences: you build professional video systems (capture, encoding, decoding, rendering, network streaming) for oil & gas, where ROV video is literally how people see subsea assets. Then the three promises: *measure, engineer, collaborate*. Read the mindset line slowly — it comes back at the end:

> *“How would we measure that?” comes before “How do we fix that?”*

**Slide 3 — MATE.** The MATE ROV Competition (MATE Center + Marine Technology Society) scores the product demonstration (pool missions) **and** technical documentation, an engineering presentation and a marketing display. Check the current season's manual for exact weights — they change.

> *“Judges in the engineering presentation ask ‘why did you choose this?’. Today you'll leave with answers backed by measurements. That is worth points.”*

**Slide 4 — agenda.** 30 seconds. Point out there is an activity every 20–30 minutes.

**Slide 5 — video is the primary sensor.** Professional work-class ROVs carry several cameras with **different jobs**: pilot/navigation (wide, lowest latency), manipulator (close-up, depth cues, latency-critical), inspection/zoom (detail, often recorded, latency less critical), rear/tether (occasional glances). Different jobs → different requirements → this is the seed of main streams vs substreams later.

Situational awareness (Mica Endsley's model): **perceive → comprehend → project**. Video feeds all three.

**Ask the room:** *“If you lose depth telemetry mid-mission, can you still finish a task? If you lose the main camera?”*
Expected: depth — maybe, by eye; main camera — no. → Video is the most critical sensor, yet it's usually the least engineered subsystem.

**Misconception:** “Video is just a webcam plugged in.” → It is a real-time distributed system: sensor, encoder, network, decoder, display — each with failure modes.

**Transition:** *“Before we optimise anything, let's understand the environment we're fighting — and the system we're optimising.”*

---

## 1.2 Underwater video & your architecture

**Objective:** Explain why underwater video is hard; separate known facts from assumptions about their system; introduce the three encoding architectures and the vocabulary codec/container/protocol.
**Duration:** 30 min · **Slides:** 7–14

**Slide 6 — the world runs on compression.** *(new, Nov 2026)* 1–2 minutes. Video is about 65 % of all internet traffic (Sandvine, 2022 data). Every codec generation needs roughly half the bits of the one before for the same quality: H.264 (2003) → HEVC (2013) → VVC (2020). The H.264 team received two engineering Emmys (2008, 2009). Message: nobody notices compression until it fails, and our ROV is a small version of the same problem.

**Slide 8 — physics.** Water absorbs red light first (within a few metres), then orange/yellow → blue-green cast, low contrast. Suspended particles cause **turbidity**; the ROV's own lights reflect off particles between camera and target (**backscatter**, “marine snow”). Low light → camera raises gain → **noise** that changes every frame.

Connect to compression immediately:

> *“An encoder works by predicting the next frame from the previous one. What's unpredictable? Noise. Particles. Rippling light. Every unpredictable pixel costs bits. Underwater video is expensive to compress — and that's before we talk about the tether.”*

Point at the image: it's the Encoding Lab's synthetic clip, which was built to have these properties.

**Slide 9 — student vs industrial.** Be respectful: they build in months, as volunteers. The point is which industrial practices are **cheap to adopt**: measuring, configuring encoders deliberately, budgeting bandwidth, specifying latency, testing failures, designing with pilots. Industrial ROVs often use fibre-optic tethers with multiplexers — but they *still* budget, prioritise and test. The difference is as much discipline as money.

**Slide 10 — what we know.** This slide models the behaviour you want: label facts, unknowns and hypotheses.

The key unknown — say it explicitly:

> *“My brief says ‘USB cameras connected through network hubs/switches’ and also ‘IP cameras into a switch’. Those are two different systems. Which is it?”*

| If USB cameras | If IP cameras |
|---|---|
| Cameras connect to the SBC's USB ports, usually via a USB hub | Cameras connect to an Ethernet switch |
| Camera sends raw YUYV, MJPEG, or (some models) H.264 | Camera almost always encodes H.264/H.265 itself |
| Shared bottleneck: the **USB bus** | Shared bottleneck: switch uplink and **tether** |
| Identify with `lsusb -t`, `v4l2-ctl --list-devices` | Identify with the camera's web page, `ffprobe rtsp://…` |

Second unknown: **Jetson Nano vs Jetson Orin Nano** — they are often confused, and only the original Nano has a hardware video encoder (details on slide 37).

**Slide 11 — three architectures.** Draw them on the whiteboard too.
- **A — camera encodes:** IP cameras send H.264/H.265; switch forwards; SBC is optional (relay/control). No SBC encode load; you depend on the camera's encoder settings.
- **B — SBC encodes:** USB cameras send raw/MJPEG to the SBC; the SBC's encoder (hardware on Jetson Nano, CPU on Pi 5) is the bottleneck. If cameras send MJPEG, the SBC must **decode it first**, then encode — double work.
- **C — SBC forwards/transcodes:** cameras already encode; the SBC remuxes (cheap), relays, or **transcodes** (expensive: full decode + encode per stream), e.g. to feed a browser via WebRTC.

**Ask:** *“Which one are we? How would you prove it in five minutes?”*
Expected: `ffprobe` the stream (codec field), `lsusb`, `v4l2-ctl --list-formats-ext`, look at the process list on the SBC (`ps aux | grep -E "ffmpeg|gst|mjpg"`), check camera web UI.

**Slide 12 — USB vs IP cameras.** *(new, Nov 2026)* Both can deliver eight cameras; what changes is where the encoding and the bandwidth limit live. USB 2.0 = 480 Mb/s shared per bus, 5 m passive cables, isochronous reservations that make hubs fail. IP = each camera encodes, own Ethernet port, 100 m cables, PoE 15.4 W per port; this is why network video recorders can take dozens of cameras. Ask: *“Which cameras do we have today, and which ones encode H.264 themselves?”* Answer with `v4l2-ctl --list-formats-ext`.

**Slide 13 — following a frame.** Walk left to right: capture → encode → packetize → network → buffer → decode → render. At each box ask *“where does this run on our ROV?”*. Three points:
1. Encoding happens wherever the encoder is (camera or SBC).
2. The cable is rarely the main delay — **buffers** are (encoder lookahead, receiver buffer).
3. Decoding happens on the topside laptop. Eight streams means eight decoders — a weak laptop browser can be the bottleneck.

**Slide 14 — codec ≠ container ≠ protocol.** Parcel analogy:
- **Codec** = how you folded the clothes to make them small (H.264, H.265, MJPEG, AV1).
- **Container / payload format** = the labelled box with timing information (MP4, MKV, MPEG-TS, the RTP payload format for H.264 defined in RFC 6184).
- **Streaming/control protocol** = the delivery service (RTSP sets up sessions; RTP carries media; WebRTC; HLS; HTTP-MJPEG; SRT).
- **Transport** = the road (UDP or TCP). **Network/link** = the ground (IP, Ethernet, the tether).

**Misconceptions to correct:**
- “We stream MP4.” → MP4 is a file container; live streams are usually RTP, MPEG-TS, fragmented MP4 or WebRTC.
- “RTSP is our codec.” → RTSP is a control protocol; the video inside is typically H.264 over RTP.
- “MJPEG is a protocol.” → MJPEG is a codec (sequence of JPEGs); “MJPEG over HTTP” is how it's often delivered.

**Transition:** *“Now let's count bits. This is the single most useful quantitative skill of the day.”*

---

## 1.3 Bandwidth engineering

**Objective:** Students can compute raw and compressed bandwidth, apply overhead and headroom, and distinguish bitrate/bandwidth/throughput.
**Duration:** 30 min (incl. 🎯 Activity 1, 15 min) · **Slides:** 15–21

**Slide 16 — the formula.** Write it on the board:

R_raw = W × H × bpp × f

Do 1080p30 RGB together, out loud:
- 1920 × 1080 = 2,073,600 pixels
- × 24 bits = 49.8 Mbit per frame
- × 30 frames/s = **1.49 Gbit/s**

> *“One camera. Uncompressed. Bigger than gigabit Ethernet. Eight of them: 11.9 Gbit/s.”*

Explain bpp per pixel format: RGB24 = 24; **YUYV 4:2:2** = 16 (what USB webcams send raw); **NV12 / YUV420P 4:2:0** = 12. (4:2:0 explained properly on slide 24.)

Units: networks use decimal — 1 Mb/s = 10⁶ bit/s. Storage often uses MiB (2²⁰ bytes). Write **Mb/s** (bits) vs **MB** (bytes) carefully: factor 8.

**Slide 17 — raw chart.** Log scale. Key lines:
- 100 Mb/s — Fast Ethernet (long or thin tethers often negotiate only this; check with `ethtool`).
- ≈ 197 Mb/s — the maximum a single USB 2.0 UVC camera can use with high-bandwidth isochronous transfer (3 × 1024 bytes per 125 µs micro-frame).
- 480 Mb/s — USB 2.0 signalling rate, **shared by every device on that bus**; periodic (isochronous) traffic is limited to 80 % of each micro-frame.
- 1000 Mb/s — Gigabit Ethernet.

> *“Raw YUYV only fits USB 2.0 at about 640×480@30. That's why your webcams switch to MJPEG at 720p — the camera compresses because USB forces it to. Many teams stream MJPEG without ever deciding to.”*

**Real-world example:** With 3–4 UVC cameras on one USB 2.0 hub, the next camera fails to start (`VIDIOC_STREAMON: No space left on device`). The bus isn't full of data — each camera **reserved** isochronous bandwidth. Fixes: spread cameras over different USB controllers/root ports (`lsusb -t` shows the tree), use MJPEG/H.264 modes with smaller packet sizes, or use IP cameras.

**Slide 18 — the Egyptian-pound version.** *(new, Nov 2026)* WE's entry home package is 100 GB for EGP 150 + 14 % VAT from 1 November 2026, about EGP 1.71/GB. One hour of raw 1080p30 RGB = 672 GB ≈ EGP 1,150 (the month's 100 GB lasts 9 minutes); the same hour as H.264 at 5 Mb/s = 2.25 GB ≈ EGP 3.85. Re-check prices at te.eg before presenting. Demo: `python demos/01_why_streaming/egypt_cost.py`.

**🎯 Slide 19 — Activity 1 (15 min).** See `workshop_activities/Activity_Instructions.md` for cards and the answer key. Teams of 3–5; each team gets one card; they compute raw, compressed, on-the-wire, utilisation vs 70 %, verdict, and one confirming measurement. Score: arithmetic 4, verdict 3, measurement 3. Reveal with notebook Experiment 7.

**Slide 20 — compression is the core.** Measured on the 1280×720 clip: raw 4:2:0 = 332 Mb/s; MJPEG ≈ 8.2 Mb/s (≈ 40:1); H.264 CRF 23 ≈ 1.5 Mb/s (≈ 221:1).

> *“Halving width and height divides pixels by four — and throws away detail the pilot may need. Moving from MJPEG to H.264 at similar quality saved about 8× in our measurement — with no loss of resolution.”*

Caveat out loud: compression ratios depend heavily on content. Their real footage will compress differently — that's why the Encoding Lab can run on their own clip (sidebar → Upload your own video).

**Slide 21 — words that get mixed up.**
- **Bitrate**: what the encoder produces (e.g. 4 Mb/s per camera).
- **Bandwidth/capacity**: what the link could carry (negotiated: 100 or 1000 Mb/s).
- **Throughput**: what is actually delivered (measure with `iperf3`; ~94–95 Mb/s on a healthy Fast Ethernet link with UDP).
- **Headroom**: capacity left unused on purpose (≥ 30 %): I-frame bursts, retransmissions, control and telemetry, measurement error.

Overhead: Ethernet adds 38 bytes per frame on the wire (preamble+SFD 8, header 14, FCS 4, inter-frame gap 12); IPv4 20; UDP 8; RTP 12. With a 1500-byte MTU: 1538/1460 ≈ 1.053 → ~5 %. MPEG-TS over UDP: ~7 %.

Duplex: switched Ethernet is full-duplex (both directions at once). A true Ethernet *hub* is half-duplex with collisions — rare today, but check: `ethtool eth0` shows `Duplex: Full`.

Packet loss: on UDP, lost packets corrupt video (slide 33); on TCP, they cause retransmission, which shows up as **growing delay** and freezes. Jitter = variation in packet delay.

**Ask:** *“A 100 Mb/s tether, 8 cameras, 30 % headroom. Max average bitrate per camera?”*
Expected: 100 × 0.7 / 8 = 8.75 Mb/s, before ~5 % overhead → ≈ 8.3 Mb/s of video.

**Misconceptions:**
- “100 Mb/s link = 100 Mb/s of video.” → Minus overhead, minus headroom, minus control traffic.
- “Average bitrate is what matters.” → Peaks matter (slide 27).
- “Gigabit switch = gigabit tether.” → The tether may negotiate 100 Mb/s (cable length/quality, extenders). Measure both ends.

⏱ **Break (10 min).** **Transition after the break:** *“Compression is the core of the system — so let's open the box and see how an encoder throws away 99 % of the bits without the pilot noticing.”*

---

## 1.4 How video encoding works

**Objective:** Intuitive but correct mental model of a hybrid video encoder.
**Duration:** 30 min · **Slides:** 22–26

**Slide 23 — four ideas.**
1. **Predict** each block — from neighbouring pixels in the same frame (*intra*) or from earlier frames (*inter*).
2. **Transform** the prediction error (residual) into frequencies (a DCT-like integer transform). Most energy ends up in a few low-frequency coefficients.
3. **Quantize**: divide coefficients by a step size and round. **This is the only lossy step.** Bigger step → fewer bits → more distortion. The quantizer (QP) is what CRF and bitrate control ultimately set.
4. **Entropy-code** the symbols (CAVLC or CABAC in H.264) — lossless packing.

**Rate control** sits on top, choosing QP per frame/block to hit a quality (CRF) or bitrate target.

Key insight for later: *the decoder runs the same predictions*. The encoder sends instructions + corrections. If a reference is lost, everything predicted from it is wrong until something intra-coded arrives.

**Slide 24 — YUV and chroma subsampling.** Human vision resolves brightness detail much better than colour detail. YUV separates **luma** (Y) from two **chroma** components (U, V / Cb, Cr). 4:2:0 keeps one chroma pair per 2×2 block → 8 + 16/4 = **12 bits/pixel** instead of 24. Free 50 % before any “real” compression.
- **NV12** = Y plane + interleaved UV plane (common for hardware encoders/decoders).
- **YUV420P** (I420) = three separate planes.
- Almost all hardware decoders and browsers expect 8-bit 4:2:0. If you feed 4:2:2 (YUYV) to Jetson's encoder, convert first (NVIDIA's forum guidance: the hardware encoder doesn't accept YUV422).

**Slide 25 — redundancy and motion.**
- **Spatial redundancy** → intra prediction.
- **Temporal redundancy** → motion estimation (search the reference frame for the best match) + motion compensation (send a motion vector and the residual).
- **Blocks:** H.264 macroblocks are 16×16 (partitioned down to 4×4); H.265 **coding tree units** up to 64×64, recursively split — large flat areas (open water) become one cheap block.
- **Slices:** independently decodable regions of a frame — used for error resilience and parallel/low-latency encoding.

> *“Particles, noise and moving caustics can't be predicted from the previous frame, so the residual stays large. Good lighting and lower camera gain literally save bandwidth.”*

**Slide 26 — I, P, B and GOP.**
- **I-frame**: intra-only; a decoder can start here; large. (An **IDR** frame additionally tells the decoder to forget all previous references.)
- **P-frame**: predicted from earlier frames; small.
- **B-frame**: may also reference a *future* frame — the encoder must wait for that future frame → **adds latency**. Live low-latency streams normally disable B-frames.
- **GOP**: from one I-frame to the next. Measured (GOP 30, CRF 23): average I-frame ≈ 45 kB vs P-frame ≈ 12 kB — about 4×. On noisier/less-moving footage the ratio is often larger.

**Ask:** *“Why would a long GOP save bandwidth, and what does it cost?”*
Expected: fewer big I-frames → lower average bitrate; cost: slower start/switch, slower recovery after loss.

**Misconceptions:**
- “Compression means lower resolution.” → No: it removes redundancy and imperceptible detail at the same resolution.
- “Lossless is possible for live video on a tether.” → Technically yes (FFV1, x264 `-qp 0`), but at tens of Mb/s per camera; not practical for 8 cameras on 100 Mb/s.
- “The GPU encodes video.” → On Jetson, a dedicated encoder block (NVENC) does; the CUDA cores are separate.

---

## 1.5 Codecs, parameters, rate control, GOP and loss (🧪 Encoding Lab)

**Objective:** Students understand what each encoder knob does, the CRF vs bitrate decision, and the GOP/loss trade-off — from measurements.
**Duration:** 30 min · **Slides:** 27–30 · **Encoding Lab:** Encode, Sweep and Bandwidth budget → Packet-loss lab

**🧪 Live demo first (5 min):** in the Encoding Lab, run one H.264 encode in the Encode tab and read the result chips and cards together. Then show the same encode as an FFmpeg command, argument by argument (`-c:v libx264`, `-preset`, `-crf`, `-pix_fmt yuv420p`, `-an`), and open **🧮 Show the math**: raw bitrate, compression ratio, bits per pixel, cores per stream.

**Slide 27 — CRF vs bitrate-based.**
- **CRF** (quality-based): constant perceived quality, bitrate floats with content. Each +6 CRF roughly halves the x264 bitrate. Great for **recording**.
- **Target bitrate + VBV** (`-b:v`, `-maxrate`, `-bufsize`): bitrate capped, quality floats. Right for the **live tether**. Smaller `bufsize` → smoother bitrate and lower latency, but hard scenes lose quality.
- Measured: CRF 23 averaged 1.5 Mb/s but **peaked at 2.6 Mb/s** in 200 ms windows; a VBV encode at the same average peaked at 2.0 Mb/s.

> *“When the ROV kicks up sediment, a CRF stream can double its bitrate — exactly when the pilot needs the picture most. Live streams need a ceiling.”*

The chart shows the bitrate each codec needed for equal SSIM at two operating points. **The curves cross**: on our clip, at the tight-tether point (SSIM 0.96) AV1 needs about a quarter of H.264's bits while H.265 is roughly level with H.264 (it pulls ahead only at even lower bitrates); at the high-quality end x264 holds up best. Published results on natural camera footage usually show larger gains for H.265/AV1; our synthetic clip suits H.264's tools. The lesson: *“which codec is best?” has no answer without an operating point and real content.* (In our measurement we used `-tune ssim` for this comparison — otherwise each encoder's psychovisual tuning distorts the metric.)

**Slide 28 — codec comparison.** Don't crown a winner:
- **MJPEG**: lowest encode cost and latency, no inter-frame error propagation, decodes everywhere — but several times the bitrate. Fine for a simple auxiliary camera.
- **H.264**: universal; hardware encode on Jetson Nano; software on Pi 5. Default choice for live streams to a browser.
- **H.265**: better compression at many operating points; hardware encode on Jetson Nano; Pi 5 decodes it in hardware but can't encode it in hardware; browser support is uneven — **test the pilot laptop's browser**.
- **AV1**: excellent compression, very expensive software encode; neither board encodes it in hardware. Recording/archiving later, not the live ROV today.

**Slide 29 — MJPEG: costly in bits, cheap in everything else.** *(new, Nov 2026)* Click through the three numbers, then the two cards. MJPEG is every frame as its own JPEG: no encoder hold, and a lost frame never smears into the next. Measured on our 720p30 clip: at the same SSIM, MJPEG needed **4.7×** H.264's bitrate (q=3: 11.9 Mb/s vs CRF 21: 2.52 Mb/s); copying a USB camera's own MJPEG with FFmpeg cost **1.3 % of one core**. So: H.264 for what the pilot drives with; MJPEG where it is free (the camera already makes it) or flexible (CV debug views, snapshots, training data, the fallback stream). Reading: `docs/mjpeg-and-ffmpeg.md`.

**Slide 30 — use FFmpeg, not mjpeg-streamer.** *(new, Nov 2026)* Click once for the table, once for the verdict. We read the PyPI library's source and tested it: it **re-encodes for every viewer** (2 viewers = 28 encodes/s instead of 14) and **paces by a timer** (a 5 fps source went out at ≈ 14 fps of duplicates). mjpg-streamer (C) is fine at passthrough but was last changed in 2021 and its Pi-camera plugin needs MMAL, which the Pi 5 lacks. FFmpeg does every job, plus RTP, recording, filters, H.264 and metrics, and the team already uses it. Be honest about the one gap: FFmpeg's HTTP server serves **one viewer per process**; we cover it by sending RTP once over the tether and fanning out topside.

**Slide 31 — FFmpeg recipes.** *(new, Nov 2026)* One recipe per click. Demo live if time allows: `demos/02_pipeline/mjpeg_ffmpeg.sh http` and open `http://localhost:8080/aux1.mjpg` in a browser; then `mjpeg_ffmpeg.sh tee` and show the recording and `aux1_latest.jpg` growing; then `python3 demos/02_pipeline/cv_debug_ffmpeg.py` and `ffplay … det.sdp`. Two gotchas to say out loud: `-content_type` is required for browsers, and `-huffman default` is required when FFmpeg encodes JPEG for RTP.

**Slide 32 — knobs.** Walk the table: bitrate, CRF, preset, GOP, B-frames, lookahead, resolution, frame rate. Then the preset charts (measured on the presenter laptop): CPU time per frame grows ~35× from `ultrafast` to `veryslow`, while bitrate at CRF 23 drops with diminishing returns after `medium`/`slow`. (CRF 23 isn't exactly equal quality across presets — `ultrafast` disables many tools.)

Profiles & levels: a **profile** limits which tools are used (Constrained Baseline / Main / High); a **level** limits resolution × frame rate × bitrate the decoder must handle. Pick what the decoder (browser, hardware) supports. Raspberry Pi's white paper measured a low-latency x264 configuration with CABAC disabled — CABAC isn't allowed in Baseline profile and costs CPU.

**Slide 33 — packet loss (measured).** We deleted ~8 kB (six UDP datagrams of MPEG-TS) at three moments and decoded:
- **GOP 30**: damaged ≈ 0.6 s on average (worst 0.7 s).
- **GOP 150**: ≈ 2.2 s on average, worst **3.6 s** — until the next I-frame at t = 5 s. *(One of the three losses was rescued early by the camera cut at t ≈ 4 s, an almost all-intra frame. Luck is not a design: plan for the worst case.)*
- **Intra refresh** (a column of intra blocks sweeping across the picture every 30 frames, no I-frames): ≈ 0.6 s, within about one refresh period — and **no I-frame bitrate spikes**.

Camera switching connection: a player that joins a stream mid-GOP shows nothing until the next I-frame. *“Camera switch takes 2 seconds”* often means *“our GOP is 2 seconds.”* Fixes: shorter GOP; request a keyframe on switch (RTCP PLI/FIR in RTP/WebRTC); or keep low-res substreams decoding so a switch is instant.

**Ask:** *“Why doesn't TCP show this smearing?”*
Expected: TCP retransmits → no corruption, but the stream **waits** → latency grows and video freezes/jumps. Both are bad for a pilot; which is worse depends on the task.

**Misconceptions:**
- “Higher bitrate always means better.” → Past the knee of the curve, more bits buy almost nothing — and congest the tether.
- “Slowest preset = best.” → Best compression per bit, but more CPU and often more latency.
- “GOP = frame rate.” → Coincidence of a common setting (GOP 30 at 30 fps = 1 s); they're independent.

⏱ **Break (10 min).**

---

## 1.6 Measuring quality (🎯 Activity 3)

**Objective:** Know PSNR/SSIM/VMAF, their maths and their limits; experience a blind comparison.
**Duration:** 20 min · **Slide:** 28 · **Encoding Lab:** Encode → Frame compare (Diff ×8, Zoom 3×) and Quality over time

**Explain (5 min):**
- **PSNR** = 10·log₁₀(255² / MSE). Every pixel error counts equally. Rough guide for 8-bit video: < 30 dB clearly degraded; 35–40 dB good; > 45 dB near-transparent. +6 dB ≈ half the average error.
- **SSIM** compares local luminance, contrast and structure; 1.0 = identical. Better at catching blur and blocking.
- **VMAF** (Netflix) fuses several features with a model trained on human opinion scores for TV/film viewing; 0–100. Needs FFmpeg with `libvmaf`.
- **Limitations:** all three need the original (full-reference) — fine in the lab, impossible live; they measure *fidelity*, not *usefulness for a pilot*; noise removal can lower PSNR while looking better.

Explain (the Lab does not stage this one): a harmless brightness shift (+8 levels) scores ~30 dB PSNR, *worse* than a blur that removed real detail; SSIM ranks them closer to how people do.

**🎯 Activity 3 — Compression Challenge (12 min).** Play clips A–E (prepared in the Encoding Lab) on the projector, same scene. Teams rank by quality and guess bitrates. Reveal measured bitrate/PSNR/SSIM. Points: 3 per correctly placed clip in the ranking, 2 for the closest bitrate guess overall. Debrief:

> *“Did the metric agree with you? Would it agree with the pilot doing a manipulator task?”*

**Key line:** *“Metrics compare settings consistently. Pilots decide what is good enough.”*

**Transition:** *“We know how to compress. Now: who does the work, how do the bits travel, and how long does it all take?”*

---

## 1.7 Hardware, protocols and latency

**Objective:** Correct facts about Jetson Nano and Pi 5; choose where to encode; choose a transport; understand the latency chain.
**Duration:** 25 min · **Slides:** 32–40

**Slide 36 — software vs hardware encoding.** Software (x264/x265/SVT-AV1 on CPU): flexible, best quality per bit, cost scales with resolution × fps × streams, competes with control software, heats the SBC. Hardware encoder: dedicated silicon, near-zero CPU, predictable, **fixed total capacity**, fewer knobs, vendor APIs.

> *“On this laptop, FFmpeg lists h264_nvenc, h264_qsv, h264_vaapi and h264_v4l2m2m — and every single one failed a test encode. Listed means compiled in, not working. Always run a one-second test encode.”*

**Slide 37 — Jetson Nano vs Raspberry Pi 5.** This is the most fact-sensitive slide. Say exactly:

- **Jetson Nano** (2019, Maxwell GPU, quad Cortex-A57): hardware **encoder** for H.264 and H.265 — up to 4K30, or 4× 1080p30, or 9× 720p30 (NVIDIA spec); hardware decoder up to 4K60 / 8× 1080p30. Use the encoder through **GStreamer** (`nvv4l2h264enc`, `nvv4l2h265enc`) or NVIDIA's Multimedia API. **Upstream FFmpeg does not use the Nano's encoder**; NVIDIA's FFmpeg package accelerates *decode*; community patches (e.g. `jetson-ffmpeg`) exist. The Nano is supported up to JetPack 4.6.x (Ubuntu 18.04).
- **Raspberry Pi 5** (BCM2712, quad Cortex-A76 @ 2.4 GHz): **no hardware H.264 encoder, no hardware H.264 decoder**; it has a 4Kp60 **HEVC decoder**. Encoding is software (libx264). Raspberry Pi's own white paper (April 2026) measured one 1080p30 low-latency x264 encode at ~62–90 % of one core, and a higher-quality configuration at ~98–153 %, depending on bitrate. It did not test multiple streams or thermals — that's their experiment.
- **Jetson *Orin* Nano**: **no hardware video encoder**; NVIDIA says 1080p30 is encoded with 1–2 CPU cores. Check `cat /etc/nv_tegra_release`.

**Ask:** *“So which board would you choose for eight cameras — and what measurement would change your mind?”*
Expected discussion: Nano's encoder covers ~4× 1080p30-equivalent of pixel rate, so 8 cameras at 1080p30 won't fit — but 1–2 main + substreams can; Pi 5 needs camera-side encoding (IP cameras / H.264 UVC) to scale; measure CPU, temperature, and the USB bus in either case.

**Slide 38 — where to encode.** Prefer, in order (after measuring): in the camera → SBC hardware → SBC software. Encoding on the topside laptop saves **zero** tether bandwidth. Remember: MJPEG from USB cameras must be decoded before re-encoding (Jetson can do JPEG decode in hardware: `nvv4l2decoder mjpeg=1` / `nvjpegdec`).

**Slide 39 — can the Pi 5 replace the Nano?** *(new, Nov 2026)* The answer depends on who encodes. Cameras that encode (UVC H.264 or IP) → the Pi 5 is a good replacement, with a much faster CPU. The SBC must encode several raw/MJPEG USB cameras → the Nano's hardware encoder (4× 1080p30) wins; the Pi 5 spends 0.62–0.9 of a core per 1080p30 low-latency stream (Raspberry Pi white paper, April 2026). On-board CV: Nano GPU vs Pi 5 + AI HAT+ (13/26 TOPS). Lifecycle: Nano dev kit EOL, JetPack 4 EOL Nov 2024, modules until Jan 2027. Nobody has tested the Pi 5 on our ROV yet, so finish with the soak-test plan.

**Slide 40 — the 2023 heat failure.** *(new, Nov 2026)* Tell the story briefly and without blame: in a 2023 competition trial the stream died because the SBC overheated. Walk the chain: sealed hull → constant encode load → throttling at 80 °C (Pi) → encoder falls behind → stream stops. Then the five fixes: measure, design a heat path, reduce load, soak-test, show temperature to the pilot. Ask whoever was there for details and fill in `sdlc/postmortem-template.md` together.

**Slide 41 — protocols.**
- **UDP**: no retransmission; lost is lost; no waiting.
- **TCP**: reliable, ordered; under loss/congestion, head-of-line blocking → growing delay.
- **RTP (+RTCP)**: timestamps and sequence numbers over UDP; RTCP carries receiver reports (loss, jitter) and keyframe requests. The classic low-latency transport.
- **RTSP**: controls RTP sessions (DESCRIBE/SETUP/PLAY); can interleave RTP over TCP. IP cameras speak it; browsers don't.
- **WebRTC**: browser-native real-time media over UDP with congestion control and keyframe requests; typically a few hundred ms or less glass-to-glass when configured well.
- **HTTP-MJPEG**: simple and low-latency, bandwidth-hungry.
- **HLS/DASH**: segmented HTTP streaming for viewers — seconds of delay. **Never for piloting.**
- Bridge: cameras → RTSP → **MediaMTX** (single binary, converts RTSP ↔ WebRTC/WHEP) → browser.

**Slide 42 — latency budget (ESTIMATE).** Three pipelines; numbers are typical, except the x264 encoder hold which is measured. The H.264-with-defaults pipeline is ~2.4 s, dominated by encoder lookahead (≈ 1.37 s) and a 1 s player cache (VLC's default network caching is 1000 ms) — not by the cable.

> *“FPS is not latency. A perfect 30 FPS stream can be two seconds late — like a long conveyor belt that still delivers 30 boxes a second.”*

**Slide 43 — latency is designed (measured).** x264 defaults held **41 frames** before the first output (rc-lookahead 40 + frame threading) ≈ 1.37 s at 30 fps — independent of CPU speed. `-tune zerolatency` held **0**. Recipe: `-preset veryfast -tune zerolatency`, capped bitrate with small `bufsize`, short GOP, no B-frames; receiver: small jitter buffer.

Jitter chart: a simulated tether with small everyday jitter and 2 % spikes of 30–80 ms. Every extra millisecond of buffer reduces late frames but adds latency. Choose deliberately (e.g. 30–60 ms on a clean wired tether) and measure.

**How to measure glass-to-glass (tell them now; it's homework):** millisecond clock on the topside screen; camera pointed at it; video window next to it; phone photo of both; difference = latency; ≥ 10 repeats; report median and worst; repeat with 1 and 8 cameras, with thrusters on.

**Misconceptions:**
- “The network is the latency.” → On a short wired tether, the wire is microseconds; queues and buffers are milliseconds to seconds.
- “UDP is unreliable so it's bad.” → For live video, late data is useless; UDP + good GOP/intra refresh is the professional choice.
- “WebRTC is only for video calls.” → It's the browser's real-time media engine — ideal for a web pilot UI.

---

## 1.8 Multi-camera strategy, measurement, diagnosis (🎯 Activity 2)

**Objective:** Apply everything to eight cameras; produce a measurement-based diagnosis and an optimization procedure.
**Duration:** 35 min · **Slides:** 41–47

**Slide 44 — main vs substreams (measured).** Main 720p30 ≈ 2.5 Mb/s; sub 640×360@15 ≈ 0.42 Mb/s; thumbnail 320×180@10 ≈ 0.12 Mb/s. Eight cameras: all-main 19.8 Mb/s; 1 main + 7 subs ≈ 5.4 Mb/s (≈ 27 %). IP cameras usually provide substreams natively; on an SBC: GStreamer `tee` or one FFmpeg process with two outputs (costs encoder capacity).

> *“The pilot looks at one or two cameras at a time. The other six only need to answer: is something happening there?”*

**Slide 45 — priorities and adaptation.** Measure → budget (70 % of throughput minus control/telemetry) → allocate (minimums by priority, then top up) → apply (encoder bitrate, pause/resume) → show (UI states: live, degraded, paused, lost). Priorities change with the task: the manipulator camera becomes priority 1 during a grab. The measurement (former notebook Experiment 8; Bandwidth budget tab in the Encoding Lab) shows the tether degrading 100 → 40 → 20 → 6 Mb/s: the pilot view stays sharp; aux cameras degrade then pause — visibly.

Requirements for this: encoders whose bitrate can change at runtime (hardware encoders and x264's API can; many IP cameras expose it via HTTP/ONVIF), a throughput estimate (RTCP receiver reports, WebRTC stats/congestion control, probing), and an honest UI.

**Slide 46 — streaming for computer vision.** *(new, Nov 2026)* Detection, 3D reconstruction, autonomy and SLAM all inherit streaming decisions when they run on the topside stream. A YOLOv5 study on H.264 found moderate compression (CRF 37 vs 22) barely mattered, but performance dropped at stronger compression — worst in poor light and fast motion, which is underwater footage. SLAM needs corners and texture, exactly what compression removes. Rules: run CV next to the raw frames; otherwise give CV its own stream profile; photogrammetry uses stills or local recordings.

**Slide 47 — toolbox.** Point at the Diagnostic Checklist, which has the full commands. Each claim in their design document should cite one of these measurements.

**🎯 Slide 48 — Activity 2: Diagnose the ROV (20 min).** Read the scenario: 8 cameras at 640×480; after ~10 min in the water video lags ~1 s; two cameras freeze occasionally; one sometimes fails to start; thrusters feel slow; plan = reduce resolution again. Teams list ≥ 5 hypotheses, rank them, and give a measurement for each. Answer key in `Activity_Instructions.md`. Score: 1 per plausible hypothesis, 2 per correct measurement, +3 for the best-ranked root cause.

Good answers to listen for: USB bus/isochronous reservation (camera fails to start; `lsusb -t`, `dmesg`); SBC CPU saturated by MJPEG decode + re-encode (`top`); thermal throttling after 10 minutes in a sealed hull (`vcgencmd get_throttled`, `tegrastats`); TCP-based streaming accumulating delay (latency grows over time); player buffering; tether negotiated 100 Mb/s or with errors (`ethtool`, `ethtool -S`); topside browser decoding 8 streams (DevTools Performance, `chrome://media-internals`); control traffic queued behind video on the same link (thrusters feel slow!); power brown-outs from thrusters resetting USB (`dmesg`).

**Slide 49 — optimization strategy.** In order: inventory & measure → stop wasting bits → stream smart → design latency → design failure → verify. *“Reducing resolution is the last lever, not the first.”*

**Slide 50 — homework.** Hand out the Diagnostic Checklist; each subsystem owner fills their part. Record 60 s of real footage (upload it to the Encoding Lab (sidebar → Upload your own video). Measure glass-to-glass latency.

**Transition to Session 2 (next time):** *“Bring the numbers. We'll turn them into requirements, tests and a better pilot interface.”*

---

# SESSION 2 — ENGINEERING PRACTICE & UX (≈ 3 h 55 min incl. one 10-min break)

## 2.0 Recap (10 min)

Ask each subsystem owner for one surprising finding from the checklist. Write them on the board under **Facts / Surprises / Still unknown**. If nobody did the homework, do 5 minutes of it live with the SBC (if available): `ffprobe`, `lsusb -t`, `ethtool`.

> *“Notice what just happened: we found things we didn't know. How do we make sure we keep finding them before competition day, not on it? That's what process is for.”*

---

## 2.1 Lifecycle, requirements, DoR/DoD

**Objective:** A lightweight process the team can actually run; testable requirements; shared definitions of ready and done.
**Duration:** 30 min · **Slides:** 48–54

**Slide 52 — integration cliff.** The chart is **illustrative**, not data. Tell a story: every subsystem works alone; the week before competition everything is connected; the camera driver and thruster controller fight over USB power; the web app can't keep up with 8 streams; nobody remembers why a setting was chosen. Late discovery = no good fixes.

**Slide 53 — Work force = Quality × Efficiency.** *(new, Nov 2026)* It's a product: a zero in either factor makes the result zero. Fast but broken = 0; perfect but late = 0. Ask the room which factor is weaker today; the rest of the session gives a lever for each.

**Slide 54 — SDLC loop, ROV examples:**
1. Requirements — “pilot camera latency ≤ 200 ms median”.
2. Analysis & architecture — where to encode, which protocol.
3. Planning — tasks, owners, order, dependencies.
4. Implementation — small branches.
5. Testing — unit → integration → pool.
6. Code review — every PR.
7. Integration — merge weekly; run on the real ROV.
8. Release — tag `v0.4-pool-test`.
9. Maintenance — retrospective, fix, improve.

A 1–2 week loop, not a waterfall.

**Slide 55 — functional vs non-functional.** Functional = what it does; non-functional = how well (latency, bandwidth, reliability, usability, safety). Testable = **a number, a condition, a method**.

**2-minute exercise:** each team rewrites “the video should be smooth and low latency” as a testable requirement.
Good answer: *“With all eight cameras streaming, the pilot camera's glass-to-glass latency is ≤ 200 ms median and ≤ 300 ms worst over 10 measurements, at ≥ 25 fps.”*

**Slide 56 — epic → test case.** Walk down: epic *multi-camera pilot video* → feature *primary camera selection* → user story *“As a pilot, I want to switch the primary camera with one key, so that I can follow the task without looking away from the video”* → acceptance criteria (≤ 1 s, highlight, offline shown honestly, other streams continue) → tasks → test cases tracing to criteria.

**Slide 57 — DoR/DoD.** Short lists, printed, on the wall, reviewed in retros. DoD includes *tested on the real ROV for hardware-related work* and *UI changes tried by a pilot*.

**Misconceptions:**
- “Process slows us down.” → Rework slows you down; a 30-minute weekly planning saves days of integration panic.
- “Agile means no documentation.” → It means *just enough*: requirements, decisions, test results.

---

## 2.2 Testing (🎯 Activity 4)

**Objective:** Testing as discovering failure; levels and techniques; experience finding, reporting and fixing real defects.
**Duration:** 10 min talk + 60 min activity · **Slides:** 55–58

**Slide 58 — levels and techniques.** Pyramid: many fast unit tests (allocator, command parser, PID maths), fewer integration tests (stream manager + real FFmpeg/GStreamer; web app + backend), few system tests (whole ROV in the pool), acceptance tests with the pilot. Techniques: boundary, negative, stress, performance, regression.

**Slide 59 — mindset.** *“A test that cannot fail is not a test.”* Developers test to confirm; testers test to break. Read 2–3 scenarios and ask: *“For which of these do we already know what our system does?”* (Usually none.)

**🎯 Slide 60 — Break the Other Team's Software (60 min).** Follow `student_materials/Testing_Competition_Guide.md`.
- Teams test `rov_core` (camera manager + command validator) against `SPECIFICATION.md`.
- The code contains **16 seeded defects**, 6 of them critical (crash, frozen frame reported live, unsafe thruster values). The referee key and a test that proves each one are in the presenter-only `referee/` folder (Drive, not the team repo) — **don't hand those out**. Copy it next to the code and run it yourself: `python -m pytest -q path/to/referee/test_referee_seeded_defects.py` from the code folder → 16 failed. When a team fixes a defect, its referee test passes.
- Scoring is in the guide (+10 defect, +20 critical, +5 clear repro with automated test, −5 false positive, +10 fix with regression test, −10 fix that breaks something).

Refereeing tips: validate every claim against the spec, explain each decision, and award the “best bug report” bonus to the clearest report, not the most dramatic defect.

**Debrief questions (10 min):** Which technique found the critical defects? (Usually special values — NaN — and state-based tests.) Why did all 7 starter tests pass? How did it feel to receive bug reports about “your” code?

⏱ **Break (10 min).**

---

## 2.3 Code review, Git, organisation, mindset

**Objective:** Practical, kind code review; a simple Git workflow; a board and a rhythm; outcome metrics.
**Duration:** 25 min · **Slides:** 59–64

**Slide 61 — the Bug Hunt League.** *(new, Nov 2026)* The 16 non-GUI members are our best testers. Points by severity (10/5/2/1), bonuses for repro videos, failing tests and regressions; developers can't score on their own code; the hunter verifies the fix. Weekly leaderboard, monthly award, Bug Bash before every pool test. Full rules: `sdlc/bug-hunt-league.md`.

**Slide 62 — code review.** Why: catch defects early, spread knowledge (a student team's “bus factor” is often 1), keep consistency. How: small PRs (< 400 lines, one purpose); label comments *blocking / suggestion / question*; comment on code, not people (*“this function doesn't handle a disconnected camera”*, never *“you forgot”*); approve when it improves the codebase and meets the DoD — not when it's perfect. Disagreements: data or a quick prototype; still stuck → the subsystem lead decides and it goes into the decision log.

**Slide 63 — live review (8 min).** Show only the BEFORE code; teams find ≥ 5 problems in 3 minutes. Expected: cryptic names (`sw`, `c`, `v`); hard-coded IP; no validation; fire-and-forget `fetch` with no error handling; **UI claims success immediately** (“CAM 3 OK” even if offline); no state feedback; string concatenation into a URL. Reveal AFTER; discuss the trade-off (more code, but every state explicit and failures visible to the pilot).

**Slide 64 — Git.** Trunk-based with short-lived branches; `main` always runnable on the ROV; PR + 1 review; meaningful commits that explain *why*; tag before every pool test and competition (`v0.4-pool-2026-03-14`). Merge conflicts: pull `main` often; small PRs mean small conflicts.

**Slide 65 — GitHub is a workflow, not a folder.** *(new, Nov 2026)* Today the repo is a backup drive. Show the six features (Issues, PRs, Actions, Releases, branch protection, Projects) and the four-week ladder: one habit per week. Templates are ready in `.github/`. Guide: `sdlc/github-workflow.md`.

**Slide 66 — board.** Backlog / Ready / In progress (WIP ≤ 2 per person) / Review / Done. Card types: story, task, bug, debt. Weekly rhythm: Monday 30-min planning; async “done / next / blocked” updates; Friday 30-min review + retro (what went well, what didn't, one improvement). Milestones = pool tests and the competition. Tool doesn't matter (GitHub Projects, Trello, Jira).

**Slide 67 — mindset & metrics.** Habits: measurable objectives; decision log (context, options, decision, why); blockers raised the same day; hardware–software interfaces agreed early (connectors, message formats, power budget); failed experiments are data. Useful metrics: requirements met (measured), test pass rate, defects found vs fixed, features done (DoD), main runnable, latency/bandwidth vs targets. Vanity: lines of code, commits, hours, features *started*.

**Transition:** *“We've made the system faster and more reliable. Now: is it usable by a human under pressure?”*

---

## 2.4 UX for ROV pilots

**Objective:** UX as an engineering discipline: understand the pilot, apply principles, design for safety, validate with users.
**Duration:** 35 min · **Slides:** 65–74

**Slide 69 — central message.** Read the quote slowly:

> *“An excellent engineering system is not just one that works technically. It is one that allows its operator to use it effectively, confidently, and safely.”*

The pilot simultaneously understands the situation, monitors several feeds, controls movement, operates the manipulator, watches telemetry, and reacts to the unexpected. Ask a pilot in the room for their worst moment on mission day — it's usually a UX failure. *“Attractive is not the same as usable”*: thin fonts, low-contrast dark-on-dark, decorative animation can actively hurt under stress.

**Slide 70 — vocabulary.** UI = the screens and controls; UX = the experience of getting the job done; HCI = the research discipline; human factors = designing for human abilities and limits (aviation, nuclear, subsea); accessibility = usable in different conditions and by different people. **Cognitive load**: working memory is small — every extra thing to find or remember steals attention from driving. **Situational awareness**: perceive → comprehend → project; e.g. show *“depth 2.31 m, 0.2 m above target”*, not just *“2.31”*.

**Slide 71 — persona & journey.** A persona is a realistic composite from observation (Mariam: pilot, gamepad in both hands, glances only). The journey maps a mission with pain points (red): grab object; camera freezes without her noticing. Pain point → requirement: *“A stale feed is visibly marked within 1 s.”* Full persona and journey: `ux_materials/UX_Pilot_Experience_Pack.md`.

**Slide 72 — seven principles** (one ROV example each): information hierarchy; low cognitive load; situational awareness; feedback (**requested ≠ confirmed**); error prevention (dangerous actions deliberate); consistency (never move a control — muscle memory); customization (with a known-good default and reset).

**Slide 73 — before/after.** Ask: *“Where does your eye go first on each?”* Before: eight equal tiles, telemetry as tiny text, buttons of equal weight (STOP looks like LIGHT), no camera or link state. After: large primary feed with HUD (depth, heading), thumbnails with explicit states (LIVE/DEGRADED/LOST), link and mode always visible, separated E-STOP, commanded vs confirmed gripper state.

**Slide 74 — layouts.** Primary + previews (navigation), grid (search/survey), picture-in-picture (manipulation: manipulator camera large, pilot camera inset), task workspaces (per mission phase, switched with one key). The best layout depends on the task, not on taste — and controls stay in the same place in every layout.

**Slide 75 — UX is a safety feature.** The rule: **the UI must never imply that an operation succeeded when the system has not confirmed it.** Commanded vs confirmed; data age (telemetry older than ~1 s marked stale); deliberate dangerous actions (hold-to-confirm, two-step); defined connection-loss behaviour on the ROV + unmistakable banner topside; E-stop always reachable, never moved, visually distinct; safe defaults (start disarmed). Say clearly: *“I'm not prescribing your safety implementation — design it with your control architecture and the competition's safety rules.”*

**Slide 76 — usability testing.** Recruit a pilot who didn't build the UI. Give **tasks, not instructions**: *“While holding depth, switch to the rear camera, find which camera has a problem, then return to the pilot camera.”* Think-aloud. Measure task completion, time on task, errors, and satisfaction (the 10-question **System Usability Scale**, SUS, 0–100). About five users find most of the major problems (Nielsen). Heuristic evaluation = cheap expert review. A/B test only with two concrete variants and enough trials.

**Slide 77 — UX in the lifecycle.** Understand → require → wireframe → prototype → test → build → validate. Show the user story (*identify disconnected cameras immediately*), its acceptance criteria (unmistakable indicator; frozen frame never shown as live; feedback on disconnect/reconnect; other feeds continue) and DoD (disconnect/reconnect tested; visual states reviewed; usability-tested with a pilot; no regressions).

**Misconceptions:**
- “UX is the colours at the end.” → UX decides what information exists on screen, when, and how actions are confirmed.
- “Developers know what pilots need.” → Developers know what the system *can* do. Watch pilots.
- “More data on screen = more awareness.” → More data = more cognitive load. Hierarchy creates awareness.

---

## 2.5 🎯 Activity 6 — Design the Perfect ROV Pilot Experience (40 min)

Follow `ux_materials/UX_Pilot_Experience_Pack.md` §6. Brief (5) → design on A3 or in Figma/Penpot (20) → swap: another team's member pilots the paper prototype while designers “play computer” (10) → score with the rubric (5). Observers time the five tasks and count errors.

Debrief: *“What surprised the designers when someone else used their design?”*

---

## 2.6 Close — the challenge (15 min)

**Slide 80 — Activity 5 + post-workshop challenge.** Mission statement on screen. 4–6 weeks: baseline (week 1) → design with ≥ 2 architecture options compared by numbers (2–3) → build & test incl. failure cases and usability (3–5) → demonstrate before/after against requirements (6). Judged on requirements met (measured), quality of evidence, failure handling, pilot usability, documentation. No architecture is prescribed — the first deliverable is the measured baseline. Details: `workshop_activities/Post_Workshop_Challenge.md`; options: `student_materials/Proposed_Architecture_Options.md`.

If you have 20 minutes left, run **Activity 5** live: each team sketches its target architecture on A3 with a bandwidth budget and an encoder-capacity budget (rubric in `Activity_Instructions.md`).

**Slide 81 — seven things.** Read them as a checklist; ask each student to pick the one they'll act on first. Close with the mindset line.

**Slide 82 — thanks.** Point to the folder; offer to review their baseline measurements in two weeks; collect feedback (most useful / least clear).

---

## Appendix A — Quick technical answers to likely questions

| Question | Short, accurate answer |
|---|---|
| “Can we just use Wi-Fi?” | Not underwater: radio is absorbed within centimetres–metres in water. The tether is the link. Topside Wi-Fi is fine for spectators, not for the pilot. |
| “Why not H.265 everywhere?” | Only if the encoder exists where you encode (Jetson Nano yes; Pi 5 no hardware encode) and the pilot's browser decodes it. Measure the gain on your footage first. |
| “What bitrate should we use?” | The lowest that meets the pilot's quality requirement on *your* footage at the pilot's operating point — find it with the rate–quality curve and a pilot test, then cap it with VBV. |
| “Why is our video fine on the bench and laggy in the pool?” | Usual suspects: thermal throttling in the sealed hull; TCP delay growth under brief link problems; the tether negotiating 100 Mb/s or with errors; USB brown-outs when thrusters draw current. Measure each. |
| “Is 60 fps better for piloting?” | Smoother motion, but doubles pixel rate and encoder load. Latency matters more than fps; 25–30 fps with low latency usually beats 60 fps with high latency. |
| “What's an IDR frame?” | An I-frame that also clears the decoder's reference list — a clean random-access point. Streams start on IDR frames. |
| “What does `-tune zerolatency` actually do in x264?” | Disables lookahead and B-frames, uses slice-based threading instead of frame threading, and disables mb-tree — so each frame is output as soon as it's encoded. |
| “Can FFmpeg use the Jetson Nano's encoder?” | Not upstream FFmpeg. Use GStreamer (`nvv4l2h264enc`), the Jetson Multimedia API, or a community-patched FFmpeg. NVIDIA's FFmpeg package covers accelerated decode. |
| “Can the Pi 5 decode H.264 in hardware?” | No. It decodes HEVC in hardware; H.264 is decoded in software (fast enough for a few 1080p streams on the A76 cores, but it costs CPU). |
| “What is SRT?” | Secure Reliable Transport: UDP-based with selective retransmission within a latency budget; popular in broadcast contribution. An option, but WebRTC fits a browser UI better. |

## Appendix B — Timing cheat (print this)

| Block | Slides | Minutes | Running |
|---|---|---|---|
| **S1** Opening | 1–6 | 10 | 0:10 |
| Underwater & architecture | 7–14 | 30 | 0:40 |
| Bandwidth + Activity 1 | 15–21 | 30 | 1:10 |
| Break | | 10 | 1:20 |
| Encoding | 22–26 | 30 | 1:50 |
| Codecs, knobs, GOP (+ Encoding Lab) | 27–30 | 30 | 2:20 |
| Break | | 10 | 2:30 |
| Quality + Activity 3 | 31 | 20 | 2:50 |
| Hardware, protocols, latency | 32–40 | 25 | 3:15 |
| Multi-camera + Activity 2 + homework | 41–47 | 35 | 3:50 |
| **S2** Recap | — | 10 | 0:10 |
| SDLC, requirements, DoR/DoD | 48–54 | 30 | 0:40 |
| Testing talk | 55–56 | 10 | 0:50 |
| Activity 4 (+ debrief) + Bug Hunt League | 57–58 | 60 | 1:50 |
| Break | | 10 | 2:00 |
| Code review, Git, board, metrics | 59–64 | 25 | 2:25 |
| UX | 65–74 | 35 | 3:00 |
| Activity 6 | 75 | 40 | 3:40 |
| Close | 76–79 | 15 | 3:55 |
