# Demos

One folder per video. Each demo runs on a normal laptop with FFmpeg and Python 3. Steps marked *(board)* need the ROV computer.

| Video | Demo | Command | Shows |
|---|---|---|---|
| 1 · Why streaming is underrated | Glass-to-glass latency | open `01_why_streaming/clock.html` full screen (press F), film it with the camera, photograph clock + received video | Latency the pilot actually feels |
| 1 | Cost in Egyptian pounds | `python3 01_why_streaming/egypt_cost.py` | Raw vs H.264, in EGP and package-minutes |
| 1 | Raw vs compressed | `./01_why_streaming/raw_vs_compressed.sh [clip.mp4]` | 10 s raw = GBs; 8/4/2/1 Mb/s H.264 = MBs |
| 2 · Pipeline & bottlenecks | Live stream | `./02_pipeline/sender.sh` + `./02_pipeline/receiver.sh` | A real low-latency pipeline |
| 2 | Monitor | `python3 02_pipeline/monitor.py` | CPU per core, video-process cores, temperature, throttling, Mb/s vs budget |
| 2 | Find the bottleneck | follow `02_pipeline/bottleneck_lab.md` (uses `impair.sh`, needs sudo) | Processing vs network vs buffering |
| 2 | Camera inventory *(board)* | `./02_pipeline/camera_inventory.sh [rtsp://…]` | Which cameras share a USB bus, which encode H.264 themselves |
| 3 · Encoding pipeline | I/P/B frames | `./03_encoding/gop_view.sh` | GOP pattern and I-frame spikes |
| 3 | Encoding lab matrix | `python3 03_encoding/experiment_matrix.py [--input dive.mp4]` | Experiments A–E: bitrate, FPS, GOP vs size, quality, CPU |
| 3 | Encoding Lab app | `03_encoding/encoding_lab_walkthrough.md` | Every knob, live, on real video |
| 3 | Hardware vs software *(board)* | `03_encoding/hw_vs_sw.md` | CPU and heat of x264 vs Jetson NVENC |

Generated files go to `out/` folders, which git ignores.
