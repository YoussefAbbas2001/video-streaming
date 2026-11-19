# ROV Video System — Diagnostic Checklist

**Purpose:** find out what your video system *actually* does — with measurements, not memory. Fill this in before changing anything. "Unknown" is an acceptable answer; it becomes a task.

**How to use:**
1. Each subsystem owner fills in their section (owner in the header of each section).
2. Record the **command you ran** and the **value you got**, with date and conditions (bench / pool, enclosure open / closed, how many cameras streaming).
3. Bring it to the next team meeting. Every "surprise" becomes a backlog item.

Vehicle / software version: ________  Date: ________  Filled in by: ________  Conditions: ☐ bench ☐ pool ☐ enclosure closed ☐ thrusters running

---

## 1. Onboard computer (owner: ________)

| # | Check | How | Result |
|---|---|---|---|
| 1.1 | Exact board | `cat /proc/device-tree/model` | |
| 1.2 | Jetson: L4T / JetPack version (R32 = Jetson Nano; R35/R36 = Orin) | `cat /etc/nv_tegra_release` | |
| 1.3 | Pi: OS release | `cat /etc/os-release` | |
| 1.4 | Hardware encoder actually usable? | Jetson: `gst-inspect-1.0 nvv4l2h264enc` · any: 1-s test encode | ☐ yes ☐ no |
| 1.5 | CPU load with **all** cameras streaming (per core) | `htop` (screenshot) | |
| 1.6 | Memory use with all cameras | `free -m` | |
| 1.7 | Temperature after 15 min, enclosure **closed** | Pi: `vcgencmd measure_temp` · Jetson: `tegrastats` | |
| 1.8 | Throttling occurred? | Pi: `vcgencmd get_throttled` (0x0 = never) · Jetson: `tegrastats` clocks | |
| 1.9 | Power supply stable under thruster load? | `dmesg -w` while running thrusters (under-voltage, USB resets) | |
| 1.10 | Which processes handle video? | `ps aux \| grep -Ei "ffmpeg\|gst\|mjpg\|ustreamer\|mediamtx\|python"` | |

## 2. Cameras (owner: ________) — one row per camera

| # | Camera (position/role) | Model | USB or IP? | Output formats supported | Format in use | Resolution | FPS | Who encodes? (camera / SBC / nobody) |
|---|---|---|---|---|---|---|---|---|
| C1 | | | | | | | | |
| C2 | | | | | | | | |
| C3 | | | | | | | | |
| C4 | | | | | | | | |
| C5 | | | | | | | | |
| C6 | | | | | | | | |
| C7 | | | | | | | | |
| C8 | | | | | | | | |

How:
- USB: `v4l2-ctl --list-devices`, `v4l2-ctl -d /dev/videoN --list-formats-ext`, `v4l2-ctl -d /dev/videoN --get-fmt-video`.
- IP: camera web page (encoding settings), `ffprobe -hide_banner rtsp://<ip>/<path>`.

Additional checks:

| # | Check | How | Result |
|---|---|---|---|
| 2.1 | USB topology: which cameras share a bus/hub, and at what speed (480M = USB 2.0, 5000M = USB 3) | `lsusb -t` | |
| 2.2 | Do all cameras start reliably every time? (try 10 power cycles) | count failures; `dmesg` | __ / 10 |
| 2.3 | Does any camera support **H.264 output** (UVC) or substreams (IP)? | `--list-formats-ext` / web page | |
| 2.4 | Camera exposure/gain settings (auto? fixed?) | `v4l2-ctl -d /dev/videoN --list-ctrls` | |

## 3. Network and tether (owner: ________)

| # | Check | How | Result |
|---|---|---|---|
| 3.1 | Topology diagram (draw it: cameras, switch, SBC, tether, laptop, IPs) | — | attach |
| 3.2 | Switch model; managed? port speeds? | label / datasheet | |
| 3.3 | Negotiated link speed & duplex — **ROV side** | `ethtool eth0` | |
| 3.4 | Negotiated link speed & duplex — **topside side** | `ethtool <iface>` / OS network settings | |
| 3.5 | Tether type, length, any extenders/converters | — | |
| 3.6 | Interface errors (CRC, drops) after 10 min of streaming | `ethtool -S eth0`, `ip -s link` | |
| 3.7 | UDP throughput, jitter, loss (no video running) | ROV `iperf3 -s`; topside `iperf3 -c <rov> -u -b 80M -t 30` (raise -b until loss appears) | Mb/s · ms · % |
| 3.8 | TCP throughput both directions | `iperf3 -c <rov> -t 30` and `-R` | |
| 3.9 | RTT idle vs with all video streaming | `ping -c 50 <rov>` | idle __ ms / loaded __ ms |
| 3.10 | Who uses the tether, per stream | `iftop -i eth0` / `nload` (screenshot) | |
| 3.11 | Do control/telemetry share the link with video? Any prioritisation? | design / code | |

## 4. Streams (owner: ________) — one row per stream on the tether

| # | Stream | Protocol (RTP/RTSP/WebRTC/HTTP-MJPEG/…) | Transport (UDP/TCP) | Codec | Resolution | FPS | Avg Mb/s | Peak Mb/s | GOP / keyframe interval | B-frames? |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | | | | | | | | | | |
| S2 | | | | | | | | | | |
| … | | | | | | | | | | |

How:
- `ffprobe -v error -show_streams -of json <url>` → codec, profile, size, fps.
- Bitrate: `iftop` per stream, or record 30 s (`ffmpeg -i <url> -c copy -t 30 s.mkv`) and divide size by time.
- Peaks: `ffprobe -show_entries packet=pts_time,size` on the recording (or notebook helper `windowed_mbps`).
- GOP / B-frames: `ffprobe -show_entries frame=pict_type -of csv=p=0 s.mkv | head -100`.

Totals: sum of average Mb/s = ______ → ______ % of measured throughput (target ≤ 70 %).

## 5. Topside: decoding and rendering (owner: ________)

| # | Check | How | Result |
|---|---|---|---|
| 5.1 | Laptop model, CPU, GPU, OS, browser + version | — | |
| 5.2 | Which component decodes (browser `<video>`, WebRTC, JS decoder, `<img>` MJPEG, native player)? | code / DevTools | |
| 5.3 | Hardware decoding used? | `chrome://gpu` (Video Acceleration) · `chrome://media-internals` | |
| 5.4 | CPU/GPU load with all streams displayed | Task Manager / `htop` | |
| 5.5 | Dropped frames / decode time | `chrome://webrtc-internals` (framesDropped, totalDecodeTime, jitterBufferDelay) | |
| 5.6 | Does the UI stay responsive (control input) with all streams? | DevTools → Performance, long tasks | |

## 6. Latency (owner: ________)

Method: millisecond clock on the topside screen, camera pointed at it, video window next to it, phone photo; 10 repeats.

| Condition | Camera | Median (ms) | Worst (ms) |
|---|---|---|---|
| 1 camera streaming | pilot | | |
| All cameras streaming | pilot | | |
| All cameras + thrusters at full power | pilot | | |
| After 15 min, enclosure closed | pilot | | |
| Camera switch time (press → new picture) | any | | |

## 7. Failure behaviour (owner: ________)

| # | Test | What happened? | Recovered? How long? |
|---|---|---|---|
| 7.1 | Unplug one camera while streaming | | |
| 7.2 | Unplug the tether for 5 s | | |
| 7.3 | Switch cameras rapidly for 10 s | | |
| 7.4 | Add 1 % packet loss (`tc netem loss 1%`) | | |
| 7.5 | Load the SBC CPU (`stress-ng --cpu 4 -t 60`) | | |
| 7.6 | Restart the streaming service while the UI is open | | |

---

## 8. Summary (fill in together)

| | Value | Requirement / target | OK? |
|---|---|---|---|
| Total video on the wire | | ≤ 70 % of throughput | |
| Pilot camera latency (median / worst) | | e.g. ≤ 200 / 300 ms | |
| SBC CPU, all streaming | | ≥ 1 core free | |
| SBC temperature after 15 min closed | | below throttling | |
| Camera start reliability | | 10 / 10 | |
| Failure tests passed | | all recover, UI honest | |

**Top 3 surprises:** 1. ______ 2. ______ 3. ______
**Top 3 bottleneck hypotheses (ranked) and the next measurement for each:** ______
