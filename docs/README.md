# Docs

## Streaming (`streaming/`)

| File | What's inside |
|---|---|
| [measure-and-diagnose.md](streaming/measure-and-diagnose.md) | **Measure and diagnose.** Diagnose by stage · symptom → suspect matrix · every metric with the tool and exact command (network, stream, compute and heat, latency, quality, reliability) · latency methods · throughput and loss in the pilot GUI (with tested code) · first 15 diagnostics · reporting template · **field guide: 45 problems with pictures**, cause, ROV meaning, confirm and fix |
| [hardware-and-encoders.md](streaming/hardware-and-encoders.md) | **Cameras, boards, heat.** USB vs IP cameras · Jetson Nano 2GB (hardware + software) vs Raspberry Pi 5 vs MJPEG passthrough: capacity, CPU, latency, quality, how many cameras · can the Pi 5 replace the Nano · the 2023 heat failure · sources |
| [codecs-and-ffmpeg.md](streaming/codecs-and-ffmpeg.md) | **Compression and tools.** Why compression runs the world · the Egypt cost example · MJPEG vs H.264 measured · **the resolution trap** · NVENC and other hardware options · mjpeg-streamer vs mjpg-streamer vs FFmpeg · tested recipes · pitfalls · streaming for computer vision · sources |

## Experiments (`experiments/`)

| File | What's inside |
|---|---|
| [ROV_Experiments.md](experiments/ROV_Experiments.md) | **The member handbook.** Every experiment the team can run on the real ROV (glass-to-glass latency, tether truth, encoder limits, packet-loss torture, heat soak, chaos drills, pilot blind tests…), with predictions, steps, result sheets, points and badges |
| [Leader_Guide.md](experiments/Leader_Guide.md) | **The leader's recipe.** How a team leader runs the experiments as six weekly 90-minute mini-workshops: kit and prep, the session rhythm, a plan per week, the answer key (expected results, common mistakes, debrief questions), verifying results, keeping it fun, adapting it, running the boss level, a printable result sheet |
| [ms_clock.html](experiments/ms_clock.html) | Full-screen millisecond clock for glass-to-glass latency photos |
| [experiment_board.py](experiments/experiment_board.py) | Leaderboard, ranks and badges from the labelled result issues |

## Debugging (`debug/`)

| File | What's inside |
|---|---|
| [ROV_Debug_Checklist.md](debug/ROV_Debug_Checklist.md) | **When the video is broken.** Write the symptom · symptom finder · 45 checks in pipeline order (power, cameras, computer, streams, tether, topside, pilot), each with the command, the good value and what a bad value means · step-by-step routes for 9 symptoms · numbers at a glance |
| [rov_healthcheck.sh](debug/rov_healthcheck.sh) | Runs the A–E checks on the ROV computer in about 10 s and prints ✅ ⚠️ ❌ with the meaning and the fix; `--md` for a GitHub issue. Tests: `test_healthcheck.sh` |

## Engineering practice (`sdlc/`)

See [sdlc/README.md](sdlc/README.md): live session plan, Bug Hunt League, GitHub workflow, weekly Knowledge Exchange, postmortem template.

Reading and printing versions are in Google Docs; links are in the main [README](../README.md#documents-google-docs).
