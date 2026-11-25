# 🩺 ROV Video Debug Checklist

*M.I.A Robotics · 25 Nov 2026 · the one page to open when the video misbehaves*

> **Don't guess. Check in order.** Video passes through a chain: **power → camera → ROV computer → encoder → tether → topside → screen → pilot**. Something broken early in the chain causes symptoms everywhere after it. Go down this list in order, and **the first ❌ is almost always the cause**.

**Contents:** [How to use it](#how-to-use-it) · [1 Write the symptom](#1-write-the-symptom) · [2 Symptom finder](#2-symptom-finder) · [3 The checklist (A–G)](#3-the-checklist) · [4 Symptom routes](#4-symptom-routes) · [5 Fix, re-measure, write it down](#5-fix-one-thing-re-measure-write-it-down) · [Numbers at a glance](#numbers-at-a-glance)

---

## How to use it

1. **Write the symptom** in one line (section 1). A clear symptom saves half the work.
2. **Run the automatic check on the ROV computer** (10 seconds):
   ```bash
   bash docs/debug/rov_healthcheck.sh --top 192.168.2.1 --cams 4      # your topside IP and camera count
   sudo bash docs/debug/rov_healthcheck.sh --top 192.168.2.1 --iperf   # + throughput (run `iperf3 -s` on the topside first)
   ```
   It checks power, heat, cameras, USB, CPU, memory, stream settings and the tether, and prints ✅ ⚠️ ❌ for each, with **what it means** and **what to do**. Its IDs (A1, B4, E7…) are the rows below. Add `--md` to get a table you can paste into a GitHub issue.
3. **Do the manual checks** the script cannot see: the topside (F) and the pilot's view (G).
4. **Follow the route for your symptom** (section 4) if the cause is still not clear.
5. **Change one thing, measure again, write it down** (section 5).

Don't have the script on the ROV? Every check below has its command; the whole checklist works by hand.

**Set these once** (they are used in the commands):

```bash
ROV=192.168.2.2   TOP=192.168.2.1   IF=eth0   CAM=/dev/video0
```

---

## 1. Write the symptom

| Question | Answer |
|---|---|
| What does the pilot see? (frozen, late, blocky, black, choppy, colours wrong…) | |
| Which cameras? (one / some / all) | |
| When? (from start / after N minutes / when thrusters run / after switching camera / in the pool only) | |
| Always, or sometimes? How often? | |
| What changed since it last worked? (code, cable, camera, settings, location) | |

The last question finds the cause more often than any tool.

---

## 2. Symptom finder

Find your symptom; do those checks first.

| What the pilot sees | Check first | Most likely causes |
|---|---|---|
| ⬛ **No picture at all** (one camera) | B1 · B2 · B5 · C4 | camera not detected, USB bandwidth, stream process crashed |
| ⬛ **No picture at all** (all cameras) | E1 · E4 · C4 · F3 | tether link down, wrong IP, streaming service stopped, player wrong port |
| 🧊 **Frozen picture, app still running** | C4 · B5 · E4 · E5 · F6 | encoder stuck or crashed, camera dropped off USB, network stopped |
| 🐢 **Picture is late** (always the same delay) | G1 · F3 · D4 · F5 · E4 | player buffer, encoder holding frames, TV processing, queueing |
| 📈 **Picture gets later and later** | G2 · D6 · C1 · F4 · A1 | TCP transport, receiver slower than the stream, CPU full, heat |
| 🧱 **Blocks or smears that clear after a moment** | E5 · E2 · E8 · D3 | packet loss, tether full, long keyframe interval |
| 🟩 **Green or grey garbage** | D5 · E5 · E6 | player joined without a keyframe, loss, fragmentation |
| 🧱 **Blocky only when moving** | D2 · B7 · E8 | bitrate too low, noise/backscatter wasting bits |
| 🎞️ **Choppy / low frame rate** | B6 · C1 · A2 · F4 · F1 | dark scene (long exposure), CPU, throttling, slow GUI |
| 🔌 **Camera disappears or resets** (often with thrusters) | B5 · A3 · A5 · B4 | power dips, loose cable, USB bandwidth |
| 🚫 **3rd (or 4th) camera won't start** | B2 · B4 · B5 | raw (YUYV) format, too many cameras on one USB 2 bus |
| 🕹️ **Thrusters feel slow when video is on** | E9 · E8 · E4 · C1 | control queued behind video, tether full, CPU full |
| 🌫️ **Bad image** (dark, green, blurry, foggy, specks) | B7 · B6 · D2 | exposure, white balance, focus, condensation, lights |
| 🏊 **Fine on the bench, fails in the pool** | A1 · A3 · E1 · E2 · G2 | heat in the closed hull, power under thrust, tether noise |
| 💾 **Recording won't play** | G6 · C3 | MP4 cut by a power loss, disk full |
| ⏱️ **Camera switch is slow** | G3 · D3 | long keyframe interval, reconnect on every switch |

---

## 3. The checklist

Tick each box. **🤖** = the health-check script does it for you. "Good" values are starting targets for a pilot camera.

### A · Power and heat

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **A1** 🤖 | Board temperature | Pi `vcgencmd measure_temp` · Jetson `sudo tegrastats` | < 70 °C with everything running | ≥ 80 °C the board slows itself down → heatsink touching the hull, fan, less software encoding. Test closed for 30 min (experiment E16) |
| ☐ **A2** 🤖 | Has it throttled? | Pi `vcgencmd get_throttled` · Jetson: clocks in `tegrastats` drop under load | `throttled=0x0` | Anything else: it slowed down at some point → see [the flags](#raspberry-pi-throttled-flags), then A1 or A3 |
| ☐ **A3** 🤖 | Under-voltage | Pi: bit 0 / bit 16 of `get_throttled` · `dmesg \| grep -i voltage` | none | The supply sags (usually when thrusters pull) → separate regulated 5 V for computer and cameras, thicker and shorter wires |
| ☐ **A4** 🤖 | Did it reboot? | `uptime` · `last -x reboot \| head` | up since you powered it | A reboot during the dive = power (A3) or a crash → check connectors and the kernel log |
| ☐ **A5** | Supply under thrust | Multimeter on the computer's 5 V input while reversing all thrusters | stays ≥ 4.9 V | Dips → brown-outs reset USB cameras (B5) → stronger supply, separate the thruster power |

### B · Cameras and USB

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **B1** 🤖 | Every camera detected | `v4l2-ctl --list-devices` | one entry per camera | Missing → reseat the cable, try another port, check B4 and B5. Swap cameras between ports to see if the fault follows the camera or the port |
| ☐ **B2** 🤖 | Format in use | `v4l2-ctl -d $CAM --get-fmt-video` | `MJPG` or `H264` | `YUYV` (raw) uses ~10× the USB bandwidth → set MJPG; a 3rd camera will not start otherwise |
| ☐ **B3** | Size and fps as planned | `--get-fmt-video` and `--get-parm` | matches your budget | Bigger → wasted bits and CPU; smaller or slower than asked → the camera fell back to another mode |
| ☐ **B4** 🤖 | USB bus speed and sharing | `lsusb -t` | each camera at `480M` or `5000M`; ≤ 2 MJPEG cameras per USB 2 bus | `12M` = camera behind a USB 1.1 hub → plug in directly. Many cameras on one bus → spread them over separate controllers |
| ☐ **B5** 🤖 | Kernel errors | `dmesg \| grep -Ei "usb.*(reset\|disconnect)\|uvcvideo\|no space"` | nothing new while streaming | `reset` / `disconnect` = power or cable (watch `dmesg -w` while thrusting). `No space left on device` = USB bandwidth (B2, B4) |
| ☐ **B6** | Real frame rate | `v4l2-ctl -d $CAM --stream-mmap --stream-count=300` (camera not in use) | equals the configured fps | Lower in a dark scene → auto-exposure makes frames longer → manual exposure (experiment E23) |
| ☐ **B7** | Lens, dome and image | Look at the picture and the dome | sharp, clean, no fog, natural colours | Fog = condensation → desiccant, seal in dry air. Soft = focus (auto-focus hunting) → fix focus. Specks = backscatter → move lights to the side (E22). Green/blue = white balance → manual WB (E23) |

### C · ROV computer

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **C1** 🤖 | CPU per core | `htop` or `mpstat -P ALL 1` | every core < 80 %, one core free | All high → too much software encoding/decoding → hardware encoder, camera's own H.264, fewer streams. One core at 100 % → a single-threaded stage is the bottleneck |
| ☐ **C2** 🤖 | Memory | `free -m` | > 20 % available, no swap in use | Falling over time = something keeps queuing frames (a leak) → find it in `htop` (sort by MEM) |
| ☐ **C3** 🤖 | Disk space | `df -h` | > 4 GB free where recordings go | Full disk stops recordings and can crash apps → clear old recordings before the dive |
| ☐ **C4** 🤖 | Video processes running | `ps aux \| grep -Ei "ffmpeg\|gst\|mediamtx\|ustreamer"` | one per stream, running for a long time | Missing = crashed. Started seconds ago = crash-restart loop → read the log: `journalctl -u <service> -n 50` |
| ☐ **C5** 🤖 | No pointless re-encoding | Read the pipeline | MJPEG/H.264 from the camera forwarded (`-c copy`) or encoded once | Decode → resize → encode on the CPU ([the resolution trap](../streaming/codecs-and-ffmpeg.md#the-resolution-trap)) → ask the camera for the size you want |

### D · The streams (what the encoder sends)

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **D1** | Codec, size, fps | `ffprobe -hide_banner <stream-url>` | as in your plan | Different → the wrong config file is being used |
| ☐ **D2** | Bitrate | `ffmpeg -hide_banner -i <stream-url> -f null -` (read `bitrate=`) | within ±10 % of the plan | Much higher → noise, backscatter or no rate control. Much lower → blocky when moving → raise it or lower the fps/size |
| ☐ **D3** 🤖 | Keyframe interval (GOP) | `ffprobe -v error -show_entries frame=pict_type -of csv=p=0 rec.mkv \| head -120` (count frames between `I`) | 0.5–1 s (15–30 frames at 30 fps), or intra refresh | Long GOP → loss damage lasts longer, camera switch is slow → `-g 30` |
| ☐ **D4** 🤖 | Low-latency encoder | Read the pipeline | x264: `-tune zerolatency -bf 0` · Jetson: `maxperf-enable=1`, no B-frames | Missing → the encoder holds ~30–40 frames (≈ 1 s!) before sending anything |
| ☐ **D5** 🤖 | Picture on join | Start the player after the stream is running | picture within ~1 s | Green/grey until the next keyframe → send SPS/PPS with every keyframe (`insert-sps-pps=1`, `-x264-params repeat-headers=1`); shorter GOP |
| ☐ **D6** 🤖 | Transport | Read the URLs: `rtsp_transport`, `udp://`, `protocols=` | UDP / RTP for the live view | TCP → after any loss the delay grows and never comes back ([latency drift](../streaming/measure-and-diagnose.md#latency-drift)) |

### E · Tether and network

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **E1** 🤖 | Link speed and duplex, **both ends** | `ethtool $IF` | expected speed (100 or 1000), `Full` | `10` / `100` / `Half` → a broken pair or connector in the tether, or a slow switch port ([wrong link speed](../streaming/measure-and-diagnose.md#link-at-the-wrong-speed)) |
| ☐ **E2** 🤖 | Interface errors | `ethtool -S $IF \| grep -Ei "err\|crc\|drop"`, before and after 1 min | not increasing | Rising CRC / errors = electrical noise or a bad pair → test with thrusters off and on; reroute or shield the tether |
| ☐ **E3** 🤖 | Real throughput | topside `iperf3 -s` · ROV `iperf3 -c $TOP -t 30` | ≥ 90 % of the link speed | Lower → E1, E2. **This number is your real budget** |
| ☐ **E4** 🤖 | Round trip | `ping -c 100 -i 0.2 $TOP` | 0 % loss, avg < 2 ms, max < 10 ms | Spikes only while video runs → packets wait behind video (E8, E9). Loss → E1, E2 |
| ☐ **E5** | Loss per stream | `python3 encoding_lab/tools/rtp_probe.py --port 5600 --forward 5601` | 0 % loss, jitter < 5 ms | Loss → smears until the next keyframe ([packet loss](../streaming/measure-and-diagnose.md#packet-loss-artifacts)) → find where: E2, E8, socket buffers |
| ☐ **E6** 🤖 | Packet size fits | `ping -M do -s 1472 -c 3 $TOP` | works | Fails → the path MTU is below 1500 and big packets get fragmented → RTP payload 1200–1400 bytes (`pkt_size=1316`) |
| ☐ **E7** 🤖 | No leftover test rules | `tc qdisc show dev $IF` | no `netem`, no `tbf` | Someone forgot a Chaos Monkey rule → `sudo tc qdisc del dev $IF root` |
| ☐ **E8** 🤖 | Tether use | `sar -n DEV 1 10` | ≤ 70 % of E3 | Above → keyframe bursts hit the ceiling and packets drop → lower bitrates or cameras (Encoding Lab → *Bandwidth budget*) |
| ☐ **E9** | Control survives video | Drive the thrusters with all video running | instant response | Lag → control waits behind video → give control priority (separate port and DSCP), cap the video |

### F · Topside and display (manual)

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **F1** | Laptop CPU / GPU | Task Manager or `htop`, all streams on | < 70 % | High → software decoding of many streams → hardware decoding (F2), smaller substreams for the small tiles |
| ☐ **F2** | Hardware decoding | Chrome: `chrome://gpu` (*Video Decode: Hardware accelerated*), `chrome://media-internals` | hardware | Software → update drivers, check browser flags; fewer decoders |
| ☐ **F3** 🤖 | Player buffer | Player settings | jitter buffer ≤ 50 ms; VLC not at its 1000 ms default | Big buffer = constant delay → `ffplay -fflags nobuffer -flags low_delay -framedrop`; GStreamer `rtpjitterbuffer latency=50` |
| ☐ **F4** | GUI fps = stream fps | GUI fps counter vs D1 | equal | Lower → the GUI cannot draw fast enough (one thread, image copies) → profile the GUI |
| ☐ **F5** | Screen | TV or monitor settings | TV in **Game mode**, ≥ 60 Hz | TV picture processing adds 50–150 ms → game mode or use the laptop screen |
| ☐ **F6** | Honest UI | Freeze one encoder: `kill -STOP <pid>` (then `kill -CONT <pid>`) | STALE warning within 0.5 s | A frozen frame that looks live → add "time since last frame" to the GUI ([frozen frame](../streaming/measure-and-diagnose.md#frozen--stale-frame)) |
| ☐ **F7** | Clocks in sync (only for timestamp measurements) | `timedatectl` · `chronyc tracking` | synchronised | Wrong per-stage numbers → chrony on both ends ([clock drift](../streaming/measure-and-diagnose.md#clock-drift-bad-measurements)) |

### G · What the pilot feels (end to end, manual)

| ☐ ID | Check | How | ✅ Good | ❌ If not: cause → fix |
|---|---|---|---|---|
| ☐ **G1** | Glass-to-glass latency | Phone photo of [ms_clock.html](../experiments/ms_clock.html) and its video, 10 times | median ≤ 150 ms, worst ≤ 250 ms | Above → the usual suspects in order: F3 player buffer, D4 encoder, F5 TV, E4 queueing |
| ☐ **G2** | Latency drift | G1 at 1 min and at 10 min | same ± 20 ms | Grows → a queue only grows: D6 TCP, F4 slow GUI, C1 CPU, A1 heat |
| ☐ **G3** | Camera switch time | Slow-motion film of key press and screen | ≤ 1 s | Slow → D3 GOP, a reconnect on every switch |
| ☐ **G4** | Recovery | Unplug the tether for 1 s | picture back within 2 s, nothing restarted | Not → no reconnect logic, D6 TCP, D3 GOP |
| ☐ **G5** | Can the pilot read it? | Eye chart at 1 m under water (experiment E24) | the smallest mission marking is readable | Not → D2 bitrate, B7 focus, lights, exposure |
| ☐ **G6** | Recording survives a power cut | `kill -9` the recorder, then `ffprobe` the file (E15) | the file plays | Plain MP4 lost → record MKV or fragmented MP4 (`-movflags +frag_keyframe+empty_moov`) |

---

## 4. Symptom routes

Go down the steps. At the first **❌**, you have found it: apply the fix, then check the symptom again.

### ⬛ No picture at all

1. **All cameras or one?** All → step 2. One → step 5.
2. **E1** link up at the right speed? ❌ → tether, connector, topside switch.
3. **E4** ping the ROV from the topside? ❌ → IP addresses (`ip -br addr` on both), laptop firewall, wrong network adapter.
4. **C4** streaming processes running? ❌ → start the service; read its log. ✅ → **F3** is the player listening on the right port / URL?
5. **B1** camera detected? ❌ → cable, port, power. ✅ → **B5** errors? `No space left on device` → **B2 / B4** USB bandwidth.
6. **C4** its stream process running? ❌ → it crashed: read its log (often "device busy": two programs opened the same camera).

### 🧊 Frozen picture, app alive

1. **C4** is the process for that camera still running, and not just restarted? ❌ → it crashed: read its log.
2. **B5** kernel errors at the moment it froze? ❌ → the camera dropped off USB → power (**A3**, **A5**) or cable.
3. **E4** ping still works? ❌ → the link dropped → **E1**, **E2**.
4. **E5** packets still arriving at the topside? **No** → the sender is stuck (**C1** CPU, **A2** throttling). **Yes** → the receiver or decoder stopped → restart the player, read its log.
5. **F6** did the GUI warn the pilot? No → open an issue: a frozen picture that looks live is the most dangerous video bug.

### 🐢 Picture is late (same delay all the time)

1. **G1** measure it. ≤ 150 ms → it is within target; the pilot may be reacting to something else (e.g. control lag, **E9**).
2. **F3** player buffer > 50 ms or VLC default caching? ❌ → cut it. *(Most common cause.)*
3. **D4** encoder low-latency settings missing? ❌ → `-tune zerolatency -bf 0`. *(Second most common: up to 1 s.)*
4. **F5** TV not in game mode? ❌ → game mode or laptop screen.
5. **E4** ping max > 10 ms while video runs? ❌ → queueing → **E8**.
6. Still late → do experiment **E2** (*Where do the milliseconds go?*): change one stage at a time.

### 📈 Picture gets later during the dive

1. **G2** confirm it: measure at 1 and 10 minutes.
2. **D6** any stream over TCP? ❌ → UDP/RTP. *(TCP never catches up after a loss.)*
3. **F4** GUI fps lower than stream fps? ❌ → the GUI falls behind and frames pile up → drop old frames, show only the newest.
4. **C1 / A1 / A2** CPU full, hot or throttled after a while? ❌ → cooling, less encoding.
5. **C2** memory falling while delay grows? ❌ → a queue with no limit → limit it and drop frames.

### 🧱 Blocks, smears, green or grey patches

1. **E5** loss on that stream? ✅ (no loss) → step 5.
2. **E2** interface errors rising (especially with thrusters)? ❌ → tether noise.
3. **E8** tether above 70 %? ❌ → lower bitrates, fewer cameras.
4. **E6** large packets blocked? ❌ → smaller RTP payload.
5. No loss but still blocky → **D2** bitrate too low for the scene, **B7** noise or backscatter wasting bits.
6. Green until a keyframe after joining → **D5** SPS/PPS; long damage → **D3** shorter GOP.

### 🎞️ Choppy / low frame rate

1. **B6** the camera itself delivers fewer fps (dark water)? ❌ → manual exposure.
2. **C1** a core at 100 %? ❌ → hardware encoder, no re-encoding (**C5**).
3. **A1 / A2** hot or throttled? ❌ → cooling.
4. **F4 / F1** stream fps fine but GUI slow? ❌ → topside decoding/drawing → **F2** hardware decoding.

### 🔌 Camera disappears, resets, or the 3rd camera won't start

1. **B5** read the kernel log while it happens (`dmesg -w`).
   - `No space left on device` → **B2** use MJPEG, **B4** spread cameras over buses, or lower fps/size.
   - `reset` / `disconnect` → step 2.
2. **A3 / A5** voltage dips when thrusters run? ❌ → separate supply for computer and cameras.
3. Wiggle the cable while watching `dmesg -w`: messages → replace the cable or add strain relief.

### 🕹️ Thrusters feel slow when video is on

1. **E9** compare control response with video off and on. Same → not a video problem.
2. **E4** ping max jumps with video on? ❌ → control waits in the same queue as video.
3. **E8** tether above 70 %? ❌ → lower video bitrate.
4. **C1** CPU full on the ROV? ❌ → the control process is starved → give it priority (`nice`), reduce encoding.

### 🏊 Fine on the bench, fails in the pool

1. **A1 / A2** after 20–30 min with the hull closed? → heat ([the 2023 heat failure](../streaming/hardware-and-encoders.md#4-reliability-the-2023-heat-failure-and-how-to-prevent-it)).
2. **A3 / A5 / B5** only when thrusters run? → power.
3. **E1 / E2** link speed or errors different with the full tether and thrusters? → tether noise or a damaged pair.
4. **B7** fog on the dome after a while? → condensation.

---

## 5. Fix one thing, re-measure, write it down

- **One change at a time.** Two changes at once and you never know which one worked.
- **Measure again** with the same check that failed. "It looks better" is not a measurement.
- **Write it down** in a GitHub issue, so nobody debugs the same thing twice:

```markdown
**Symptom:** (section 1, one line)
**Conditions:** bench / pool · hull open / closed · cameras streaming · thrusters on/off · software version
**Health check:** (paste the output of rov_healthcheck.sh --md)
**Failed checks:** e.g. B5 (12 USB resets), A3 (under-voltage since boot)
**Cause:** what you believe and why
**Change made:** one change
**After:** the same check again → result
```

If the problem was new, add a row to this checklist or a symptom route. That is how it gets better.

---

## Numbers at a glance

| What | ✅ Good | ⚠️ Look at it | ❌ Problem |
|---|---|---|---|
| Board temperature (A1) | < 70 °C | 70–80 °C | ≥ 80 °C |
| `get_throttled` (A2, A3) | `0x0` | — | anything else |
| CPU, all cores (C1) | < 70 % | 70–85 %, or one core ≥ 95 % | ≥ 85 % |
| Memory available (C2) | > 20 % | 10–20 % | < 10 % |
| Cameras per USB 2 bus, MJPEG (B4) | ≤ 2 | 3 | 4+ or any at 12M |
| Keyframe interval (D3) | 0.5–1 s | > 1 s (the script flags > 2 s) | — |
| Encoder frames held (D4) | 0 | — | > 0 on a live stream |
| Link (E1) | expected speed, Full | — | lower, or Half |
| Throughput (E3) | ≥ 90 % of link | 50–90 % | < 50 % |
| Ping on the tether (E4) | avg < 2 ms, max < 10 ms | max 10–30 ms | any loss, or max > 30 ms |
| Stream loss (E5) | 0 % | < 0.1 % | ≥ 0.1 % |
| Tether use (E8) | ≤ 70 % | 70–85 % | > 85 % |
| Player buffer (F3) | ≤ 50 ms | 50–200 ms | > 200 ms |
| Glass-to-glass (G1) | ≤ 150 ms median, ≤ 250 ms worst | 150–250 ms | > 250 ms |
| Drift over 10 min (G2) | ± 20 ms | — | growing |
| Camera switch (G3) | ≤ 1 s | 1–2 s | > 2 s |
| Recovery after 1 s unplug (G4) | ≤ 2 s, by itself | — | needs a restart |

### Raspberry Pi throttled flags

`vcgencmd get_throttled` returns a hex number. `0x0` means nothing ever happened. Otherwise:

| Bit | Value | Meaning |
|---|---|---|
| 0 | `0x1` | under-voltage **now** |
| 1 | `0x2` | CPU frequency capped **now** |
| 2 | `0x4` | throttled **now** |
| 3 | `0x8` | soft temperature limit **now** |
| 16 | `0x10000` | under-voltage happened since boot |
| 17 | `0x20000` | frequency capping happened since boot |
| 18 | `0x40000` | throttling happened since boot |
| 19 | `0x80000` | soft temperature limit happened since boot |

Example: `0x50005` = under-voltage now and throttled now, and both have happened since boot. Fix the power first.

---

**Related:** [Measure and diagnose](../streaming/measure-and-diagnose.md) (every metric, and the 45-problem field guide with pictures) · [ROV experiments](../experiments/ROV_Experiments.md) (practise each check as an experiment) · [Hardware and encoders](../streaming/hardware-and-encoders.md) · [Cheat sheet](../../workshop/student_materials/Video_Streaming_Cheat_Sheet.md)

*Tests for the script's parsers: `bash docs/debug/test_healthcheck.sh`.*
