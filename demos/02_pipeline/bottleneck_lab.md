# Demo 2: Find the bottleneck

**Goal:** make the audience think like system engineers. Change **one** thing, ask them to predict which pipeline stage breaks first, then show the numbers.

## Setup (2 terminals + 1 window, 3 minutes)

| Terminal | Command | What it shows |
|---|---|---|
| A: sender (ROV computer, or the same laptop) | `./sender.sh` (or `DEST=<topside IP> ./sender.sh`) | Encoder `fps=` and `speed=` |
| B: monitor (same machine as the sender) | `python3 monitor.py --iface eth0 --link-mbps 100` (use `--iface lo` on one laptop) | CPU per core, video-process cores, temperature, Mb/s vs budget |
| Window: receiver | `./receiver.sh` | The picture |

Put `../01_why_streaming/clock.html` in front of the camera (or use the test pattern's own timer) to show latency changes.

## The four controlled problems

| # | Change | Command | Predict, then show | Bottleneck it reveals |
|---|---|---|---|---|
| 1 | Resolution up | `RES=1920x1080 ./sender.sh`, then `RES=3840x2160 ./sender.sh` | Encoder cores jump; at 4K the `speed=` drops below 1.0× and latency grows | **Processing:** the encoder can't keep up |
| 2 | Frame rate up | `FPS=60 ./sender.sh` | ≈ 2× CPU; same bitrate cap, so each frame gets half the bits and looks worse | **Processing and quality:** high FPS ≠ low latency |
| 3 | Thin tether | `sudo ./impair.sh lo limit 1mbit` while sending 2 Mb/s | The queue fills, latency climbs second by second, then the picture smears or freezes | **Network bandwidth** |
| 4 | Added delay and jitter | `sudo ./impair.sh lo delay 150ms`, then `sudo ./impair.sh lo jitter 80ms` | Constant delay: smooth but late. Jitter: stutter, because the receiver must buffer or drop | **Network delay and buffering** |
| bonus | Packet loss | `sudo ./impair.sh lo loss 2%` | Grey or smeared blocks that heal at the next keyframe (try `GOP_S=5` vs `GOP_S=0.5`) | **Reliability:** GOP length |
| bonus | Receiver buffering | Run `./receiver.sh --plain` next to `./receiver.sh` and read `vq=` in ffplay's status line | Measured here: default ffplay queued ≈ 1.2 MB of video (seconds at 2 Mb/s) vs ≈ 23 kB with the low-latency flags | **Buffering**: the delay is in the player, not the network |
| bonus | Slow preset | `PRESET=medium ./sender.sh` | CPU up, a little fewer bits, more latency | **Processing:** speed vs efficiency |

**Always end with** `sudo ./impair.sh lo clear` (or `eth0`).

## Questions to ask the audience

1. Which stage is the bottleneck now: camera, encoder, network, buffer, decoder or display? How do you know?
2. Which number on the monitor proves it?
3. What is the cheapest fix? (Usually: let the camera encode, lower the auxiliary cameras' FPS, or cap the bitrate. Rarely a bigger computer.)

## Heat variant (reliability)

Run `python3 monitor.py --csv heat.csv --duration 1800 --plain` while sending 3–4 streams (`PORT=5601 ./sender.sh &` …) inside the closed enclosure. Plot `temp_max_c` and `video_proc_cores` over time. If temperature passes 80 °C on a Pi, `get_throttled` changes from `0x0` and the encoder `speed=` falls: that is the 2023 failure, reproduced on purpose.
