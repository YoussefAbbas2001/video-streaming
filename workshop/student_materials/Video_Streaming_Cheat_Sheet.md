# ROV Video Streaming — Cheat Sheet

*M.I.A Robotics · Engineering Better ROV Systems. Keep this next to the topside laptop.*

---

## 1. Bandwidth in one line

**R_raw = W × H × bpp × f**   (bit/s)  — pixels per frame × bits per pixel × frames per second

| Pixel format | bpp | Where you meet it |
|---|---|---|
| RGB24 / BGR24 | 24 | OpenCV frames, screenshots |
| YUYV (YUY2) 4:2:2 | 16 | raw USB webcam output |
| NV12 / YUV420P (I420) 4:2:0 | 12 | encoder input, hardware decoders, browsers |

| One camera, raw | 15 fps | 30 fps | 60 fps |
|---|---|---|---|
| 640×480 YUYV | 74 Mb/s | 147 Mb/s | 295 Mb/s |
| 1280×720 NV12 | 166 Mb/s | 332 Mb/s | 664 Mb/s |
| 1920×1080 NV12 | 373 Mb/s | 746 Mb/s | 1,493 Mb/s |
| 1920×1080 RGB24 | 746 Mb/s | 1,493 Mb/s | 2,986 Mb/s |

**Compressed estimate:** R ≈ bits-per-pixel × W × H × f. Measure your own bpp (notebook Exp. 6). On the workshop's synthetic clip at good quality (SSIM ≈ 0.98): H.264 ≈ 0.045, MJPEG ≈ 0.34 bits/pixel. Real camera footage usually needs more.

**On the wire:** + ~5 % (RTP/UDP, 1500 MTU) · + ~7 % (MPEG-TS/UDP) · TCP adds ACK traffic in the other direction.

**Planning rule:** sustained video ≤ **70 %** of *measured* throughput, minus control & telemetry.

**Units:** 1 Mb/s = 10⁶ bit/s. 1 MB = 8 Mb. 1 Gb/s = 1000 Mb/s.

| Link | Nominal | Notes |
|---|---|---|
| Fast Ethernet | 100 Mb/s | ~94–95 Mb/s UDP payload in practice |
| Gigabit Ethernet | 1000 Mb/s | needs good cable/connectors over the whole tether |
| USB 2.0 | 480 Mb/s **shared per bus** | periodic (isochronous) ≤ 80 % of each micro-frame; one UVC camera ≤ ~197 Mb/s |
| USB 3.x | 5 Gb/s+ | USB 2.0 cameras on a USB 3 hub still share the hub's USB 2.0 side |

---

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Codec** | how pixels are compressed: H.264/AVC, H.265/HEVC, MJPEG, AV1, VP8/VP9 |
| **Container** | how compressed frames are packaged with timing: MP4, MKV, MPEG-TS, RTP payload |
| **Protocol** | how a stream is set up and delivered: RTSP (control), RTP, WebRTC, HLS, HTTP-MJPEG, SRT |
| **Transport** | UDP (no retransmit, no waiting) or TCP (reliable, may stall/delay) |
| **Bitrate** | bits/s the encoder produces |
| **Bandwidth / capacity** | bits/s the link could carry |
| **Throughput** | bits/s actually delivered (measure with iperf3) |
| **Latency** | time from scene to screen for one frame (glass-to-glass) |
| **Jitter** | variation in packet/frame arrival time |
| **FPS** | frames per second — *not* the same as latency |
| **I / P / B frame** | intra-only (big, decodable alone) / predicted from earlier / also from a future frame (adds latency) |
| **IDR** | I-frame that also resets the reference list — a clean starting point |
| **GOP** | frames from one I-frame to the next (`-g`) |
| **Intra refresh** | heal the picture with a sweeping column of intra blocks instead of periodic I-frames |
| **CRF** | constant-quality mode (x264/x265); lower = better quality, bigger; +6 ≈ half the bitrate |
| **CBR / VBR / VBV** | constant / variable bitrate; VBV buffer (`-maxrate`, `-bufsize`) caps peaks |
| **Preset** | encoder speed vs efficiency (`ultrafast` … `veryslow`) |
| **Profile / level** | which coding tools / how big & fast a stream the decoder must handle |
| **Lookahead** | frames the encoder analyses before deciding — better compression, more latency |
| **Main stream / substream** | high-quality stream for the big screen / small stream for thumbnails |
| **NVENC / NVDEC** | NVIDIA's dedicated hardware encoder / decoder blocks |
| **PSNR / SSIM / VMAF** | objective quality metrics (dB / 0–1 / 0–100) |

---

## 3. FFmpeg — the commands you'll actually use

### Inspect a stream or file
```bash
ffprobe -hide_banner input.mp4                                   # quick summary
ffprobe -v error -show_streams -show_format -of json rtsp://192.168.1.10/stream1   # everything, as JSON
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,avg_frame_rate,bit_rate,pix_fmt -of default=nw=1 input.mp4
ffprobe -v error -select_streams v:0 -show_entries frame=pict_type -of csv=p=0 input.mp4 | head -60   # I/P/B pattern → GOP
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time,size,flags -of csv=p=0 input.mp4  # per-packet sizes (bitrate over time)
ffmpeg -hide_banner -encoders | grep -E "264|265|hevc|mjpeg|av1"  # what this FFmpeg was BUILT with (not what works!)
```

### Encode (files)
```bash
# H.264, constant quality (recording)
ffmpeg -i in.mkv -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -an out.mp4
# H.264, live-style: capped bitrate, low latency, 1-second GOP, no B-frames
ffmpeg -i in.mkv -c:v libx264 -preset veryfast -tune zerolatency -b:v 2500k -maxrate 2500k -bufsize 1250k -g 30 -bf 0 -pix_fmt yuv420p out.mp4
# H.265
ffmpeg -i in.mkv -c:v libx265 -preset medium -crf 28 -tag:v hvc1 out.mp4
# MJPEG (q:v 2 = best … 31 = worst)
ffmpeg -i in.mkv -c:v mjpeg -q:v 5 out.mkv
# AV1 (SVT-AV1)
ffmpeg -i in.mkv -c:v libsvtav1 -preset 8 -crf 35 out.mkv
# Substream: 640×360 at 15 fps
ffmpeg -i in.mkv -vf "scale=640:360,fps=15" -c:v libx264 -preset veryfast -tune zerolatency -b:v 400k -maxrate 400k -bufsize 200k out_sub.mp4
```

### Capture from a USB (V4L2) camera
```bash
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext                  # YUYV? MJPG? H264? which sizes/fps?
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 -c copy test.mkv   # record without re-encoding
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 -f null -          # cost of decode alone
```

### Stream
```bash
# RTP/UDP to the topside laptop (also writes an SDP file the player needs)
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2500k -maxrate 2500k -bufsize 1250k -g 30 \
  -f rtp -sdp_file cam0.sdp rtp://192.168.2.1:5600
# Publish to a media server (e.g. MediaMTX) over RTSP; browsers then read it via WebRTC
ffmpeg -re -i in.mp4 -c copy -f rtsp rtsp://localhost:8554/cam0
# Low-latency playback for testing
ffplay -fflags nobuffer -flags low_delay -framedrop -protocol_whitelist file,udp,rtp -i cam0.sdp
```

### Measure quality
```bash
ffmpeg -i distorted.mp4 -i reference.mkv -lavfi "[0:v][1:v]psnr" -f null -
ffmpeg -i distorted.mp4 -i reference.mkv -lavfi "[0:v][1:v]ssim" -f null -
ffmpeg -i distorted.mp4 -i reference.mkv -lavfi "[0:v][1:v]libvmaf" -f null -     # needs FFmpeg built with libvmaf
```
⚠️ Inputs must have the same resolution and aligned timestamps. MKV stores millisecond timestamps — add `settb=1/30` to both inputs when comparing frame by frame.

---

## 4. GStreamer on Jetson Nano (hardware encoder)
```bash
gst-inspect-1.0 | grep -E "nvv4l2|nvjpeg"              # NVIDIA elements present?
gst-inspect-1.0 nvv4l2h264enc                          # all properties (bitrate, iframeinterval, ...)
gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 ! image/jpeg,width=1280,height=720,framerate=30/1 ! \
  nvv4l2decoder mjpeg=1 ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' ! \
  nvv4l2h264enc bitrate=2500000 iframeinterval=30 insert-sps-pps=true maxperf-enable=1 ! \
  h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=192.168.2.1 port=5600 sync=false
sudo tegrastats                                        # NVENC/NVDEC activity, CPU, temperatures
```
Upstream FFmpeg does **not** use the Jetson Nano's hardware encoder. The **Jetson Orin Nano has no hardware encoder at all.** The **Raspberry Pi 5 has no hardware H.264 encoder** (software libx264 only; HEVC *decode* is hardware).

---

## 5. Troubleshooting commands

| Question | Command |
|---|---|
| Which SBC / OS exactly? | `cat /proc/device-tree/model` · `cat /etc/nv_tegra_release` (Jetson) · `uname -a` |
| USB tree, speeds, which camera shares which bus? | `lsusb -t` |
| USB errors / resets / brown-outs? | `dmesg -w` (watch while starting cameras and thrusters) |
| Camera formats? | `v4l2-ctl -d /dev/videoN --list-formats-ext` |
| Link speed and duplex? | `ethtool eth0` (both ends!) · errors: `ethtool -S eth0` |
| Real throughput, jitter, loss? | ROV: `iperf3 -s` · topside: `iperf3 -c <rov-ip> -u -b 80M -t 30` and `iperf3 -c <rov-ip> -R` |
| What is using the tether? | `iftop -i eth0` · `nload` · `tcpdump -i eth0 -w cap.pcap` + Wireshark |
| Ping / RTT under load | `ping -i 0.2 <rov-ip>` while all cameras stream |
| CPU / memory / processes | `htop` · `top -H -p $(pgrep -d, ffmpeg)` |
| Temperature & throttling | Pi: `vcgencmd measure_temp` · `vcgencmd get_throttled` (0x0 = OK) · Jetson: `tegrastats` |
| Simulate a bad tether | `sudo tc qdisc add dev eth0 root netem delay 30ms 10ms loss 1%` · remove: `sudo tc qdisc del dev eth0 root` |
| Browser decode/drops | `chrome://webrtc-internals` · `chrome://media-internals` · DevTools → Performance |
| Glass-to-glass latency | ms clock on the topside screen, camera pointed at it, photo of both, ×10, median + worst |

---

## 6. Testing terms

| Term | One line |
|---|---|
| Unit test | one function/class in isolation |
| Integration test | components together (stream manager + real FFmpeg) |
| System test | the whole ROV, ideally in the pool |
| Acceptance test | checks the acceptance criteria, with the user |
| Regression test | old bugs stay fixed — re-run after every change |
| Boundary test | at, below and above every limit (8 vs 9 cameras; −1.0 vs −1.0001) |
| Negative test | invalid input must be rejected |
| Special values | NaN, ±inf, 0, empty, None, True/False |
| Stress / performance | all cameras + full thrust + 30 min; latency, CPU, temperature |
| DoR / DoD | Definition of Ready (can we start?) / Definition of Done (are we really finished?) |

---

## 7. Code review checklist

- [ ] **Correctness** — meets the acceptance criteria; edge cases handled
- [ ] **Readability & naming** — a new member understands it
- [ ] **Architecture** — right layer; no unjustified new dependency
- [ ] **Error handling** — camera lost, timeout, bad input, link loss
- [ ] **Resources** — streams, sockets, processes, timers closed/stopped
- [ ] **Concurrency** — no races between callbacks/threads; UI updated from the right thread
- [ ] **Performance** — no per-frame copies/allocations/logging that aren't needed
- [ ] **UX honesty** — the UI never shows success before the system confirms it
- [ ] **Tests** — added/updated; they would fail without the change
- [ ] **Docs** — decision log / README updated

Comment on the code, not the person. Label comments *blocking / suggestion / question*. Keep PRs < 400 lines.
