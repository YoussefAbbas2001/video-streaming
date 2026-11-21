# Postmortem: <title>

> **Blameless:** we describe systems and decisions, never people. The question is "what made this failure possible?", not "who did it?". People who were there are the most valuable witnesses, so make it safe for them to talk.

| | |
|---|---|
| Date of incident | |
| Event | (pool test / regional / competition trial) |
| Impact | (what the pilot lost, for how long, what it cost in points or time) |
| Authors | |
| Status | Draft · Reviewed · Actions done |

## Summary (3 sentences)

## Timeline

| Time | What happened | What we saw (screen, logs, temperature…) |
|---|---|---|
| | | |

## What went wrong (causes, not culprits)

- **Trigger:** the event that started it
- **Contributing causes:** design, testing gaps, missing monitoring
- **Why didn't we catch it earlier?**

## What went right

## Actions

| Action | Type (prevent / detect / mitigate) | Owner | Due | Issue |
|---|---|---|---|---|
| | | | | #… |

## Measurements to add so we'd see it next time

---

## Worked example: 2023 competition trial, video stream lost to heat (draft to complete together)

**What we know:** during a competition trial in 2023, the video stream stopped working because the on-board computer overheated.

**What we still need from the people who were there:**
- Which board (Jetson Nano?) and which software (FFmpeg / GStreamer, which settings)?
- How many cameras, at what resolution and frame rate, and who encoded: the cameras or the board?
- The enclosure: sealed? Any heat sink or thermal path to the hull? Was a fan inside?
- Water and air temperature; how many minutes into the run did it fail?
- Symptoms: gradual (rising latency, dropped frames) or sudden (black screen)? Did it come back after cooling?
- Was temperature being logged or shown to anyone?

**Likely chain to verify:**
sealed hull → constant encode load → SoC at its thermal limit → firmware throttles the clock → encoder slower than the cameras → queues grow, frames drop → stream stops.

**Candidate actions:**

| Action | Type | Owner | Issue |
|---|---|---|---|
| Log SoC temperature and throttling every second during every pool test (`demos/02_pipeline/monitor.py --csv`) | detect | | |
| Show SoC temperature on the pilot GUI, warning at 75 °C | detect | | |
| Thermal path: pad → aluminium plate → hull, measured with the soak test | prevent | | |
| Move encoding into the cameras (H.264 UVC or IP) where possible | prevent | | |
| 30-minute sealed soak test in warm water before every event, added to the Definition of Done | prevent | | |
| Degraded mode: drop auxiliary cameras' FPS automatically above 78 °C | mitigate | | |
