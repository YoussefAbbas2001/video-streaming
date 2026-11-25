# ROV hardware for video: cameras, encoder boards and heat

*M.I.A Robotics · streaming docs · 25 Nov 2026 · merges the former jetson-nano-vs-pi5 page and the hardware parts of streaming-additions*

**Contents:** [1 USB vs IP cameras](#1-usb-cameras-vs-ip-cameras) · [2 Jetson Nano 2GB vs Raspberry Pi 5](#2-jetson-nano-2gb-vs-raspberry-pi-5-for-our-cameras) · [3 Can the Pi 5 replace the Nano?](#3-can-the-raspberry-pi-5-replace-the-jetson-nano) · [4 Heat and reliability](#4-reliability-the-2023-heat-failure-and-how-to-prevent-it) · [Sources](#sources)

## 1. USB cameras vs IP cameras

We already stream 8 cameras, and network video recorders (NVRs) routinely ingest dozens of IP cameras. Both work because each design puts the encoding and the bandwidth limit somewhere different.

| | USB (UVC) camera | IP camera |
|---|---|---|
| Link | USB 2.0: 480 Mb/s signalling shared by everything on the bus | Ethernet: its own 100 Mb/s or 1 Gb/s switch port |
| Cable length | 5 m for a passive USB cable [S9] | 100 m for a standard Ethernet channel [S10] |
| Power | 5 V from USB. The Blue Robotics Low-Light HD USB camera draws up to 220 mA [S11] | PoE 802.3af: 15.4 W at the switch port, at least 12.95 W at the camera [S10] |
| Who encodes? | Raw YUYV or MJPEG means the SBC encodes. Some UVC cameras encode H.264 on board: the Blue Robotics low-light camera offers H.264, MJPEG and YUY2 at 1080p30 [S11] | Always the camera (H.264/H.265, often with a substream). The SBC is optional |
| Scaling to 8 | Limited by USB bus bandwidth and isochronous reservations, so hubs fail first | Add switch ports. An NVR only receives; it never encodes |
| Latency | Lowest when raw/MJPEG frames are used on the same computer | Set by the camera's internal buffering, so measure glass-to-glass |
| Integration | Small, cheap, easy to seal | Larger board, more power and heat, needs a switch inside the hull |

**How to know what you have:**
- `lsusb -t` shows which bus each camera is on and its speed.
- `v4l2-ctl -d /dev/videoN --list-formats-ext` lists the formats it offers (look for H264).
- For IP cameras, `ffprobe rtsp://…` shows codec, resolution and frame rate.

Run all three for every camera and keep the output in the team docs.

**Recommendation for M.I.A:** keep what works, but prefer cameras that deliver H.264 themselves, either UVC cameras with onboard H.264 or IP cameras. The SBC then only forwards packets, which also decides the Pi 5 question below.

## 2. Jetson Nano 2GB vs Raspberry Pi 5 for our cameras

**The short answer.** The Jetson Nano 2GB has a **hardware** H.264/H.265 encoder that NVIDIA rates at **4 × 1080p30 or 9 × 720p30**. It uses almost no CPU, so the four ARM cores stay free for the GUI link and computer vision. The Raspberry Pi 5 has **no hardware H.264 encoder**. It encodes in software (libx264) on four much faster Cortex-A76 cores, and Raspberry Pi measures **≈ 62–90 % of one core per 1080p30 stream** in low-latency mode. Both boards can **pass USB cameras' MJPEG through** with no encoding at all. That is the cheapest way to carry the small auxiliary cameras on either board.

| | Jetson Nano 2GB · hardware encoder | Jetson Nano 2GB · software x264 | Raspberry Pi 5 · software x264 | Any board · USB MJPEG passthrough |
|---|---|---|---|---|
| Who encodes | NVENC block in the Tegra X1 (via GStreamer `nvv4l2h264enc`) | 4 × Cortex-A57 @ 1.43 GHz | 4 × Cortex-A76 @ 2.4 GHz | the camera's own chip |
| Capacity (vendor / our estimate) | **1 × 4K30, 2 × 1080p60, 4 × 1080p30, 4 × 720p60, 9 × 720p30** (H.264 and H.265), ≈ 250 Mpx/s total [1] | far below the Pi 5: **measure** with the Encoding Lab's Bandwidth budget → Measure this computer | **≈ 3–4 × 1080p30** or **≈ 7–10 × 720p30** in low-latency mode *(estimate from [2], at 70 % CPU, with cooling)* | limited by USB bandwidth and the tether, not the CPU |
| CPU per 1080p30 stream | near zero (frame copies only) | high; measure | **62–90 % of one core** (low latency) · **98–153 %** (high quality) [2] | ≈ 1 % of a core for 720p30 (measured) |
| Encoder latency | hardware, about a frame or less when configured without B-frames; **measure** glass-to-glass | x264 zerolatency: 0 frames held, encode time = CPU time per frame | 0 frames held with zerolatency; ≈ 21–30 ms of single-core work per 1080p frame *(0.62–0.9 × 33 ms)* | 0 encode; the camera chip adds its own buffering |
| Bitrate for good quality | H.264 at a few Mb/s per 1080p stream; quality per bit **not yet measured** (older-generation encoder) | same as the Pi (same x264) | 1080p30 at ≈ 1 Mb/s: **39.1 dB / SSIM 0.956** (low latency), **41.8 dB / 0.974** (high quality) [2] | **4–5 × H.264's bitrate** for the same SSIM (measured): ≈ 1.3 Mb/s at 640×480@15, ≈ 18 Mb/s at 1080p30 |
| JPEG (MJPEG cameras) | hardware JPEG decode and encode, ≈ 600 Mpx/s [3] | — | software JPEG decode (cheap; ≈ 2.4 ms per 720p frame on our test PC) | no decode needed if you don't resize |
| Memory | 2 GB **shared** by CPU, GPU and encoder | | 4 / 8 / 16 GB | |
| Software | JetPack 4.6.x line (Ubuntu 18.04 base), GStreamer for the hardware encoder; mainline FFmpeg cannot use it | | current Raspberry Pi OS; FFmpeg, GStreamer, `rpicam-vid` | FFmpeg `-c:v copy`, mjpg-streamer |

Sources: [1] NVIDIA Jetson Nano module specification; [2] Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5–series computers*, white paper, 28 Apr 2026; [3] NVIDIA Jetson Nano product brief. Links at the end.

---

### Encoding capacity: how many cameras?

**Jetson Nano: a pixel budget.** The hardware encoder's capacity is a number of pixels per second. NVIDIA's table works out to about 250 Mpx/s: 4 × 1080p30 = 249 Mpx/s, and 9 × 720p30 = 249 Mpx/s [1]. Add up your cameras' width × height × fps and stay under that budget.

| Camera mix (our 8-camera plan) | Mpx/s | Share of the Nano's encoder |
|---|---|---|
| Pilot 1080p30 + manipulator 720p30 + rear 640×360@15 | 93 | ≈ 37 % |
| …plus 5 aux at 640×480@15, all hardware-encoded | 116 | ≈ 47 % |
| 2 × 1080p30 + 6 × 720p30 | 290 | **≈ 116 %: does not fit** |

The 2 GB board has the same Tegra X1 video engines as the 4 GB Nano. Its 2 GB of memory is shared with the GPU, so the realistic limit is **encoders + CV model + GUI link in 2 GB**. Watch `tegrastats` during a soak test.

**Raspberry Pi 5: a CPU budget.** Every stream costs CPU, roughly in proportion to its pixels.

- Raspberry Pi's measurements cover 1080p30 only [2]. In low-latency mode, 62 % of one core at 100 kb/s rising to 90 % at 20 Mb/s.
- With 4 cores and our 70 % headroom rule (2.8 cores), that is **about 3–4 low-latency 1080p30 streams**.
- Scaling by pixels (720p is 44 % of 1080p) gives **about 7–10 × 720p30**.
- These are **estimates**. Multi-stream scaling, other software on the Pi and thermal throttling all reduce them. Run the Encoding Lab **Bandwidth budget → Measure this computer** tab on the Pi itself, and soak-test with the enclosure closed.

**Jetson Nano in software.** Its Cortex-A57 cores are an older, slower design than the Pi 5's A76 cores. Software x264 on the Nano is a fallback, not a plan. If you need it, measure it with the Encoding Lab (Bandwidth budget → Measure this computer).

### Latency

- **Encoder hold** is the frames an encoder keeps before releasing the first one.
  - x264 with its defaults holds ~30 frames, about 1 s; we measured this in the Encoding Lab's Live camera tab.
  - With `-tune zerolatency` it holds **0**. Use zerolatency on both boards.
  - The Jetson hardware encoder must be configured without B-frames for the same effect.
- **Encode time per frame.**
  - On the Pi 5, a low-latency 1080p30 frame costs 0.62–0.9 × 33 ms ≈ 21–30 ms of one core's work. x264's slice threads spread it over several cores and shorten it.
  - Hardware encoders run at a fixed throughput (≈ 250 Mpx/s on the Nano), so a 1080p frame takes a few ms.
- **What the pilot feels is glass-to-glass.** Measure it, don't add up guesses. Film a phone stopwatch with the ROV camera, then photograph the phone and the pilot screen together; the difference is the latency. Take the median of 10 photos, on both boards, with the real tether.

### Quality per bit

- **Software vs older hardware.** Raspberry Pi's paper compares Pi 5 software x264 with the Pi 4's hardware encoder at the same bitrates [2]:
  - At ≈ 1 Mb/s the Pi 4 hardware (39.5 dB) matches the low-latency software preset (39.1 dB), while the high-quality software preset reaches 41.8 dB.
  - The Pi 4 encoder also tops out at about 6 Mb/s.
  - Older hardware encoders trade quality per bit for speed. The Jetson Nano's encoder is from the same era (Maxwell).
- **Measure the Nano's encoder before committing.** Record the same 30 s clip with `nvv4l2h264enc` at your target bitrate and compare with x264:
  ```bash
  ffmpeg -i nano_hw.mp4 -i reference.mkv -lavfi ssim -f null -   # prints SSIM against the reference
  ```
- **Underwater footage is harder than test charts** (marine snow, caustics). Calibrate with pool footage.

### MJPEG USB cameras on each board

- **Passthrough is free on both.** Ask the camera for its MJPEG mode at the size you want and copy it, with FFmpeg `-c:v copy` or mjpg-streamer `input_uvc -r WxH`. It costs about 1 % of a core and **4–5 × the bits** of H.264. That is fine for small cameras: ≈ 1.3 Mb/s at 640×480@15.
- **Resizing in software turns it into decode → scale → encode.** That costs ≈ 13 % of a core per 720p30 camera on our test PC, more on the Pi. See [codecs-and-ffmpeg.md](codecs-and-ffmpeg.md#the-resolution-trap).
- **The Jetson trick: MJPEG in, H.264 out, all in hardware.** The Nano decodes JPEG in hardware [3], so an MJPEG camera can feed the hardware H.264 encoder without touching the CPU. You get MJPEG's free capture and H.264's small bitrate:
  ```bash
  gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 ! \
    nvv4l2decoder mjpeg=1 ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' ! \
    nvv4l2h264enc bitrate=2000000 iframeinterval=30 insert-sps-pps=true maxperf-enable=1 ! \
    h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=192.168.1.100 port=5600 sync=false
  ```
- **The Pi 5 equivalent** decodes the JPEG in software, then encodes with x264. It is affordable for one or two cameras:
  ```bash
  ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -framerate 30 -i /dev/video0 \
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2M -maxrate 2M -bufsize 1M -g 30 \
    -f rtp rtp://192.168.1.100:5600
  ```

(The commands are reference pipelines. They were not run here, because there is no Jetson or Pi in the test environment.)

### Recommendation for our 8 cameras

| If we use… | Pilot + manipulator | Rear + aux cameras | Watch out for |
|---|---|---|---|
| **Jetson Nano 2GB** | hardware H.264 (≈ 90 of 250 Mpx/s) | MJPEG passthrough, or hardware H.264 via the MJPEG → H.264 pipeline above | 2 GB shared memory with CV; old JetPack 4.6 base; set no B-frames |
| **Raspberry Pi 5** | x264 `ultrafast` + `zerolatency`: ≈ 1–1.5 cores for 1080p30 + 720p30 (estimate) | MJPEG passthrough (no CPU) | **active cooling is mandatory** (our 2023 heat failure); measure capacity with the Encoding Lab (Bandwidth budget → Measure this computer) |
| **Either** | cameras that encode H.264 themselves (IP cameras, UVC H.264 cameras) remove the problem | | camera latency and GOP settings |

**How to decide:** run the same three measurements on both boards with the real cameras and tether:

1. Encoding Lab **Bandwidth budget → Measure this computer**: streams per board; then **Plan the budget** with *This computer (benchmarked)* for the full camera mix.
2. **Glass-to-glass** latency: median of 10.
3. **30-minute soak test** in the closed enclosure, logging temperature and throttling.

Put the numbers in a GitHub issue. Numbers beat opinions.

## 3. Can the Raspberry Pi 5 replace the Jetson Nano?

The Pi 5 has not been tested on our ROV yet. What the vendors document:

| | NVIDIA Jetson Nano | Raspberry Pi 5 |
|---|---|---|
| Hardware video **encoder** | Yes: H.264/H.265 up to 4K30, 4× 1080p30 or 9× 720p30 (used through GStreamer `nvv4l2h264enc`) | **None**: H.264 must be encoded in software (libx264) [S12] |
| CPU | 4× Cortex-A57 @ 1.43 GHz | 4× Cortex-A76 @ 2.4 GHz [S12] |
| Measured software encode | n/a | One 1080p30 low-latency libx264 stream (`ultrafast`, `zerolatency`) used **62–90 % of one core**. The higher-quality `superfast` setting used **98–153 %** [S12] |
| Computer vision | 128-core Maxwell GPU (CUDA, TensorRT) | CPU, or the AI HAT+ (Hailo-8L 13 TOPS or Hailo-8 26 TOPS, over PCIe) [S13] |
| Lifecycle | Developer kit listed as end-of-life; JetPack 4 end-of-life November 2024; production modules available until January 2027 [S14, S15] | Current product, current OS (Raspberry Pi OS Trixie) |

**Verdict: it depends on who encodes.**

1. **The cameras encode** (UVC H.264 or IP cameras). The SBC only forwards packets, so the Pi 5 is a **good replacement**. Its CPU is much faster for everything else: control, telemetry and the web server.
2. **The SBC must encode several raw or MJPEG USB cameras.** The **Jetson Nano is better.** Its hardware encoder handles four 1080p30 streams almost for free. A Pi 5 would spend most of a core per 1080p30 stream, so realistically about three such streams, with heat as the next problem (section 5).
3. **On-board computer vision.** With the AI HAT+ the Pi 5 is competitive for detection networks. Without it, the Nano's GPU wins.

**Before deciding, run a soak test:** 8 streams in the real configuration, 30 minutes, inside the sealed enclosure. Log CPU per core, temperature and throttling flags every second (`while true; do date +%T; vcgencmd measure_temp; vcgencmd get_throttled; sleep 1; done >> soak.log` on a Pi, `tegrastats --interval 1000 --logfile soak.log` on a Jetson) and dropped frames, then compare both boards the same way. Full comparison: [hardware-and-encoders.md](#).

## 4. Reliability: the 2023 heat failure and how to prevent it

**What we know:** during a competition trial in 2023 the video stream stopped working because the SBC got too hot. The details still need collecting (board, cameras, enclosure, water and air temperature, minutes into the run). Collect them and write a blameless postmortem using the [postmortem template](https://github.com/YoussefAbbas2001/mia-software-practice/blob/HEAD/docs/postmortem-template.md).

**Mechanism:**
1. The hull is sealed, so it has no airflow.
2. Encoding is a constant heavy load.
3. The processor reaches its thermal limit and the firmware lowers the clock. On Raspberry Pi boards throttling starts at **80 °C** and becomes aggressive at **85 °C** [S16].
4. A slower CPU encodes fewer frames than the cameras produce. Queues grow, latency grows, frames drop, and the pipeline eventually stalls.

The Pi 5 Active Cooler's fan starts at 60 °C and reaches full speed at 75 °C [S16]. But inside a sealed hull a fan only stirs hot air: the heat must leave **through the hull into the water**.

**Five fixes:**

| Fix | What to do |
|---|---|
| Measure | Log temperature and throttle flags every second: `vcgencmd measure_temp` and `vcgencmd get_throttled` on a Pi, `tegrastats` on a Jetson |
| Design | Make a heat path: thermal pad → aluminium plate → hull wall → water. Keep the SBC away from the ESCs and power converters |
| Reduce | Let cameras encode. Lower the frame rate and resolution of auxiliary cameras. Stop streams nobody is watching |
| Soak-test | Run 30 minutes in the sealed enclosure, in water as warm as the competition pool, before every event |
| Show | Put the SBC temperature on the pilot screen, with a warning at 75 °C, before throttling starts |

## Sources

**Boards (section 2)**

1. NVIDIA, Jetson Nano module specifications (video encode: 250 Mpx/s; 1×4K30, 2×1080p60, 4×1080p30, 4×720p60, 9×720p30, H.264/H.265): <https://developer.nvidia.com/embedded/jetson-Nano>
2. Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5–series computers*, white paper RP-010033, 28 Apr 2026 (no hardware H.264 encoder on Pi 5; 1080p30 CPU use and quality per preset): <https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf>
3. NVIDIA Jetson Nano product brief (JPEG encode and decode 600 MP/s): <https://www.ximea.com/support/attachments/download/13172/embedded-print-product-brief-for-jetson-nano-931214-lr.pdf>
4. Our own measurements: Encoding Lab, 19–21 Nov 2026 (MJPEG vs H.264 bitrate, passthrough vs resize CPU, x264 encoder hold).

**Cameras, Pi 5 vs Nano, heat (sections 1, 3, 4)**

- [S9] USB 2.0 5 m passive cable limit (ATEN extender documentation): https://www.aten.com/gb/en/products/usb-solutions/extenders/ueh4002a/
- [S10] PoE standards and 100 m Ethernet channel limit: https://www.alarmgrid.com/blog/products/alarm-com-adc-csvr2016p and https://reolink.com/blog/poe-distance-limit/
- [S11] Blue Robotics Low-Light HD USB Camera specifications: https://www.robotshop.com/products/bluerobotics-low-light-hd-usb-camera-2
- [S12] Raspberry Pi Ltd, "H.264 encoding performance on Raspberry Pi 5-series computers", white paper, 28 April 2026: https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf
- [S13] Raspberry Pi AI HAT+ product brief (13 / 26 TOPS): https://cdn.sparkfun.com/assets/c/9/b/7/3/Raspberry_Pi_AI_HAT__product_brief.pdf
- [S14] NVIDIA Jetson Product Lifecycle and Jetson FAQ (Nano dev kit EOL; JetPack 4 EOL Nov 2024): https://www.developer.nvidia.com/embedded/lifecycle and https://dz4-prod.svc.nvidia.com/embedded/faq
- [S15] NVIDIA forum announcement: Jetson Nano production modules available until January 2027: https://forums.developer.nvidia.com/t/jetson-nano-and-jetson-xavier-announcements/232519
- [S16] Raspberry Pi, "Heating and cooling Raspberry Pi 5" (80/85 °C throttling, Active Cooler fan curve): https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/
