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
| [ROV_Experiments.md](experiments/ROV_Experiments.md) | **The homework.** Every experiment the team can run on the real ROV (glass-to-glass latency, tether truth, encoder limits, packet-loss torture, heat soak, chaos drills, pilot blind tests…), with predictions, steps, result sheets, points and badges |
| [ms_clock.html](experiments/ms_clock.html) | Full-screen millisecond clock for glass-to-glass latency photos |

## Engineering practice (`sdlc/`)

See [sdlc/README.md](sdlc/README.md): live session plan, Bug Hunt League, GitHub workflow, weekly Knowledge Exchange, postmortem template.

Reading and printing versions are in Google Docs; links are in the main [README](../README.md#documents-google-docs).
