# Break the Other Team's Software! — Testing Competition Guide

> **Testing is not about proving that software works. It is about discovering how it can fail — before the pool does.**

Duration: **60 minutes** (+10 min debrief). Teams of 3–5. One referee (the presenter or a senior member).

---

## 1. What you will test

Two small Python modules from an imaginary ROV pilot application, in `workshop_activities/testing_competition_code/`:

| Module | What it does |
|---|---|
| `rov_core/camera_manager.py` | Keeps track of up to 8 cameras, their state (connecting / live / lost), the primary camera, and the bandwidth budget |
| `rov_core/command_validator.py` | Checks pilot commands (thrusters, gripper) before they are sent to the vehicle: arming, link watchdog, value ranges |

The **specification** is `SPECIFICATION.md`. *The spec is the truth.* If the code and the spec disagree, the code has a defect.

The code contains **real defects** — some minor, some critical. Your job is to find them, prove them with a test, and report them so a developer could fix them without asking you anything.

Setup (2 minutes):

```bash
cd workshop_activities/testing_competition_code
pip install pytest
python -m pytest -q            # 7 starter tests — all pass. That proves nothing!
```

### Variant B — teams build, then attack each other
If you have more time, each team first implements the spec themselves (30 min), then the teams swap code. Same rules, same scoring. This variant also teaches that the author is the worst tester of their own code.

---

## 2. Schedule

| Time | Phase | What happens |
|---|---|---|
| 0:00 | Brief | Referee explains rules and scoring; everyone reads the spec (5 min) |
| 0:05 | **Test design** | Write a test plan *before* touching the code: list cases per spec rule using the techniques below (10 min) |
| 0:15 | **Attack** | Write tests, run them, file bug reports (20 min) |
| 0:35 | **Fix & regress** | Teams swap roles: you receive *another* team's bug reports for the module, fix the code, keep the failing test as a regression test (15 min) |
| 0:50 | **Score** | Referee validates every claim and fix (10 min) |
| 1:00 | Debrief | Which technique found the most defects? Which defects would have hurt in the pool? |

---

## 3. Scoring

| Event | Points |
|---|---|
| Real defect found (spec violated, reproducible) | **+10** |
| Defect is **critical** (see severity guide in the spec) | **+20** instead of +10 |
| Bug report has clear, minimal steps to reproduce **and** a failing automated test | **+5** |
| Report rejected: false positive (code matches spec) or not reproducible | **−5** |
| Duplicate of a defect your team already reported | 0 |
| Developers fix a defect and the regression test now passes | **+10** (to the fixing team) |
| A fix breaks a previously passing test (found by referee) | **−10** |
| Best bug report of the round (referee's choice) | **+5** bonus |

Rules:
1. Only the **spec** decides what is correct. "I would have designed it differently" is not a defect — write it as a suggestion (0 points, but welcome).
2. Every claim must be reproducible by the referee from your report alone.
3. One defect = one root cause. Ten tests that fail for the same reason are one defect.
4. The referee's decision is final, and the referee explains every decision (that is part of the learning).

---

## 4. Testing techniques — use them deliberately

| Technique | Question it asks | Example for this module |
|---|---|---|
| **Boundary testing** | What happens exactly at, just below and just above each limit? | 8 vs 9 cameras; width 1, 3840, 3841; value −1.0, −1.0001; heartbeat age = timeout |
| **Negative testing** | Does it reject what it must reject? | unknown keys, wrong types, unknown camera ids |
| **Equivalence classes** | Which inputs should behave the same? Test one of each class | axis values: in range / below / above / not a number |
| **Special values** | What about the values programmers forget? | `NaN`, `±inf`, `True`, `0`, empty dict, `None` |
| **State-based testing** | Does every state transition behave as specified? | LIVE → LOST → CONNECTING → LIVE; primary camera disconnects |
| **Sequence / integration** | Does it still work after a series of operations? | add → remove → add → allocate |
| **Regression** | Does an old bug stay fixed? | keep every failing test after the fix |

### Testing levels (for the debrief)
- **Unit tests** — one function or class in isolation (what you do today).
- **Integration tests** — several components together (camera manager + real FFmpeg pipeline).
- **System tests** — the whole ROV, ideally in the pool.
- **Acceptance tests** — does it meet the acceptance criteria, judged with the pilot?
- **Performance / stress tests** — 8 cameras, full thrust, 10 minutes, hot enclosure.
- **Regression tests** — re-run everything after each change.

---

## 5. Test case template

```markdown
### TC-<number>: <short title>
- Requirement / spec rule: <section and sentence of SPECIFICATION.md>
- Technique: boundary | negative | special value | state | sequence
- Preconditions: <e.g. 8 cameras added, vehicle armed, heartbeat at t=10.0>
- Steps:
  1. ...
  2. ...
- Test data: <exact values>
- Expected result (from the spec): ...
- Actual result: ...
- Status: pass | FAIL
- Automated test: tests/test_<team>.py::test_<name>
```

Example:

```markdown
### TC-07: Thruster value just below the lower limit is rejected
- Spec: §2 "Axis values must be real numbers … in [−1.0, +1.0] inclusive"
- Technique: boundary
- Preconditions: validator armed; heartbeat at t = 10.0 s
- Steps: validate({"yaw": -1.0001}, now_s = 10.1)
- Expected: CommandRejected
- Actual: ...
```

## 6. Bug report template

```markdown
## BUG-<team>-<number>: <one-line summary that states the wrong behaviour>
- Module / function: camera_manager.CameraManager.add_camera
- Severity: critical | major | minor   (justify in one sentence)
- Spec reference: §1 "At most 8 cameras. Adding a 9th raises CameraError."
- Steps to reproduce (minimal):
  1. m = CameraManager()
  2. add cameras 0..7 (640×360, 15 fps, 0.5 Mb/s)
  3. m.add_camera(8, 640, 360, 15, 0.5)
- Expected: CameraError
- Actual: camera 8 is added; len(m.cameras) == 9
- Failing test: tests/test_team_blue.py::test_ninth_camera_rejected
- Impact on the ROV: <what could go wrong in the pool / for the pilot>
- Notes / suspected cause (optional): comparison uses `>` instead of `>=`
```

A good bug report is **specific, minimal, reproducible, neutral in tone** ("the function returns X", never "someone forgot…"), and explains the **impact**.

---

## 7. Sample ROV test scenarios (for your real system, after the workshop)

| # | Scenario | Expected safe behaviour (write yours as acceptance criteria) |
|---|---|---|
| 1 | Unplug a USB camera / IP camera while streaming | That tile shows **LOST** within 1 s; other cameras unaffected; automatic reconnection; no frozen frame shown as live |
| 2 | Pull the tether / disable the switch port | ROV goes to its defined safe state; UI shows **LINK LOST** prominently; controls disabled; recovers when link returns |
| 3 | Switch cameras rapidly (key-mash 1–8 for 10 s) | No crash, no memory/CPU growth, final selection correct |
| 4 | Exceed available bandwidth (add streams / limit the link with `tc`) | Graceful degradation by priority; control traffic unaffected |
| 5 | Inject corrupted or incomplete frames (drop packets with `tc netem loss 2%`) | Decoder recovers at the next keyframe; no permanent freeze |
| 6 | Send invalid control commands (NaN, out of range, unknown keys) | Rejected, logged, never reaches the thrusters |
| 7 | Request an unsupported resolution / frame rate | Clear error message, fallback to a supported mode, no crash |
| 8 | CPU overload on the SBC (`stress-ng --cpu 4`) or a hot enclosure | Video degrades before control does; latency stays within requirement or the UI warns |
| 9 | Power the thrusters at full load while all cameras stream | No USB resets, no brown-outs (watch `dmesg`) |
| 10 | Run for 30 minutes | No memory growth, no latency creep (latency at t=30 min ≈ t=1 min) |

Useful Linux tools for these: `tc qdisc add dev eth0 root netem delay 50ms loss 2%` (simulate a bad tether), `stress-ng`, `dmesg -w`, `iperf3`, `htop`, `tegrastats`, `vcgencmd measure_temp`.

---

## 8. Debrief questions

1. Which technique found the most defects? Which found the **critical** ones?
2. Which defects would *your* ROV software probably also have?
3. Why did the 7 starter tests all pass, even though the code has many defects?
4. How did it feel to receive bug reports about "your" code? What made a report easy or hard to act on?
5. What is the one test you will add to your real ROV software this week?
