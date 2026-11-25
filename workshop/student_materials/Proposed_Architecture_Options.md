# Proposed Improved Architectures — Options and Trade-offs

> **Read this first.** None of these is a prescription. Which option is right depends on facts we have not yet measured: whether the cameras are USB or IP, which board flies (Jetson Nano, Orin Nano or Raspberry Pi 5), the tether's negotiated speed, the pilot laptop, and the browser. Run the experiments in `docs/experiments/ROV_Experiments.md` first (at least E0, E1, E6, E7, E16, E18), then use this document to compare options **with your numbers**.

Notation: **E** = where encoding happens · **D** = where decoding happens · Mb/s figures are illustrative (from the workshop's synthetic clip) — replace with your measurements.

---

## Common building blocks (useful in every option)

1. **Roles and priorities per camera** — pilot, manipulator, inspection, rear, aux. Priorities can change with the mission phase.
2. **Main stream + substream per camera** — full quality only where the pilot is looking; thumbnails elsewhere.
3. **Live encoding settings** — H.264, capped bitrate (VBV), `zerolatency`-style settings (no B-frames, no lookahead), GOP ≈ 0.5–1 s *or* intra refresh, keyframe on request.
4. **Low-latency transport to the browser** — RTP/UDP into a media server that offers **WebRTC** (e.g. MediaMTX), or WebRTC directly. Small jitter buffer. Never HLS for piloting.
5. **Central stream manager** — one component (on the SBC or topside) that knows every stream's state, measures throughput, allocates bitrate by priority, pauses/resumes streams, requests keyframes, and publishes camera states to the UI.
6. **Failure handling** — automatic reconnection with back-off; per-camera watchdog (no frames for > 1 s → LOST); link watchdog → ROV safe state + UI banner; control traffic protected from video (separate process, separate port, ideally prioritised).
7. **Recording** — record the primary stream separately (on the ROV's storage or topside) so recording quality never competes with live latency.

---

## Option 1 — Cameras encode (IP cameras or H.264-capable UVC cameras)

```
[IP cam ×8: H.264 main + sub] → [switch] → [tether] → [topside: media server → WebRTC] → [browser]
                                      ↘ [SBC: control, telemetry, stream manager (optional)]
```
- **E:** in each camera · **D:** topside browser.
- **Pros:** no SBC encode load; substreams usually built in; scales to 8 cameras; SBC free for control and vision.
- **Cons:** camera encoders vary in quality and latency (some add hundreds of ms); you depend on each camera's settings API (HTTP/ONVIF); more power and space for IP cameras.
- **Watch:** camera GOP/latency settings; whether the camera supports runtime bitrate change; switch uplink capacity.
- **Fits when:** IP cameras already in use, or you can source small IP/H.264 cameras.

## Option 2 — Jetson Nano hardware encoding

```
[USB cams: MJPEG/YUYV] → [USB (spread across controllers)] → [Jetson Nano: HW JPEG decode → NVENC H.264 main+sub] → [tether] → [media server → WebRTC] → [browser]
```
- **E:** Jetson Nano's hardware encoder via GStreamer (`nvv4l2h264enc`) · **D:** browser.
- **Budget:** encoder ≈ 4× 1080p30 ≈ 9× 720p30 (≈ 249 Mpx/s). Example fit: 1× 1080p30 main + 1× 720p30 main + 6× 640×360@15 subs ≈ 62 + 28 + 21 = **111 Mpx/s** ✔.
- **Pros:** low CPU; predictable; cheap USB cameras.
- **Cons:** MJPEG must be decoded first (use the hardware JPEG path); USB bus limits; JetPack 4.x (older Ubuntu); upstream FFmpeg can't use the encoder — GStreamer or the Multimedia API.
- **Watch:** `tegrastats` under full load, USB topology (`lsusb -t`), heat in the enclosure.
- **Not applicable to:** Jetson **Orin** Nano (no hardware encoder).

## Option 3 — Raspberry Pi 5 software encoding, few full-quality streams

```
[USB cams] → [Pi 5: libx264 ultrafast/zerolatency for 1–2 main streams; MJPEG passthrough or very low-res H.264 for the rest] → [tether] → [browser]
```
- **E:** Pi 5 CPU (libx264) · **D:** browser.
- **Budget (estimate, measure yours):** ~0.6–0.9 core per 1080p30 low-latency stream (Raspberry Pi white paper); keep ≥ 1 core free for control → **≈ 2–3 × 1080p30, or more at 720p/360p**.
- **Pros:** simple stack (FFmpeg/GStreamer), modern OS, fast CPU.
- **Cons:** no hardware encoder; MJPEG decode costs CPU too; thermal throttling in a sealed hull; 8 full-quality streams are not realistic.
- **Variant:** cameras that output H.264 over UVC → Pi only forwards (`-c copy`), no encode cost.

## Option 4 — Selective streaming (any hardware)

```
[8 cameras] → only the 1–2 cameras the pilot needs are streamed at full quality; others as 1–5 fps thumbnails or paused
```
- **E/D:** as in options 1–3.
- **Pros:** the biggest bandwidth and CPU saving of all; works with weak hardware.
- **Cons:** switching latency (start a stream → wait for an I-frame); risk of missing events on unwatched cameras.
- **Mitigations:** keep tiny substreams running (instant switch); request a keyframe on switch; show "PAUSED" honestly; let the pilot pin cameras.

## Option 5 — Adaptive bitrate with a stream manager (layer on top of 1–4)

- Measure throughput/loss (RTCP receiver reports, WebRTC stats); budget = 70 % − control; allocate by priority; change encoder bitrates at runtime; pause lowest priorities first.
- **Pros:** graceful degradation when the tether misbehaves; protects the pilot view.
- **Cons:** more software; needs encoders with runtime bitrate control; must be tested carefully (oscillation, hysteresis).
- **Start simple:** a fixed table of "profiles" (normal / degraded / emergency) switched by measured loss, before any continuous controller.

---

## Comparison (fill in with your measurements)

| Criterion | Opt 1 Cameras encode | Opt 2 Nano HW | Opt 3 Pi 5 SW | Opt 4 Selective | Opt 5 Adaptive |
|---|---|---|---|---|---|
| Onboard CPU load | low | low | **high** | lower | + small |
| Max full-quality streams | 8 (camera-dependent) | ~4× 1080p30-equivalent | ~2–3× 1080p30 | 1–2 by design | same as base |
| Tether bandwidth | depends on settings | depends on settings | depends on settings | **lowest** | **adapts** |
| Latency risk | camera encoder | low | CPU contention | switching | controller tuning |
| Hardware change? | IP/H.264 cameras | none if Nano | none if Pi 5 | none | none |
| Software effort | low–medium | medium (GStreamer) | low–medium | medium | medium–high |
| Main risk | camera quirks | USB + heat | heat + CPU | missed events | complexity |

**Decision log template**

```markdown
## DEC-<n>: <decision title>
- Date / authors:
- Context (with measurements):
- Options considered (with numbers):
- Decision:
- Why (which requirement / measurement decided it):
- Consequences / risks:
- How we will verify it:
```
