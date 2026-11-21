# Post-Workshop Engineering Challenge

> **Mission:** *Optimize the ROV video system to provide the best possible operator experience under limited network bandwidth and processing resources.*

**Duration:** 6 weeks (adjust to your season). **Team:** the software + electronics members who own video, plus at least one pilot.
**Deliverable at the end:** a 10-minute demonstration and a short engineering report (≤ 6 pages) that you can reuse in your MATE technical documentation and engineering presentation.

No architecture is prescribed. **The first deliverable is a measured baseline**; every later decision must refer back to it.

---

## 1. Requirements

Replace the placeholder numbers (marked ⟨…⟩) with values agreed with your pilots **after** the baseline. Keep the IDs — you will trace tests to them.

### Functional

| ID | Requirement |
|---|---|
| F1 | The pilot can select the primary camera with one key/button, from any screen. |
| F2 | Every camera shows an explicit state: LIVE, DEGRADED, PAUSED, LOST, CONNECTING. A frozen frame is never shown as live. |
| F3 | The primary camera can be recorded at full quality (on the ROV or topside) without affecting the live view. |
| F4 | A camera that disconnects reconnects automatically, without restarting the application. |
| F5 | When link capacity drops, cameras degrade in priority order; the pilot and manipulator cameras are protected. |
| F6 | The control/telemetry channel keeps working when video saturates the link. |

### Non-functional

| ID | Requirement | Example target |
|---|---|---|
| N1 | Pilot-camera glass-to-glass latency, all cameras streaming | median ≤ ⟨200⟩ ms, worst ≤ ⟨300⟩ ms over 10 trials |
| N2 | Pilot-camera quality | ≥ 1280×720, ≥ 25 fps; pilot can read ⟨the mission's smallest text/marking⟩ at ⟨distance⟩ |
| N3 | Bandwidth | total video ≤ 70 % of **measured** tether throughput |
| N4 | Onboard load | ≥ 1 CPU core free; no thermal throttling after 30 min in the closed enclosure |
| N5 | Camera switch time | ≤ ⟨1⟩ s from key press to new live picture |
| N6 | Recovery after a 1 s link interruption | live video again within ⟨2⟩ s, no application restart |
| N7 | Usability | a pilot who did not build the UI completes the 5 scripted tasks with ≤ 1 error and SUS ≥ ⟨70⟩ |

## 2. Constraints

- Use the vehicle's existing tether and onboard computer (Jetson Nano or Raspberry Pi 5) unless you can **justify a change with measurements and cost**.
- No change may reduce safety or remove existing control functions.
- Any new dependency (media server, library) must be documented: why, licence, how to install, how to remove.
- Everything must run on the competition laptop, offline.

## 3. Phases and milestones

| Week | Phase | Output | Milestone check |
|---|---|---|---|
| 1 | **Baseline** | Filled `ROV_System_Diagnostic_Checklist.md`; 60 s of real footage; the footage uploaded to the Encoding Lab (your bits-per-pixel) | Baseline review with the whole team |
| 2–3 | **Design** | ≥ 2 architecture options compared with numbers (`Proposed_Architecture_Options.md`); decision log entry; updated requirements with agreed targets; user stories with acceptance criteria | Design review (another team member challenges it) |
| 3–5 | **Build & test** | Small PRs, reviewed; unit + integration tests; failure tests (§5); usability test with a pilot; weekly pool or bench integration | Tagged release `v<x>-challenge-rc` |
| 6 | **Demonstrate** | Before/after measurements; demo; report | Final demonstration |

## 4. Acceptance criteria (for the challenge as a whole)

1. Every requirement F1–F6 and N1–N7 has **a test**, and **a measured result** (pass/fail) in the report.
2. The report contains a **before/after table** for N1, N3, N4, N5 with the method used.
3. At least **two architecture options** were evaluated with numbers before choosing.
4. At least **three failure scenarios** (§5) were tested, with results.
5. A pilot who did not build the UI ran the usability test; findings and resulting changes are documented.
6. The decision log explains every non-obvious setting (codec, bitrate, GOP, buffer sizes, priorities).

## 5. Testing requirements

| Level | Minimum |
|---|---|
| Unit | Bitrate/priority allocation logic; command validation; camera-state model (incl. boundaries and invalid input) |
| Integration | Stream pipeline with the real encoder (start/stop/reconnect); UI ↔ backend camera-state updates |
| System (bench + pool) | All cameras + thrusters, 30 min; latency at t = 1 min and t = 30 min |
| Failure | Camera unplug; tether interruption 1 s and 10 s; 1 % packet loss (`tc netem`); CPU load (`stress-ng`); hot enclosure |
| Usability | 5 scripted tasks (UX Pack §5), time on task, errors, SUS |
| Regression | All of the above re-run before the final demo; every fixed bug keeps its test |

## 6. Performance metrics to report

| Metric | Unit | How |
|---|---|---|
| Video on the wire (avg / peak 1 s) | Mb/s | `iftop` / recorded packets |
| Link utilisation | % of measured throughput | iperf3 + above |
| Glass-to-glass latency (median / worst) | ms | ms-clock photo method, 10 trials |
| Camera switch time | ms | high-speed phone video or ms clock |
| Recovery time after interruption | s | stopwatch / video |
| SBC CPU per core, temperature, throttling | %, °C, flag | `htop`, `vcgencmd` / `tegrastats` |
| Topside decode drops | frames | `chrome://webrtc-internals` |
| Pilot task success / time / errors / SUS | %, s, count, 0–100 | usability test |

## 7. Definition of Done (challenge)

- [ ] All requirement tests executed; results recorded (pass/fail with numbers)
- [ ] Code merged to `main` through reviewed PRs; release tagged
- [ ] Failure scenarios tested on the real vehicle
- [ ] Usability test done with a pilot; top findings addressed or ticketed
- [ ] Decision log and README updated (how to run, how to configure, how to recover)
- [ ] Report and demo prepared; measurements reproducible by another member

## 8. Final demonstration (10 min) and scoring

| Part | Time | Content |
|---|---|---|
| Baseline | 2 min | What you measured and what surprised you |
| Design decision | 2 min | Options compared, numbers, why you chose |
| Live demo | 4 min | Pilot drives; switch cameras; pull a camera; interrupt the link; show the UI states |
| Results | 2 min | Before/after table; what's next |

| Criterion | Weight |
|---|---|
| Requirements met — measured, not claimed | 30 % |
| Quality of evidence (methods, repeatability, honesty about limits) | 20 % |
| Failure handling (robust system, honest UI) | 20 % |
| Pilot usability (test results, pilot feedback) | 15 % |
| Engineering documentation (decision log, tests, README) | 15 % |

## 9. Achievability notes (read before you start)

- You do **not** need to rebuild the web app. Most gains come from configuration (codec, rate control, GOP, buffers), stream management (substreams, priorities) and honest UI states.
- If your cameras already encode H.264 (IP cameras), most of the work is on the receiving side (protocol, buffering, UI).
- If your SBC encodes software-only (Pi 5), fewer full-quality streams + substreams is usually the realistic path.
- Ask for help early: a blocker raised on Monday is a 10-minute fix; raised on Friday it's a missed milestone.
