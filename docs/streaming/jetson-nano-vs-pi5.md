# Jetson Nano 2GB vs Raspberry Pi 5 for our cameras

*M.I.A Robotics · streaming docs · 21 Nov 2026*

**The short answer.** The Jetson Nano 2GB has a **hardware** H.264/H.265 encoder that NVIDIA rates at **4 × 1080p30 or 9 × 720p30**. It uses almost no CPU, so the four ARM cores stay free for the GUI link and computer vision. The Raspberry Pi 5 has **no hardware H.264 encoder**. It encodes in software (libx264) on four much faster Cortex-A76 cores, and Raspberry Pi measures **≈ 62–90 % of one core per 1080p30 stream** in low-latency mode. Both boards can **pass USB cameras' MJPEG through** with no encoding at all. That is the cheapest way to carry the small auxiliary cameras on either board.

| | Jetson Nano 2GB · hardware encoder | Jetson Nano 2GB · software x264 | Raspberry Pi 5 · software x264 | Any board · USB MJPEG passthrough |
|---|---|---|---|---|
| Who encodes | NVENC block in the Tegra X1 (via GStreamer `nvv4l2h264enc`) | 4 × Cortex-A57 @ 1.43 GHz | 4 × Cortex-A76 @ 2.4 GHz | the camera's own chip |
| Capacity (vendor / our estimate) | **1 × 4K30, 2 × 1080p60, 4 × 1080p30, 4 × 720p60, 9 × 720p30** (H.264 and H.265), ≈ 250 Mpx/s total [1] | far below the Pi 5: **measure** with the Encoding Lab Benchmark tab | **≈ 3–4 × 1080p30** or **≈ 7–10 × 720p30** in low-latency mode *(estimate from [2], at 70 % CPU, with cooling)* | limited by USB bandwidth and the tether, not the CPU |
| CPU per 1080p30 stream | near zero (frame copies only) | high; measure | **62–90 % of one core** (low latency) · **98–153 %** (high quality) [2] | ≈ 1 % of a core for 720p30 (measured) |
| Encoder latency | hardware, about a frame or less when configured without B-frames; **measure** glass-to-glass | x264 zerolatency: 0 frames held, encode time = CPU time per frame | 0 frames held with zerolatency; ≈ 21–30 ms of single-core work per 1080p frame *(0.62–0.9 × 33 ms)* | 0 encode; the camera chip adds its own buffering |
| Bitrate for good quality | H.264 at a few Mb/s per 1080p stream; quality per bit **not yet measured** (older-generation encoder) | same as the Pi (same x264) | 1080p30 at ≈ 1 Mb/s: **39.1 dB / SSIM 0.956** (low latency), **41.8 dB / 0.974** (high quality) [2] | **4–5 × H.264's bitrate** for the same SSIM (measured): ≈ 1.3 Mb/s at 640×480@15, ≈ 18 Mb/s at 1080p30 |
| JPEG (MJPEG cameras) | hardware JPEG decode and encode, ≈ 600 Mpx/s [3] | — | software JPEG decode (cheap; ≈ 2.4 ms per 720p frame on our test PC) | no decode needed if you don't resize |
| Memory | 2 GB **shared** by CPU, GPU and encoder | | 4 / 8 / 16 GB | |
| Software | JetPack 4.6.x line (Ubuntu 18.04 base), GStreamer for the hardware encoder; mainline FFmpeg cannot use it | | current Raspberry Pi OS; FFmpeg, GStreamer, `rpicam-vid` | FFmpeg `-c:v copy`, mjpg-streamer |

Sources: [1] NVIDIA Jetson Nano module specification; [2] Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5–series computers*, white paper, 28 Apr 2026; [3] NVIDIA Jetson Nano product brief. Links at the end.

---

## 1. Encoding capacity: how many cameras?

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
- These are **estimates**. Multi-stream scaling, other software on the Pi and thermal throttling all reduce them. Run the Encoding Lab **Benchmark** tab on the Pi itself, and soak-test with the enclosure closed.

**Jetson Nano in software.** Its Cortex-A57 cores are an older, slower design than the Pi 5's A76 cores. Software x264 on the Nano is a fallback, not a plan. If you need it, measure it with the Benchmark tab.

## 2. Latency

- **Encoder hold** is the frames an encoder keeps before releasing the first one.
  - x264 with its defaults holds ~30 frames, about 1 s; we measured this in the Encoding Lab's Live camera tab.
  - With `-tune zerolatency` it holds **0**. Use zerolatency on both boards.
  - The Jetson hardware encoder must be configured without B-frames for the same effect.
- **Encode time per frame.**
  - On the Pi 5, a low-latency 1080p30 frame costs 0.62–0.9 × 33 ms ≈ 21–30 ms of one core's work. x264's slice threads spread it over several cores and shorten it.
  - Hardware encoders run at a fixed throughput (≈ 250 Mpx/s on the Nano), so a 1080p frame takes a few ms.
- **What the pilot feels is glass-to-glass.** Measure it, don't add up guesses. Film a phone stopwatch with the ROV camera, then photograph the phone and the pilot screen together; the difference is the latency. Take the median of 10 photos, on both boards, with the real tether.

## 3. Quality per bit

- **Software vs older hardware.** Raspberry Pi's paper compares Pi 5 software x264 with the Pi 4's hardware encoder at the same bitrates [2]:
  - At ≈ 1 Mb/s the Pi 4 hardware (39.5 dB) matches the low-latency software preset (39.1 dB), while the high-quality software preset reaches 41.8 dB.
  - The Pi 4 encoder also tops out at about 6 Mb/s.
  - Older hardware encoders trade quality per bit for speed. The Jetson Nano's encoder is from the same era (Maxwell).
- **Measure the Nano's encoder before committing.** Record the same 30 s clip with `nvv4l2h264enc` at your target bitrate and compare with x264:
  ```bash
  ffmpeg -i nano_hw.mp4 -i reference.mkv -lavfi ssim -f null -   # prints SSIM against the reference
  ```
- **Underwater footage is harder than test charts** (marine snow, caustics). Calibrate with pool footage.

## 4. MJPEG USB cameras on each board

- **Passthrough is free on both.** Ask the camera for its MJPEG mode at the size you want and copy it, with FFmpeg `-c:v copy` or mjpg-streamer `input_uvc -r WxH`. It costs about 1 % of a core and **4–5 × the bits** of H.264. That is fine for small cameras: ≈ 1.3 Mb/s at 640×480@15.
- **Resizing in software turns it into decode → scale → encode.** That costs ≈ 13 % of a core per 720p30 camera on our test PC, more on the Pi. See [mjpeg-and-ffmpeg.md](mjpeg-and-ffmpeg.md#the-resolution-trap).
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

## 5. Recommendation for our 8 cameras

| If we use… | Pilot + manipulator | Rear + aux cameras | Watch out for |
|---|---|---|---|
| **Jetson Nano 2GB** | hardware H.264 (≈ 90 of 250 Mpx/s) | MJPEG passthrough, or hardware H.264 via the MJPEG → H.264 pipeline above | 2 GB shared memory with CV; old JetPack 4.6 base; set no B-frames |
| **Raspberry Pi 5** | x264 `ultrafast` + `zerolatency`: ≈ 1–1.5 cores for 1080p30 + 720p30 (estimate) | MJPEG passthrough (no CPU) | **active cooling is mandatory** (our 2023 heat failure); measure capacity with the Benchmark tab |
| **Either** | cameras that encode H.264 themselves (IP cameras, UVC H.264 cameras) remove the problem | | camera latency and GOP settings |

**How to decide:** run the same three measurements on both boards with the real cameras and tether:

1. Encoding Lab **Benchmark**: streams per board.
2. **Glass-to-glass** latency: median of 10.
3. **30-minute soak test** in the closed enclosure, logging temperature and throttling.

Put the numbers in a GitHub issue. Numbers beat opinions.

## Sources

1. NVIDIA, Jetson Nano module specifications (video encode: 250 Mpx/s; 1×4K30, 2×1080p60, 4×1080p30, 4×720p60, 9×720p30, H.264/H.265): <https://developer.nvidia.com/embedded/jetson-Nano>
2. Raspberry Pi Ltd, *H.264 encoding performance on Raspberry Pi 5–series computers*, white paper RP-010033, 28 Apr 2026 (no hardware H.264 encoder on Pi 5; 1080p30 CPU use and quality per preset): <https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf>
3. NVIDIA Jetson Nano product brief (JPEG encode and decode 600 MP/s): <https://www.ximea.com/support/attachments/download/13172/embedded-print-product-brief-for-jetson-nano-931214-lr.pdf>
4. Our own measurements: Encoding Lab, 19–21 Nov 2026 (MJPEG vs H.264 bitrate, passthrough vs resize CPU, x264 encoder hold).
