# Workshop Design — "Engineering Better ROV Systems"

*Phase 1 output. Read this before the Presenter Script: it fixes the audience, the agenda, the learning objectives, the equipment, and — most importantly — the list of things we do **not** yet know about the M.I.A Robotics ROV.*

---

## 1. Target audience

| Group | Typical background | What they need from the session |
|---|---|---|
| Software / web team | JavaScript/TypeScript, React or similar, some Python | How video actually moves through their app; why "lower the resolution" is a blunt tool; testing and review habits |
| Embedded / electronics team | C/C++, microcontrollers, Linux on the SBC | Encoder hardware on Jetson / Pi, USB and Ethernet limits, measuring CPU/thermal load |
| Pilots and mission leads | Mixed; may be mechanical engineers | Latency, situational awareness, what a good pilot UI must show; how to write requirements |
| New members | First- or second-year students | Intuition for bandwidth and compression; how a team organizes work |

Design consequence: every technical topic is introduced **intuition → picture → numbers → measurement**. Nobody needs prior codec knowledge. Advanced students get depth through the Encoding Lab (Sweep, Benchmark, Live camera) and the "go deeper" boxes in the cheat sheet.

Recommended group size: 12–30 students, in teams of 3–5 (mixed experience in every team).

---

## 2. Learning objectives

By the end of the session a student should be able to:

1. **Trace a frame** from the camera sensor to the pilot's screen and name where it is encoded, packetized, buffered, decoded and rendered.
2. **Distinguish** codec vs. container vs. transport protocol, and bitrate vs. bandwidth vs. throughput vs. FPS vs. latency.
3. **Calculate** raw and compressed bandwidth for N cameras and judge whether a tether link has enough headroom.
4. **Explain** how H.264/H.265 compress video (prediction, transform, quantization, entropy coding, GOP) well enough to predict what a parameter change will do.
5. **Run FFmpeg/ffprobe** to encode, inspect and quality-score a stream (PSNR/SSIM/VMAF), and read the results critically.
6. **State correctly** what the Jetson Nano and the Raspberry Pi 5 can and cannot do in hardware.
7. **Investigate** their own ROV with a diagnostic checklist, producing measurements instead of guesses.
8. **Write** a user story with acceptance criteria and a Definition of Done for an ROV feature.
9. **Design and execute** test cases (boundary, negative, stress) and write a reproducible bug report.
10. **Review** code constructively using a checklist.
11. **Apply** UX principles (information hierarchy, cognitive load, feedback, error prevention) to the pilot dashboard and validate a design with a usability test.

The over-arching outcome: **students leave asking "how would we measure that?" before "how do we fix that?"**

---

## 3. Agenda

The full content is about **7 h 45 min including breaks** (≈ 7 h of contact time). Recommended delivery is **two half-day sessions** (attention drops sharply after ~3.5 h of technical content). A compressed one-day version is given after.

### Option A (recommended) — two sessions

**Session 1 — Video Engineering (≈ 3 h 50 min incl. two 10-min breaks)**

| Time | Block | Format | Deck slides |
|---|---|---|---|
| 0:00 | Opening: why video is the ROV's most important sensor; MATE | Talk + question | 1–5 |
| 0:10 | Underwater video; their architecture and the unknowns; A/B/C architectures; following a frame; codec vs container vs protocol | Talk + whiteboard | 6–12 |
| 0:40 | Bandwidth engineering + **Activity 1: Estimate the Bandwidth** (15 min) | Talk + activity | 13–18 |
| 1:10 | *Break 10 min* | | |
| 1:20 | How encoding works (YUV, prediction, transform, quantization, GOP) | Talk | 19–23 |
| 1:50 | CRF vs bitrate, codecs, parameters, presets, packet loss — **Encoding Lab live (Encode, Sweep, Packet loss)** | Talk + demo | 24–27 |
| 2:20 | *Break 10 min* | | |
| 2:30 | Quality metrics + **Activity 3: Compression Challenge** | Activity | 28 |
| 2:50 | Hardware (Jetson Nano vs Pi 5), where to encode, protocols, latency | Talk | 29–35 |
| 3:15 | Main/substreams, priorities, measurement toolbox, **Activity 2: Diagnose the ROV**, strategy, homework | Talk + team activity | 36–41 |

**Session 2 — Engineering Practice and the Pilot (≈ 3 h 55 min incl. one 10-min break)**

| Time | Block | Format | Deck slides |
|---|---|---|---|
| 0:00 | Recap + results of the diagnostic homework | Discussion | — |
| 0:10 | SDLC, requirements, epic → test case, DoR/DoD | Talk + mini-exercise | 42–47 |
| 0:40 | Testing levels, techniques, mindset | Talk | 48–49 |
| 0:50 | **Activity 4: Break the Other Team's Software** (incl. debrief) | Competition (60 min) | 50 |
| 1:50 | *Break 10 min* | | |
| 2:00 | Code review (live bad → good review), Git, board, metrics | Talk + pair review | 51–55 |
| 2:25 | UX for ROV pilots | Talk | 56–65 |
| 3:00 | **Activity 6: Design the Perfect ROV Pilot Experience** | Competition (40 min) | 66 |
| 3:40 | Final challenge (**Activity 5** briefing / live if time), takeaways, close | Talk | 67–70 |

### Option B — one long day (≈ 6 h 30 min + breaks)

Cut: Experiment 4 (presets) becomes a pre-recorded result; Activity 3 shortened to 10 min; testing competition reduced to 45 min; UX activity reduced to 30 min with paper wireframes only; Architecture Challenge assigned as homework only.

---

## 4. Required equipment

| Item | Required? | Notes |
|---|---|---|
| Projector + presenter laptop with the `.pptx` | Required | Deck uses only built-in fonts (Segoe UI/Calibri fallback) |
| Presenter laptop with Python 3.10+, FFmpeg 5+ and the Encoding Lab | Required | Run the Encoding Lab once the night before; outputs are cached in `encoding_lab/.lab_work/` |
| Student laptops (1 per team minimum) | Required for activities | the Encoding Lab is optional for students; activities work on paper |
| Paper, sticky notes, markers, A3 sheets | Required | Wireframing and bug reports |
| A timer visible to the room | Required | Competitions |
| **The real ROV + tether + topside laptop** | Strongly recommended | Turns the diagnostic section from theory into measurement |
| One USB camera (UVC) + one IP camera, if they have them | Recommended | Live `v4l2-ctl` / `ffprobe` demo |
| Jetson Nano and/or Raspberry Pi 5 with SSH | Recommended | run the Encoding Lab's Benchmark tab on the board |
| A small managed or unmanaged Ethernet switch | Optional | Show link speed negotiation with `ethtool` |
| A phone with a camera (high-speed mode helps) | Optional | Glass-to-glass latency measurement |

---

## 5. Activities overview

| # | Activity | When | Duration | Output | Scoring |
|---|---|---|---|---|---|
| 1 | Estimate the Bandwidth | Session 1, bandwidth block | 15 min | Filled worksheet | Accuracy + headroom judgement |
| 2 | Diagnose the ROV | End of Session 1 | 20 min | Ranked hypothesis list + measurement plan | Quality of measurements proposed |
| 3 | Compression Challenge | After quality metrics | 15 min | Blind ranking of encodings | Closeness to measured ranking |
| 4 | Break the Other Team's Software | Session 2 | 60 min | Bug reports, fixes, regression tests | Defect points (see Testing Competition Guide) |
| 5 | Architecture Challenge | Session 2 close / homework | 20 min + homework | Architecture proposal with numbers | Rubric |
| 6 | Design the Perfect ROV Pilot Experience | Session 2 | 40 min | Wireframe + usability test results | UX rubric |

Full instructions: `workshop_activities/Activity_Instructions.md`, `student_materials/Testing_Competition_Guide.md`, `ux_materials/UX_Pilot_Experience_Pack.md`.

---

## 6. What we know, what we assume, what we must find out

This table is the backbone of the honest framing of the workshop. **Say it out loud in the session**: "I don't know your system yet. Here is what I'm assuming, and here is how we'll find out."

### 6.1 Confirmed (from the brief)

- Onboard computer is an NVIDIA Jetson Nano **or** a Raspberry Pi 5.
- Up to 8 cameras.
- An Ethernet tether connects the ROV to a surface laptop.
- A web application displays the camera streams and provides control (PID tuning, RC configuration, etc.).
- The team reduces camera resolution to fit within bandwidth.
- The team appears to stream all cameras continuously.

### 6.2 Contradiction in the brief that must be resolved first

The brief says **"USB cameras connected through network hubs/switches"** and also draws **"IP Cameras → Network Switch"**. These are two physically different systems:

| | USB (UVC) cameras | IP cameras |
|---|---|---|
| Connects to | SBC USB port, often via a USB hub | Ethernet switch |
| Who encodes | Camera may output raw YUYV, MJPEG, or (some models) H.264 — the SBC usually re-encodes or forwards | Camera almost always encodes H.264/H.265 itself |
| Shared bottleneck | **USB bus bandwidth** of the hub/root port | **Switch uplink** and the tether |
| How to identify | `lsusb`, `v4l2-ctl --list-devices` | `nmap`/`arp -a`, the camera's web page, `ffprobe rtsp://...` |

It is common for a student ROV to have a **mix**. The first diagnostic step is to find out which they have.

### 6.3 Assumptions used in the material (clearly labeled wherever used)

- The tether link negotiates **100 Mb/s or 1 Gb/s** Ethernet. (Long or thin tethers frequently fall back to 100 Mb/s — this must be measured with `ethtool`.)
- The topside laptop is a typical x86 laptop with an integrated GPU.
- The web application runs in a Chromium-based browser.

### 6.4 Hypotheses (to be tested, never stated as fact)

- H1: Resolution was reduced because of a *perceived* bandwidth problem that may actually be a USB-bus, CPU or decoding problem.
- H2: Cameras stream continuously at the same quality whether or not the pilot is looking at them.
- H3: Streams may be MJPEG (common for USB cameras and simple web streaming), which is ~5–10× less efficient than H.264 at the same quality.
- H4: Latency may be dominated by buffering in the player/browser rather than by the network.

### 6.5 Information to collect before (or during) the session

Ask the team lead to fill this in. Each answer changes the recommendations.

1. Exact camera models (USB or IP? UVC formats supported?).
2. Which SBC is actually used in the competition vehicle, and which JetPack / Raspberry Pi OS version.
   - **Warning:** "Jetson Nano" (2019, Maxwell, *has* a hardware encoder) and "Jetson **Orin** Nano" (2023, *no* hardware encoder) are often confused. Check `cat /etc/nv_tegra_release` or the module label.
3. Tether: cable type, length, whether it uses Ethernet extenders/powerline/VDSL adapters, negotiated link speed.
4. Switch/hub models (managed? 100 Mb/s or 1 Gb/s ports? USB 2.0 or 3.x hub?).
5. Streaming software on the SBC (mjpg-streamer, GStreamer, FFmpeg, MediaMTX, ustreamer, OpenCV + Flask, custom…).
6. Protocol to the browser (MJPEG over HTTP, WebRTC, HLS, WebSocket + JS decoder…).
7. Current resolution, FPS and (if known) bitrate per camera.
8. Typical observed problems: freezes, lag, dropped cameras, high CPU, overheating.
9. How the control channel shares the tether with video (same link? priority?).
10. Who the pilots are and what their top three complaints are.

---

## 7. Design principles for the whole workshop

1. **Every concept is tied to their ROV.** No codec theory without a "so on your vehicle this means…".
2. **Measure, don't assume.** Every recommendation is paired with the command that verifies it.
3. **Honesty about uncertainty.** Hardware claims are cited; architecture claims are labeled as assumptions.
4. **Activities every 20–30 minutes.** Long lectures lose a student audience.
5. **Lightweight process.** Everything in Part C must be runnable by a student team in < 1 hour/week of overhead.
6. **The pilot is the customer.** The UX part closes the loop: the video system exists to serve a human making decisions under pressure.
