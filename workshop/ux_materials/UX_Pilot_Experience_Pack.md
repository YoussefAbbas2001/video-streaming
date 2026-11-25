# UX Pilot Experience Pack — Designing Software Around the Pilot

> **“An excellent engineering system is not just one that works technically. It is one that allows its operator to use it effectively, confidently, and safely.”**

Contents: 1 Persona · 2 User journey · 3 From pain points to requirements · 4 Dashboard wireframe (before/after) · 5 Usability test script · 6 Activity: *Design the Perfect ROV Pilot Experience* · 7 UX scoring rubric · 8 UX evaluation checklist · 9 Example UX user stories · 10 Tools.
Printable wireframe: `pilot_dashboard_wireframe.svg` (open in any browser; print A3 landscape).

> The persona and journey below are **examples to start from**. Replace them with what you observe when you watch *your* pilots — a persona invented at a desk is a guess, not a finding.

---

## 1. Persona

**Mariam, 21 — primary pilot**
- 3rd-year mechatronics student; second MATE season; also helps with the electronics.
- Flies with a gamepad in both hands. Looks at the screen almost all the time; glances at the laptop keyboard only between tasks.
- Mission day: 15 minutes in the pool, judges watching, a co-pilot beside her operating the manipulator sometimes.

| | |
|---|---|
| **Goals** | Finish mission tasks quickly; never damage props or the vehicle; know at all times where the ROV is and what it's doing |
| **Frustrations** | Didn't notice a camera had frozen and steered on an old picture · has to hunt for depth/heading in small text · not sure whether the gripper actually closed · a mis-click on a configuration button during a mission |
| **Needs** | One big, sharp, low-latency view; a glanceable depth/heading/attitude display; honest camera and link states; dangerous actions that can't happen by accident |
| **Environment** | Bright poolside, laptop screen reflections, noise, time pressure, cold hands |

**Secondary stakeholders:** co-pilot (manipulator, tether), mission lead (timer, task list), engineers (debug views — *not* on the pilot's main screen), judges (safety).

---

## 2. User journey — one mission run

| Phase | Pilot does | Pilot needs to see | Pain points observed (example) | Emotion |
|---|---|---|---|---|
| 1. Pre-dive check | Power on, check cameras, arm/disarm test | All 8 cameras LIVE, link OK, leak sensor OK, battery/voltage | Has to open several tabs; a camera is black and nobody knows why | Anxious |
| 2. Launch & descend | Descend to working depth | Depth, heading, vertical speed, pilot camera | Depth readout is small and far from the video | Focused |
| 3. Navigate to task | Fly to the prop | Pilot camera (low latency), heading, maybe rear camera for the tether | Video lag makes her overshoot | Frustrated |
| 4. Manipulate | Grab / place objects | Manipulator camera large, pilot camera small, gripper state | Switches camera with the mouse — lets go of the gamepad | Stressed |
| 5. Something fails | A camera freezes / link drops | Unmistakable alarm, what failed, what still works | Frozen frame looked live for ~10 s | Panic |
| 6. Surface & recover | Ascend, manage tether | Depth, tether camera, link | — | Relieved |

---

## 3. From pain points to requirements

| Pain point | Requirement (testable) | Type |
|---|---|---|
| Frozen frame looked live | A camera with no new frame for > 1 s is marked **STALE/LOST** within 1 s; the last frame is greyed with an overlay | Functional + safety |
| Hunting for depth | Depth, heading, and attitude are overlaid on the primary video (HUD), readable at 1 m from the screen | Usability |
| Mouse needed to switch camera | Cameras 1–8 selectable from the gamepad and number keys; switch ≤ 1 s | Usability + performance |
| Unsure the gripper closed | Gripper shows **commanded** and **confirmed** state separately | Safety |
| Mis-click on configuration | PID/RC configuration is not reachable from the mission screen while armed | Error prevention |
| Video lag causes overshoot | Pilot camera latency ≤ 200 ms median (see the ROV experiments, Boss level N1) | Performance |

---

## 4. Pilot dashboard wireframe

**Before** (typical developer-built layout):

```
+---------+---------+---------+---------+
|  cam0   |  cam1   |  cam2   |  cam3   |
+---------+---------+---------+---------+
|  cam4   |  cam5   |  cam6   |  cam7   |
+---------+---------+---------+---------+
d:2.31 h:184 v:12.1 t:21.4 p:0.4 i:0.1 d:0.02 ...
[ARM] [STOP] [REC] [PID] [LIGHT] [RESET] [CFG] [GRIP]
```
Problems: no visual hierarchy (8 equal tiles); telemetry as cryptic text; every button the same weight — STOP looks like LIGHT, CFG reachable mid-mission; no camera state, no link state, no mode; nothing distinguishes a frozen tile from a live one.

**After** (one possible redesign — test it, don't trust it):

```
+----------------------------------------------------------------------------+
| ● LINK 94 Mb/s · 18 ms   MODE: DEPTH HOLD   ARMED   LEAK: OK      [E-STOP] |
+-----------------------------------------------------+----------------------+
|  PRIMARY · CAM 1 PILOT · LIVE                       | [2] MANIP   LIVE     |
|                                                     | [3] REAR    LIVE     |
|                         +                           | [4] AUX     DEGRADED |
|                                                     | [5] AUX     LOST ✖   |
|                                                     | [6] AUX     PAUSED   |
|  DEPTH 2.31 m ▲0.2 to target    HDG 184°    PITCH 2°| [7] [8] …            |
+-----------------------------------------------------+----------------------+
| GRIPPER  commanded: CLOSE · confirmed: CLOSED ✔   LIGHTS 60 %   REC ●      |
+----------------------------------------------------------------------------+
```
Design decisions: information hierarchy (one dominant view); HUD near the pilot's gaze; explicit states with text **and** colour (never colour alone); link/mode/armed always visible at the top; E-STOP separated, distinct, never moves; commanded vs confirmed; configuration lives on a separate screen that is locked while armed.

Layouts by mission phase (task workspaces, switched with one key; controls never move):
- **NAV** — primary + previews (above).
- **GRAB** — manipulator camera large, pilot camera picture-in-picture.
- **INSPECT** — inspection camera large + recording controls.

---

## 5. Usability test script (20–30 min per pilot)

**Participant:** a pilot who did **not** build the UI. **Roles:** facilitator (reads tasks, never helps), observer (times, counts errors, notes quotes), "computer" (for paper prototypes).

**Intro (read aloud):** *“We're testing the interface, not you. Please think aloud — say what you're looking for and what you expect to happen. I can't help you during the tasks.”*

| # | Task (give the goal, not the steps) | Success criterion | Time limit |
|---|---|---|---|
| T1 | “Make the rear camera the main view, then go back to the pilot camera.” | Both switches correct | 15 s |
| T2 | “One camera has a problem. Which one, and what kind of problem?” | Correct camera and state | 10 s |
| T3 | “What is the current depth and heading?” | Both values read correctly | 5 s |
| T4 | “Close the gripper and tell me when you're sure it has closed.” | Waits for confirmed state | 10 s |
| T5 | (Facilitator triggers) “link lost”, then “leak detected” — “What do you do?” | Notices within 2 s; correct response per team procedure | 10 s |

**Record per task:** success (✔/✖), time (s), errors (wrong camera/control, hesitation > 3 s), quotes.
**After:** System Usability Scale (SUS, 10 standard questions, 0–100); 3 open questions: *What was confusing? What did you look for and not find? What would you change first?*

**Analysis:** completion rate, median time, error count per task; top 3 problems by severity (blocks the task > slows > annoys). Five pilots usually reveal most major problems; test early with paper, again with the real UI.

---

## 6. Activity — *Design the Perfect ROV Pilot Experience* (40 min)

**Scenario (same for every team):**
> Your ROV has 8 cameras (pilot, manipulator, rear/tether, 5 auxiliary), depth, heading, pitch/roll, leak sensor, battery voltage, a gripper, and lights. The tether sometimes degrades and a camera occasionally disconnects. The pilot flies with a gamepad. Design the main mission screen.

**Requirements the design must support:** monitor multiple cameras · select the primary camera · control movement (show mode/armed state) · operate the manipulator (gripper state) · monitor critical telemetry · recognise connection failures · react to critical warnings.

**Schedule:**
1. **Brief** (5 min) — read the scenario; pick roles.
2. **Design** (20 min) — A3 paper wireframe (cut-out tiles and overlays for states) or a quick Figma/Penpot prototype. Prepare overlays for: camera LOST, link lost, leak alarm, gripper confirmed.
3. **Swap & test** (10 min) — another team sends a "pilot"; your team runs the §5 script: facilitator, observer (timer + error count), computer (swaps paper overlays when the pilot "acts").
4. **Score** (5 min) — with the rubric below; the visiting pilot fills in the "pilot feedback" row.

**Debrief:** *What surprised the designers? Which state was hardest to make obvious? What did the pilot look for first?*

---

## 7. UX scoring rubric (100 points)

| Criterion | Points | Full marks when… |
|---|---|---|
| Task completion | 25 | All 5 tasks completed (5 each) |
| Ease of use | 15 | Tasks within time limits; no hand moved off the gamepad for frequent actions |
| Information clarity | 15 | Pilot reads depth/heading and camera states at a glance; text + colour, never colour alone |
| Unnecessary interactions | 10 | Common actions take one input; no hunting through menus |
| Error prevention | 15 | Dangerous actions deliberate; E-stop distinct and fixed; config locked while armed |
| Situational awareness | 10 | Link, mode, armed, alarms always visible; stale/lost cameras unmistakable |
| Pilot feedback | 10 | Visiting pilot's 0–10 rating ("I would fly a mission with this") |

Deductions: −5 if the design ever shows a frozen frame as live; −5 if a command's success is shown before confirmation.

---

## 8. UX evaluation checklist (heuristic review of your real UI)

**Information hierarchy**
- [ ] The primary video is the dominant element; nothing competes with it.
- [ ] Critical telemetry (depth, heading, attitude) is near the pilot's gaze, large enough to read at 1 m.
- [ ] Critical alarms are visually distinct from ordinary information (and from warnings).

**Cognitive load**
- [ ] Common actions (switch camera, lights, gripper) take one input from the gamepad/keyboard.
- [ ] Debug/engineering data is not on the mission screen.
- [ ] Related controls are grouped; terminology is consistent everywhere.

**Situational awareness & feedback**
- [ ] Every camera shows its state in text: LIVE / DEGRADED / PAUSED / LOST / CONNECTING.
- [ ] A frame older than ~1 s is never presented as live (greyed + label).
- [ ] Telemetry shows its age or turns STALE when not updated.
- [ ] Link state (and ideally throughput/RTT) is always visible.
- [ ] Commanded vs confirmed state is shown for actuators (gripper, lights, arming).
- [ ] Loading / connecting / disconnected states exist for every stream and panel.

**Error prevention & recovery**
- [ ] Arming, PID/RC changes and other risky actions require a deliberate action (hold, two-step) and are disabled while flying where appropriate.
- [ ] E-stop is always visible, always in the same place, visually unique.
- [ ] Connection loss has a defined, visible behaviour on both ROV and UI; recovery is automatic and shown.
- [ ] Warnings and critical alarms are distinguishable (and alarms can't be silently dismissed).

**Consistency & customisation**
- [ ] Same colours, icons, labels and positions for the same things on every screen.
- [ ] Controls never move between layouts/modes.
- [ ] Layouts can be customised per pilot, with a known-good default and one-key reset.

**Accessibility & environment**
- [ ] Readable in a bright poolside environment (contrast; no thin grey-on-dark text for critical data).
- [ ] State is never conveyed by colour alone (colour-blind pilots).
- [ ] Works at the competition laptop's resolution and scaling.

---

## 9. Example UX user stories with acceptance criteria

**US-UX-1 — Disconnected cameras**
*As an ROV pilot, I want to identify disconnected cameras immediately so that I can react without wasting time.*
- Disconnected cameras have an unmistakable status indicator (text + colour + icon).
- The interface does not display a frozen frame as if it were live.
- The pilot receives clear feedback when a camera disconnects.
- Reconnection status is communicated (CONNECTING → LIVE).
- The remaining camera feeds continue functioning.
**DoD:** implemented; disconnection and reconnection tested on the real ROV; visual states reviewed; usability-tested with a pilot; no regressions in other camera feeds.

**US-UX-2 — Commanded vs confirmed gripper**
*As a pilot, I want to know whether the gripper has actually closed, so that I don't lift an object I haven't grabbed.*
- The UI shows the command as "requested" until the ROV acknowledges it.
- If no acknowledgement within ⟨500 ms⟩, the UI shows "NO CONFIRMATION".
- The confirmed state comes from the ROV's report, never from the button press.
**DoD:** tested with the link delayed (`tc netem delay 300ms`) and with acknowledgements dropped.

**US-UX-3 — Camera switching from the gamepad**
*As a pilot, I want to switch the primary camera from the gamepad, so that I never take my hands off the controls.*
- Buttons cycle/select cameras; the selected camera is primary within ≤ 1 s.
- The new primary is announced (label + highlight) so the pilot knows what they're looking at.
- Selecting a LOST camera shows "CAMERA LOST" instead of a black or frozen view.

**US-UX-4 — Link loss**
*As a pilot, I want an unmistakable indication when the link to the ROV is lost, so that I stop giving commands and follow the recovery procedure.*
- Within 1 s of link loss, a full-width banner appears; control inputs are visibly disabled.
- The banner shows time since loss; it clears automatically when the link returns.
- The ROV's own behaviour on link loss is defined and documented (designed with the control team).

---

## 10. Tools for designing before coding

| Tool | Use | Notes |
|---|---|---|
| Paper + sticky notes | first wireframes, fastest iteration | cut-out overlays for states |
| **Figma** | wireframes → high-fidelity mockups → clickable prototypes; components & design system | free education plan for students |
| **Penpot** | open-source alternative to Figma | runs in the browser or self-hosted |
| Excalidraw | quick sketch-style wireframes | free, no account needed |
| Your real UI in a "demo mode" | usability tests with recorded/simulated video | test the real thing as early as possible |

**Design system (small team edition):** one colour palette with reserved status colours (OK / warning / critical — never reused for anything else), one type scale (3–4 sizes), one spacing unit (e.g. 8 px), reusable components (camera tile with states, telemetry readout, status pill, confirm-button), and a page documenting them.
