# Measuring every streaming metric

A metric you don't measure is a guess. This page lists every performance number we care about, the tool that measures it, and the exact command.

**Conventions**
- `ROV` is the ROV computer's IP address and `eth0` the tether interface. Replace both with yours (`ip -br addr` shows them).
- "Good" values are starting targets for a pilot camera, not laws.
- Per stream, live: `python3 encoding_lab/tools/rtp_probe.py --port 5600 --forward 5700` (throughput, packet loss, jitter; see [gui-stream-metrics.md](gui-stream-metrics.md)).
- Per computer, live: `sar -n DEV 1` (Mb/s per interface), `htop` (CPU per core), `vcgencmd measure_temp; vcgencmd get_throttled` (Pi) or `tegrastats` (Jetson).

---

## 1. Network

| Metric | Why it matters | How to measure | Good |
|---|---|---|---|
| Link speed and duplex | A 1 Gb/s port that negotiated 100 Mb/s half-duplex explains "random" stalls | `ethtool eth0`: check the `Speed:` and `Duplex:` lines | Expected speed, Full duplex |
| Usable throughput | The real budget, not the label on the switch | ROV: `iperf3 -s`. Topside: `iperf3 -c ROV -t 30` (TCP) and `iperf3 -c ROV -R -t 30` (reverse direction) | ≥ 90 % of link speed |
| Loss and jitter under load | Lost packets corrupt video (UDP) or freeze it (TCP) | `iperf3 -c ROV -u -b 80M -t 30`; the result shows `Jitter` and `Lost/Total` | Loss 0 %, jitter < 5 ms |
| Round-trip time | Adds to control latency; spikes reveal queueing | `ping -c 200 -i 0.2 ROV`: report min / avg / max / mdev | avg < 2 ms on a tether, no spikes |
| Utilised bandwidth per interface | Is the tether full? | `monitor.py` (reads `/proc/net/dev` every second), or `nload eth0`, `bmon`, `sar -n DEV 1` | ≤ 70 % of measured throughput |
| Bandwidth per connection or process | Who is using it? | `sudo iftop -i eth0` (per connection), `sudo nethogs eth0` (per process) | Matches your budget table |
| Bandwidth per stream (live) | Check each camera against its budget | `sudo tcpdump -i eth0 -w cap.pcap udp` for 30 s, then Wireshark → Statistics → Conversations (UDP) or IO Graph | Within ±10 % of the configured bitrate |
| RTP loss and jitter per stream | Per-camera health | Wireshark → Telephony → RTP → RTP Streams (lost %, max jitter, sequence errors) | 0 lost |

## 2. The video stream itself

| Metric | How to measure |
|---|---|
| Codec, resolution, frame rate | `ffprobe -hide_banner rtsp://CAMERA/…` or `ffprobe -hide_banner file.mp4` |
| Average bitrate of a recording | `ffprobe -v error -show_entries format=bit_rate -of default=nw=1 file.mp4` |
| Live bitrate and fps | `ffmpeg -hide_banner -i udp://@:5600 -f null -`: the status line shows `fps=` and `bitrate=` |
| Keyframe interval (GOP) | `ffprobe -v error -select_streams v -show_entries frame=pict_type -of csv file.mp4`, then count the frames between `I` lines |
| Frame sizes and peaks | The same `ffprobe` command with `frame=pkt_size,pict_type`, or the Encoding Lab's *Bitrate over time* tab |
| Camera formats (USB) | `v4l2-ctl -d /dev/video0 --list-formats-ext` (look for H264, MJPG, YUYV) |
| Actual camera frame rate | `v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=300`: prints the delivered fps |
| USB bus sharing | `lsusb -t` shows which cameras share a bus and its speed (480M = USB 2.0) |

## 3. Compute and heat

| Metric | Raspberry Pi | Jetson | Any Linux |
|---|---|---|---|
| CPU per core | | | `mpstat -P ALL 1`, `htop` |
| CPU of one process (e.g. ffmpeg) | | | `pidstat -u -p $(pgrep -d, ffmpeg) 1` |
| Encoder speed | | | FFmpeg status line `speed=` (≥ 1.0× = real time); `ffmpeg -benchmark` |
| Hardware encoder load | none on a Pi 5 | `sudo tegrastats --interval 1000` (NVENC clock, GR3D GPU %) or `jtop` | |
| SoC temperature | `vcgencmd measure_temp` | `tegrastats` (CPU/GPU °C), `/sys/class/thermal/thermal_zone*/temp` | `/sys/class/thermal/thermal_zone*/temp` |
| Throttling | `vcgencmd get_throttled` (0x0 = never throttled; any other value means it happened, so decode it) | `tegrastats` clocks dropping under load | CPU MHz in `monitor.py` |
| Clock speed | `vcgencmd measure_clock arm` | `tegrastats` | `/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq` |
| Memory | | | `free -m` |

`monitor.py` logs CPU per core, temperature, clock speed, Pi throttle flags and bandwidth per interface. It writes one CSV row per second, which is ideal for a 30-minute soak test.

## 4. Latency

| What | How | Notes |
|---|---|---|
| **Glass-to-glass** (the number the pilot feels) | Run a millisecond stopwatch on a phone in front of the ROV camera, put the phone next to the pilot screen, and take 10+ photos of both. In each photo, latency = stopwatch − stopwatch-in-video | Report **median and worst**, not one photo |
| Per-stage latency (GStreamer) | `GST_TRACERS="latency(flags=pipeline+element)" GST_DEBUG=GST_TRACER:7 gst-launch-1.0 …` | Shows which element holds frames |
| Encoder hold (frames buffered before the first output) | Measured: x264 defaults held 41 frames (the Encoding Lab's Live camera tab measures it live); `-tune zerolatency` held 0 | Lookahead and B-frames are the usual culprits |
| Network delay | `ping` RTT ÷ 2 (rough one-way estimate) | Usually tiny on a tether |
| Browser receive side (WebRTC) | `chrome://webrtc-internals`: inbound-rtp `jitterBufferDelay ÷ jitterBufferEmittedCount`, `totalDecodeTime ÷ framesDecoded` | Jitter buffer is often the largest part |
| Player cache (VLC, ffplay) | VLC's network caching defaults to 1000 ms. Use `ffplay -fflags nobuffer -flags low_delay -framedrop` | A big, avoidable delay |

## 5. Quality

| Metric | Command |
|---|---|
| PSNR | `ffmpeg -i encoded.mp4 -i reference.mkv -lavfi psnr -f null -` |
| SSIM | `ffmpeg -i encoded.mp4 -i reference.mkv -lavfi ssim -f null -` |
| VMAF | `ffmpeg -i encoded.mp4 -i reference.mkv -lavfi libvmaf -f null -` (needs FFmpeg built with libvmaf) |
| All of the above, interactively | Encoding Lab app (`encoding_lab/`), Encode and Compare tabs |

The reference must be the **lossless** source, at the same resolution and frame rate (the Encoding Lab handles the scaling and timestamp alignment for you).

## 6. Reliability

| Metric | How |
|---|---|
| Dropped or duplicated frames | FFmpeg status line `drop=` / `dup=`; WebRTC `framesDropped`; GStreamer `fpsdisplaysink` (rendered vs dropped) |
| Recovery after loss | Unplug the tether for 2 s and time how long until a clean picture returns; the Encoding Lab *Bandwidth budget → Packet-loss lab* shows the same effect |
| Time to switch cameras | Stopwatch from button press to clean picture (bounded by the keyframe interval) |
| Soak test | 30 min, sealed enclosure, real camera configuration: `monitor.py --csv soak.csv`. Pass when there is no throttling, no growth in latency and no stream restarts |

## 7. Reporting template

For every test, write down: date, hardware, software versions, camera settings, the command used, the **number**, and what you will change because of it. Paste it into the GitHub issue or pull request it belongs to, so measurements live next to the code they justify.
