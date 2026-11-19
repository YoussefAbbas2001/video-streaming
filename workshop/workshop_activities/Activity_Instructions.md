# Workshop Activities — Instructions, Materials and Answer Keys

Six activities, one every 20–30 minutes. Teams of 3–5, mixed experience in every team. Keep a visible timer.

| # | Activity | Session · slide | Duration | Detailed guide |
|---|---|---|---|---|
| 1 | Estimate the Bandwidth | S1 · 16 | 15 min | this file |
| 2 | Diagnose the ROV | S1 · 39 | 20 min | this file |
| 3 | Compression Challenge | S1 · 28 | 15 min | this file |
| 4 | Break the Other Team's Software | S2 · 50 | 60 min | `student_materials/Testing_Competition_Guide.md` |
| 5 | Architecture Challenge | S2 · 68 | 20 min + homework | this file + `Post_Workshop_Challenge.md` |
| 6 | Design the Perfect ROV Pilot Experience | S2 · 66 | 40 min | `ux_materials/UX_Pilot_Experience_Pack.md` §6 |

Keep a running **team scoreboard** across all activities; announce a winner at the end (small prize: first pick of pool-test slots, stickers, …).

---

## Activity 1 — Estimate the Bandwidth (15 min)

**Goal:** practise R = W × H × bpp × f, overhead and headroom; connect each estimate to a measurement.

**Materials:** one card per team (print the four cards below), calculators/laptops, the Cheat Sheet.

**Task for each card:**
1. Raw bandwidth per camera and total.
2. Compressed total (use the bitrate given, or the bits-per-pixel given).
3. On-the-wire total: +5 % for RTP/UDP, +6 % for HTTP/TCP, +7 % for MPEG-TS/UDP.
4. Utilisation vs 70 % of the link → verdict **OK / tight / over**.
5. One measurement that would confirm your answer on the real ROV.

### Cards

> **Card A** — 8 USB cameras sending **raw YUYV 640×480 @ 30 fps** through **one USB 2.0 hub** into the SBC. (Budget for periodic USB traffic: 80 % of 480 Mb/s.)
>
> **Card B** — 8 cameras streaming **MJPEG 1280×720 @ 30 fps** over HTTP to the browser on a **100 Mb/s** tether. Assume MJPEG at good quality ≈ **0.34 bits/pixel** (measured in the workshop notebook).
>
> **Card C** — 8 cameras streaming **H.264 1920×1080 @ 30 fps at 4 Mb/s each** over RTP/UDP on a **100 Mb/s** tether. The SBC (a Jetson Nano) encodes all of them.
>
> **Card D** — 1 camera **H.264 1080p30 at 6 Mb/s** (main) + 7 cameras **H.264 640×360 @ 15 fps at 0.5 Mb/s** (substreams), RTP/UDP, **100 Mb/s** tether.

### Answer key

| Card | Raw per camera | Raw total | Compressed total | On the wire | vs 70 Mb/s | Verdict | Measurement to confirm |
|---|---|---|---|---|---|---|---|
| A | 640·480·16·30 = **147.5 Mb/s** | 1,180 Mb/s | (raw — no compression) | — | USB budget 384 Mb/s → max **2 cameras** | **OVER** (USB bus, not tether) | `lsusb -t` (all on one bus?), start cameras one by one, watch `dmesg` for `No space left on device` |
| B | 1280·720·16·30 = 442 Mb/s (YUYV) | 3,539 Mb/s | 0.34·1280·720·30 = 9.4 Mb/s each → **75.2 Mb/s** | ≈ **79.7 Mb/s** | 114 % of budget (80 % of link) | **TIGHT → effectively over** (no headroom for peaks/control) | Measure the real MJPEG bitrate (`iftop`, or record 30 s and divide size by time) — real webcams often use *higher* MJPEG quality than this |
| C | 1920·1080·12·30 = 746 Mb/s (4:2:0) | 5,972 Mb/s | 8 × 4 = **32 Mb/s** | ≈ **33.7 Mb/s** | 48 % | Tether **OK** — **but the Jetson Nano's encoder is rated 4× 1080p30**: 8× 1080p30 is **2× over its encoder budget** | `tegrastats` (NVENC load), count dropped frames; or let IP cameras encode |
| D | main 746 Mb/s; sub 640·360·12·15 = 41.5 Mb/s | 1,037 Mb/s | 6 + 7 × 0.5 = **9.5 Mb/s** | ≈ **10.0 Mb/s** | 14 % | **OK**, lots of headroom | Check the cameras really offer substreams (camera web page / `ffprobe`); measure actual bitrates |

**Scoring (10 per card):** arithmetic 4 · correct verdict 3 · sensible measurement 3. **Bonus +3** for the team that spots the hidden bottleneck on Card A (USB, not the tether) or Card C (encoder capacity, not bandwidth).

**Debrief:** *“Two of the four cards had a bottleneck that was not the tether at all.”*

---

## Activity 2 — Diagnose the ROV (20 min)

**Goal:** turn symptoms into ranked hypotheses and measurements — before changing anything.

**Scenario (read aloud, also on slide 45):**
> The ROV has eight cameras streaming at 640×480. After about ten minutes in the water, the video lags by roughly one second. Two cameras freeze occasionally, and one camera sometimes fails to start at all. The pilot also says the thruster response “feels slow”. The team's plan is to reduce the resolution again.

**Task (per team, on the answer sheet):**
1. List at least **5 hypotheses**.
2. Rank them by likelihood.
3. For each, write **one measurement** that would confirm or reject it, and what result you would expect if it's true.
4. Say what you would do **first** on Monday.

### Answer key (accept any well-reasoned equivalent)

| Hypothesis | Symptom it explains | Measurement | Expected if true |
|---|---|---|---|
| USB bandwidth reservation on a shared hub | camera fails to start; freezes | `lsusb -t`; `dmesg` while starting cameras | several cameras on one 480M bus; `No space left on device` / `VIDIOC_STREAMON` errors |
| SBC CPU saturated (MJPEG decode + re-encode, Python loops) | lag, freezes, slow control | `htop` with all cameras | cores at ~100 %, control process starved |
| Thermal throttling in the sealed hull | starts fine, degrades after ~10 min | Pi `vcgencmd get_throttled`/`measure_temp`; Jetson `tegrastats` | rising temperature, throttled flag, lower clocks |
| TCP-based streaming accumulating delay (HTTP-MJPEG / RTSP-over-TCP) | latency grows over time, then jumps | glass-to-glass at t=1 min vs t=10 min; `ss -ti` send queue | latency increases; send queues grow |
| Player/browser buffering | constant ~1 s delay | browser stats (`chrome://webrtc-internals` jitterBufferDelay / player cache setting) | large buffer delay |
| Tether negotiated 100 Mb/s or has errors | lag/freezes under load | `ethtool` both ends; `ethtool -S` CRC errors; `iperf3` | 100Mb/s or Half duplex; errors increasing |
| Control traffic queued behind video on the same link | thrusters feel slow | `ping` RTT idle vs all streaming; timestamp control messages | RTT jumps from ~1 ms to 100+ ms when video runs |
| Topside laptop can't decode/render 8 streams | lag, dropped frames topside | Task Manager CPU/GPU; DevTools Performance; framesDropped | laptop CPU high; frames dropped at the decoder |
| Power brown-outs when thrusters run | freezes / camera resets during manoeuvres | `dmesg -w` while running thrusters | USB disconnect/reconnect, under-voltage messages |

The "slow thrusters" symptom is the key clue: **control sharing a congested link or a starved CPU with video** is a safety issue, not just a quality issue.

**Scoring:** 1 point per plausible hypothesis (max 7), 2 points per correct measurement, +3 for ranking a strong root cause (CPU/thermal, TCP delay growth, or control-behind-video) first, −2 if the first action is “reduce resolution” without a measurement.

---

## Activity 3 — Compression Challenge (15 min)

**Goal:** experience the gap between bitrate, metrics and perceived quality.

**Preparation (presenter):** after running the notebook, copy these files from `notebooks/work/` and rename them (keep the key secret):

| Clip | Source file | Bitrate (Mb/s) | PSNR (dB) | SSIM |
|---|---|---|---|---|
| A | `e3_crf28.mp4` | 0.93 | 44.0 | 0.973 |
| B | `e3_crf38.mp4` | 0.16 | 38.2 | 0.943 |
| C | `e3_crf18.mp4` | 2.49 | 48.1 | 0.987 |
| D | `e2_mjpeg.mkv` | 8.20 | 45.5 | 0.979 |
| E | `e3_vbv0.5.mp4` | 0.40 | 40.0 | 0.955 |

*(Values from the reference run on the synthetic clip — re-read them from your own notebook run and update the table.)*

**Run:** play each clip full-screen twice (or show a paused frame side by side). Teams rank A–E from best to worst quality and guess each bitrate.

**Reveal and discuss:**
- Did anyone rank D (MJPEG, the *largest* file) as best? Was it worth 9× the bits of A?
- Where did the team's ranking disagree with PSNR? With SSIM?
- Which clip would you accept for (a) navigation, (b) reading a gauge, (c) the manipulator?

**Scoring:** 3 points per clip placed at its measured (SSIM) rank; 2 points for the closest total bitrate guess; 2 bonus points for a team that argues convincingly *why* a metric is misleading for one of the clips.

---

## Activity 5 — Architecture Challenge (20 min in session + homework)

**Goal:** design a target video architecture for *your* ROV with numbers, and identify what must be measured first.

**Task (A3 sheet per team):**
1. Draw the architecture: cameras (USB/IP), switch/hub, SBC, tether, topside, browser. Mark **where each stream is encoded and decoded**.
2. For each camera: role, main/substream settings, codec, priority.
3. **Bandwidth budget:** total on the wire vs 70 % of measured (or assumed, labelled!) throughput, including control.
4. **Encoder budget:** pixel rate on each encoder vs its capacity (Jetson Nano ≈ 4× 1080p30 ≈ 249 Mpx/s; Pi 5 software — use your measured CPU per stream).
5. **Latency estimate** for the pilot camera, stage by stage.
6. **Failure handling:** camera loss, link loss, overload — what the system does and what the pilot sees.
7. **Top 3 assumptions** and the measurement that would validate each.

Use notebook Experiment 11 (`evaluate(design)`) to check the numbers.

**Rubric (20 points):**

| Criterion | Points |
|---|---|
| Encode/decode locations correct and explicit | 3 |
| Bandwidth budget correct, with overhead and headroom | 4 |
| Encoder capacity checked | 3 |
| Latency estimate stage by stage, with the dominant stage identified | 3 |
| Failure handling and honest UI states | 3 |
| Assumptions labelled + validation measurements | 4 |

---

## Activities 4 and 6

- **Activity 4 (testing competition):** full rules, scoring, templates and sample scenarios in `student_materials/Testing_Competition_Guide.md`. Referee key and proof tests: the presenter-only `referee/` folder in the presenter's Drive (not in the team repo).
- **Activity 6 (UX design competition):** scenario, tasks, roles and rubric in `ux_materials/UX_Pilot_Experience_Pack.md` §6.
