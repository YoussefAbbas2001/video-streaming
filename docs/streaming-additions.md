# Streaming deep-dive: additions for the 2026–27 season

Companion to the three recorded videos and slides 6, 12, 18, 39, 40 and 46 of the deck. Every number has a source at the end; prices and product lifecycles change, so re-check them before presenting.

**Contents**
1. Why streaming is underrated: compression runs the world
2. A practical example in Egyptian pounds
3. USB cameras vs IP cameras
4. Raspberry Pi 5 vs Jetson Nano: can the Pi 5 replace the Nano?
5. Reliability: the 2023 heat failure and how to prevent it
6. Streaming for computer vision: detection, 3D reconstruction, autonomy, SLAM
7. Measuring performance (separate document: [`measuring-performance.md`](measuring-performance.md))

---

## 1. Why streaming is underrated: compression runs the world

Nobody notices video compression until it fails. Yet:

- **Video is about two thirds of all internet traffic.** Sandvine's 2023 Global Internet Phenomena Report measured video at **65 %** of all internet traffic in 2022, with video volume growing **24 %** in a single year [S1].
- **Every codec generation halves the bits.** HEVC/H.265 (2013) delivers about 50 % lower bitrate than H.264/AVC (2003) at equal quality. VVC/H.266, finalized in July 2020, delivers about 50 % less than HEVC and about **75 % less than H.264** [S2, S3]. Each step took the world's video-coding experts years of joint work: VVC alone went from an exploration phase in 2015 to a final standard in 2020 [S3].
- **Compression wins Emmys.** The Joint Video Team that built H.264 received a 2008 Primetime Engineering Emmy and a 2009 Technology & Engineering Emmy [S4, S5]. Accepting the 2008 award, ITU's Malcolm Johnson called H.264 *"a jewel in the crown of international standards collaboration"* [S4].
- **Compression moves money.** Streaming services spend heavily on encoding research because every saved bit is saved delivery cost for every viewer. One example is per-title encoding, which tunes the bitrate ladder to each video's complexity [S6].

**The ROV link:** our robot is a tiny version of the same problem. We have eight cameras, one tether, a small computer and a pilot who needs the picture *now*. The engineering questions are the same ones streaming companies ask, only with harder latency limits.

## 2. A practical example in Egyptian pounds

**Price basis (November 2026).** WE (Telecom Egypt) home internet:
- The entry-level package is **100 GB for EGP 150 per month before 14 % VAT** (EGP 171 with VAT). The regulator doubled its quota from 50 GB effective 1 November 2026 [S7].
- That is about **EGP 1.71 per GB**.
- Larger WE Space tiers are in the same range, for example 150 GB for EGP 260 and 200 GB for EGP 330, VAT exclusive [S8].

| One hour of 1080p30 video | Bitrate | Data per hour | Cost at EGP 1.71/GB | 100 GB package lasts |
|---|---|---|---|---|
| Raw RGB, 24 bits/pixel | 1.49 Gb/s | 672 GB | **≈ EGP 1,150** | **9 minutes** |
| Raw YUV 4:2:0, 12 bits/pixel | 0.75 Gb/s | 336 GB | ≈ EGP 575 | 18 minutes |
| H.264, 5 Mb/s (HD streaming) | 5 Mb/s | 2.25 GB | **≈ EGP 3.85** | **44 hours** |
| H.264, 2 Mb/s (ROV pilot camera) | 2 Mb/s | 0.9 GB | ≈ EGP 1.54 | 111 hours |

How the numbers are calculated:
- **Raw bitrate:** 1920 × 1080 pixels × 30 frames/s × 24 bits = 1.49 Gb/s.
- **Data per hour:** bitrate × 3600 s ÷ 8 bits per byte.
- **Two takeaways:** H.264 is about **300× cheaper** than raw RGB for the same hour. A 30 Mb/s WE line would need about **50× more speed** just to carry raw 1080p30 live.

Run the calculator with your own numbers: `python demos/01_why_streaming/egypt_cost.py --price 1.71 --minutes 60`.

## 3. USB cameras vs IP cameras

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

The demo `demos/02_pipeline/camera_inventory.sh` runs all three.

**Recommendation for M.I.A:** keep what works, but prefer cameras that deliver H.264 themselves, either UVC cameras with onboard H.264 or IP cameras. The SBC then only forwards packets, which also decides the Pi 5 question below.

## 4. Raspberry Pi 5 vs Jetson Nano: can the Pi 5 replace the Nano?

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

**Before deciding, run a soak test:** 8 streams in the real configuration, 30 minutes, inside the sealed enclosure. Log CPU per core, temperature, throttling flags and dropped frames with `demos/02_pipeline/monitor.py --csv soak.csv`, then compare both boards with the same script.

## 5. Reliability: the 2023 heat failure and how to prevent it

**What we know:** during a competition trial in 2023 the video stream stopped working because the SBC got too hot. The details still need collecting (board, cameras, enclosure, water and air temperature, minutes into the run). Collect them and write a blameless postmortem using [`sdlc/postmortem-template.md`](../sdlc/postmortem-template.md).

**Mechanism:**
1. The hull is sealed, so it has no airflow.
2. Encoding is a constant heavy load.
3. The processor reaches its thermal limit and the firmware lowers the clock. On Raspberry Pi boards throttling starts at **80 °C** and becomes aggressive at **85 °C** [S16].
4. A slower CPU encodes fewer frames than the cameras produce. Queues grow, latency grows, frames drop, and the pipeline eventually stalls.

The Pi 5 Active Cooler's fan starts at 60 °C and reaches full speed at 75 °C [S16]. But inside a sealed hull a fan only stirs hot air: the heat must leave **through the hull into the water**.

**Five fixes:**

| Fix | What to do |
|---|---|
| Measure | Log temperature and throttle flags every second: `vcgencmd measure_temp` and `vcgencmd get_throttled` on a Pi, `tegrastats` on a Jetson. `demos/02_pipeline/monitor.py` does both |
| Design | Make a heat path: thermal pad → aluminium plate → hull wall → water. Keep the SBC away from the ESCs and power converters |
| Reduce | Let cameras encode. Lower the frame rate and resolution of auxiliary cameras. Stop streams nobody is watching |
| Soak-test | Run 30 minutes in the sealed enclosure, in water as warm as the competition pool, before every event |
| Show | Put the SBC temperature on the pilot screen, with a warning at 75 °C, before throttling starts |

## 6. Streaming for computer vision: detection, 3D reconstruction, autonomy, SLAM

When these algorithms run topside on the pilot stream, they inherit every streaming decision:

- **Object detection.** A study of YOLOv5 on H.264 surveillance video found that CRF 37 instead of 22 barely changed detection while saving a lot of bitrate. Detection dropped noticeably at stronger compression, **especially in poor lighting and with fast motion** [S17], which describes underwater footage.
- **SLAM and visual odometry.** Feature-based SLAM tracks corners and texture, exactly the detail compression removes. With compressed images fewer feature points survive and matching gets less accurate [S18].
- **3D reconstruction / photogrammetry.** It needs sharp, consistent images. Compression artefacts and keyframe pulsing (quality changing every GOP) reduce the matches between images.
- **Autonomous movement.** It is a control loop: acting on a frame that is several hundred milliseconds old makes the controller overshoot. Jitter and dropped frames make motion estimates wrong.

**Rules for the team:**
1. Run CV **next to the raw frames** (on the ROV) whenever the hardware allows.
2. If CV runs topside, give it **its own stream profile**: higher bitrate, no B-frames, constant frame rate, accurate timestamps. Don't reuse the pilot's heavily compressed substream.
3. For photogrammetry, **capture stills or record locally** at high quality and transfer them, instead of reconstructing from the live stream.
4. **Measure it:** run your detector on your own footage encoded at several bitrates (the Encoding Lab's sweep produces them) and plot detection rate against bitrate. Choose the lowest bitrate that keeps the detection rate.

---

## Sources

- [S1] Sandvine 2023 Global Internet Phenomena Report press release (video 65 % of traffic, +24 % in 2022): https://www.applogicnetworks.com/press-releases/sandvines-2023-global-internet-phenomena-report-shows-24-jump-in-video-traffic-with-netflix-volume-overtaking-youtube
- [S2] Overview of the Versatile Video Coding (VVC) Standard and its Applications (≈ 50 % vs HEVC, ≈ 75 % vs AVC): https://www.microsoft.com/en-us/research/?p=798226
- [S3] Fraunhofer HHI, Versatile Video Coding (timeline 2015–2020): https://www.hhi.fraunhofer.de/vvc
- [S4] ISO, "Hollywood presents Emmy Award to ITU, ISO and IEC" (2008): https://www.iso.org/news/2008/08/Ref1153.html
- [S5] Fraunhofer, "Second Emmy for the H.264 video standard" (2009): https://www.fraunhofer.de/en/press/research-news/2009/02/ResearchNews022009Topic7.html
- [S6] Bitmovin, per-title encoding savings: https://bitmovin.com/blog/per-title-encoding-savings/
- [S7] SEE News, Egypt doubles basic home internet data to 100 GB (1 Nov 2026, EGP 150, 14 % VAT): https://see.news/egypt-doubles-basic-home-internet-data-to-100gb-same-price
- [S8] Telecom Egypt, WE Space plans: https://te.eg/en/personal/home/we-internet/we-space/super?filterBy=we-internet-space-super
- [S9] USB 2.0 5 m passive cable limit (ATEN extender documentation): https://www.aten.com/gb/en/products/usb-solutions/extenders/ueh4002a/
- [S10] PoE standards and 100 m Ethernet channel limit: https://www.alarmgrid.com/blog/products/alarm-com-adc-csvr2016p and https://reolink.com/blog/poe-distance-limit/
- [S11] Blue Robotics Low-Light HD USB Camera specifications: https://www.robotshop.com/products/bluerobotics-low-light-hd-usb-camera-2
- [S12] Raspberry Pi Ltd, "H.264 encoding performance on Raspberry Pi 5-series computers", white paper, 28 April 2026: https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf
- [S13] Raspberry Pi AI HAT+ product brief (13 / 26 TOPS): https://cdn.sparkfun.com/assets/c/9/b/7/3/Raspberry_Pi_AI_HAT__product_brief.pdf
- [S14] NVIDIA Jetson Product Lifecycle and Jetson FAQ (Nano dev kit EOL; JetPack 4 EOL Nov 2024): https://www.developer.nvidia.com/embedded/lifecycle and https://dz4-prod.svc.nvidia.com/embedded/faq
- [S15] NVIDIA forum announcement: Jetson Nano production modules available until January 2027: https://forums.developer.nvidia.com/t/jetson-nano-and-jetson-xavier-announcements/232519
- [S16] Raspberry Pi, "Heating and cooling Raspberry Pi 5" (80/85 °C throttling, Active Cooler fan curve): https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/
- [S17] O'Byrne, Vibhoothi, Sugrue, Kokaram, "Impact of Video Compression on the Performance of Object Detection Systems for Surveillance Applications", AVSS 2022: https://arxiv.org/abs/2211.05805
- [S18] ORBBuf: A Robust Buffering Method for Remote Visual SLAM (effect of JPEG compression on feature points): https://arxiv.org/abs/2010.14861
- Jetson Nano encoder capacity: NVIDIA Jetson Nano technical specifications. See `workshop/resources/References.md`.
