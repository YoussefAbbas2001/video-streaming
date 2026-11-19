# Demo: the Encoding Lab on screen (Video 3, about 2 minutes of recording)

Start it before recording: `cd encoding_lab && streamlit run app.py`, with the sidebar on *Synthetic underwater clip* or your own footage, 540p, 4 s. Do one dry run first so every encode is cached and appears instantly on camera.

| Step | Where | Do | Say (idea) |
|---|---|---|---|
| 1 | Encode tab | Codec H.264, Quality (CRF) 23 | "This is our baseline: size, bitrate, quality and speed in one place." |
| 2 | Encode → Frame compare | Switch View to **Diff ×8** | "Bright = where the encoder threw information away. Mostly fine texture." |
| 3 | Encode | Rate control **Bitrate cap**, 1 Mb/s, then 0.25 Mb/s | "Quality falls slowly, then suddenly. Find the knee." |
| 4 | Encode → Bitrate over time | Keyframe every 2 s | "The red I-frames are the spikes the tether must absorb." |
| 5 | Encode | Toggle **Low latency** | "The grey B-frames disappear: no waiting for future frames." |
| 6 | Parameter sweep | Preset, Run sweep | "Slower presets save a few bits for a lot of CPU. On an SBC we live at the fast end." |
| 7 | Packet loss | GOP 1 s vs GOP 5 s vs Intra refresh → Simulate | "Same lost packets. One heals in a second, one stays broken for five." |
| 8 | Bandwidth planner | Our 8 cameras | "And this is whether it fits our tether." |
