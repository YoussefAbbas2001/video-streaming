# Docs

## Streaming (`streaming/`)

| File | What's inside |
|---|---|
| [streaming-additions.md](streaming/streaming-additions.md) | Why compression runs the world · the Egypt cost example · USB vs IP cameras · Pi 5 vs Jetson Nano · the 2023 heat failure · streaming for computer vision · sources |
| [jetson-nano-vs-pi5.md](streaming/jetson-nano-vs-pi5.md) | Jetson Nano 2GB (hardware + software encoder) vs Raspberry Pi 5 (software) vs MJPEG passthrough: capacity, CPU, latency, quality, how many cameras, recommendation |
| [mjpeg-and-ffmpeg.md](streaming/mjpeg-and-ffmpeg.md) | What MJPEG is · MJPEG vs H.264 measured · **the resolution trap** · NVENC and other hardware options · mjpeg-streamer vs mjpg-streamer vs **FFmpeg (our choice)** · tested recipes · pitfalls |
| [video-diagnostics.md](streaming/video-diagnostics.md) | Field guide: 45 video problems (timing, compression, network, motion, camera, display, ROV computer) with a picture, the cause, what it means on our ROV, how to confirm and how to fix; symptom → cause matrix; what to measure; latency methods; first 15 diagnostics to build |
| [gui-stream-metrics.md](streaming/gui-stream-metrics.md) | The two numbers every camera tile needs (throughput and loss), thresholds, and tested code to get them |
| [measuring-performance.md](streaming/measuring-performance.md) | Every metric (network, stream, compute and heat, latency, quality, reliability), with the tool and the exact command |

## Engineering practice (`sdlc/`)

See [sdlc/README.md](sdlc/README.md): live session plan, Bug Hunt League, GitHub workflow, weekly Knowledge Exchange, postmortem template.

Reading and printing versions are in Google Docs; links are in the main [README](../README.md#documents-google-docs).
