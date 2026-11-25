# 🧑‍🍳 Leader's Recipe: running the ROV experiments with your team

*M.I.A Robotics · for team leaders · 25 Nov 2026 · goes with the member handbook [ROV_Experiments.md](ROV_Experiments.md)*

> **You are not the one who measures. You are the one who makes measuring happen.** This recipe turns the 27 experiments into six weekly mini-workshops you run with your members, followed by a 6-week team challenge. Your members get the handbook; you get this page: what to prepare, what to say, what results to expect, and how to keep it safe and fun.

**Contents:** [What goes to whom](#what-goes-to-whom) · [Your three hats](#your-three-hats) · [Before the season](#before-the-season-one-time-about-2-hours) · [The standard session](#the-standard-session-90-minutes) · [The six sessions](#the-six-sessions) · [Answer key](#answer-key-what-to-expect-in-every-experiment) · [Being the referee](#being-the-referee-verifying-results) · [Keeping it fun](#keeping-it-fun) · [Adapting the recipe](#adapting-the-recipe) · [The boss level](#after-week-6-running-the-boss-level) · [Result sheet](#result-sheet-print-one-per-experiment)

---

## What goes to whom

| Who | Gets | Why |
|---|---|---|
| **Members** (in pairs) | [ROV_Experiments.md](ROV_Experiments.md), the handbook: every experiment with its question, steps and result table · one printed **mission map** per pair · [ms_clock.html](ms_clock.html) · the [result sheet](#result-sheet-print-one-per-experiment) | They do the measuring and explaining |
| **You, the leader** | This recipe · the [answer key](#answer-key-what-to-expect-in-every-experiment) (keep it to yourself until the debrief) · the [debug checklist](../debug/ROV_Debug_Checklist.md) and its health-check script | You prepare, coach, keep it safe and verify |
| **The whole team** | The leaderboard, read out at every weekly knowledge exchange | Visible progress keeps people coming back |

## Your three hats

1. **🧭 Facilitator.** Ask, don't tell. The answer key is for *your* confidence, not for reading out. A member who finds the number themselves remembers it; a member who is told it forgets it by Thursday.
2. **🦺 Safety officer.** You decide when thrusters spin, when `tc` rules go on, and when the hull opens. Nobody overrules the safety officer, and you check the clean-up before anyone leaves.
3. **⚖️ Referee.** You verify results and award points ([how](#being-the-referee-verifying-results)). Be generous with effort and strict with evidence.

---

## Before the season (one time, about 2 hours)

- [ ] **Read** the handbook once, end to end, and this recipe.
- [ ] **Install the tools** on the ROV computer and the topside laptop (the command is in the handbook's *Kit and setup*).
- [ ] **Run the health check** on the ROV and save its output: it is the team's day-0 baseline, and it may already show problems to fix before session 1.
  ```bash
  sudo bash docs/debug/rov_healthcheck.sh --top <topside IP> --cams <N> --md > baseline-health.md
  ```
- [ ] **GitHub:** create the labels (`bash docs/experiments/setup_experiment_labels.sh OWNER/REPO`), then open a test issue with the 🧪 *Experiment result* template and close it.
- [ ] **Pairs:** mix experienced and new members. Rotate pairs every two weeks so knowledge spreads.
- [ ] **Book the pool** for weeks 4 and 5 (or plan the [no-pool version](#adapting-the-recipe)).
- [ ] **Print:** one mission map per pair, the eye chart for E24 (letters and digits 40, 20, 10 and 5 mm high, laminated), result sheets, and the safety rules from the handbook for the wall.
- [ ] **Pack the kit box:**

| Item | For |
|---|---|
| Phone with slow-motion video (240 fps if possible) | E1, E4, E25, E26 |
| Spare monitor or second laptop for the ms clock | E1, E2, E5 |
| Multimeter | A5 in the checklist, E17 |
| Bucket, milk powder, small object, desk lamp or the ROV's lights | E22 |
| Grey card or white paper | E23 |
| Laminated eye chart, tape measure | E24 |
| An LED, a resistor (≈ 330 Ω), two jumper wires | E26 |
| Sticky notes and a marker | the prediction board |
| Prop guards or a tray to keep removed props | every bench session |
| A red cap, hat or lanyard | the `tc` operator in chaos week |

---

## The standard session (90 minutes)

Every session follows the same rhythm. Members learn the rhythm in week 1; after that you only change the experiments.

| Time | Step | You | Members |
|---|---|---|---|
| 0:00–0:10 | **🎯 Hook and predict** | Ask the session's big question (each session below has one). Everyone writes a number on a sticky note, with their name, and sticks it on the **prediction board**. | Predict alone, without discussing. |
| 0:10–0:15 | **Brief** | Why this matters for *our* ROV (use the handbook's *Why it matters*). The safety rules for today. Roles in each pair: operator and recorder (and a skeptic in groups of three). | Choose roles; open the handbook at their experiment. |
| 0:15–0:20 | **Pre-flight** | Run `rov_healthcheck.sh`. Fix any ❌ before measuring; a ❌ nobody knew about is already a 🐞 bonus for the team. | Watch: this is how a session starts in the pool too. |
| 0:20–1:00 | **Measure** | Walk between stations. Ask [coaching questions](#coaching-questions). Do not touch the keyboard. | Run the experiment; fill the result table; take photos. |
| 1:00–1:15 | **Explain** | Give each pair 2 minutes: the number, the reason, the surprise. | Present; the others ask one question each. |
| 1:15–1:25 | **Reveal and debrief** | Reveal the prediction board. Closest prediction gets the +5. Ask: *"What did we learn about our own ROV today?"* Write one action (an issue) on the board. | Discuss; agree the action. |
| 1:25–1:30 | **Post and clean up** | Check the clean-up: props, `tc qdisc show`, camera settings restored, ROV powered down. | Open the result issue before leaving, or hand you the paper sheet. |

**Golden rules (say them in week 1, repeat when needed)**

1. **Predict before you measure.** A wrong prediction is how intuition improves; it costs nothing.
2. **A number has units, a median, a worst case and conditions.** "About 100" is not a result.
3. **One change at a time.**
4. **A bug found is a win.** Celebrate it loudly; never blame the person whose code it is.
5. **Leave the ROV as you found it.**

### Coaching questions

When a pair is stuck, or done too quickly, ask one of these instead of giving the answer:

- *"Is that one measurement or the median of ten?"*
- *"What did you change, and what did you keep the same?"*
- *"Which stage of the chain causes this number: camera, encoder, network, player or screen?"*
- *"What could make this result wrong?"* (the skeptic's question)
- *"Would you get the same number tomorrow? In the pool? With the hull closed?"*
- *"If you had to make this number 2× better, what would you change first?"*
- *"Does this match your prediction? Why not?"*

---

## The six sessions

Plan on **4 to 12 members** (2 to 6 pairs). Each session runs as **stations**: each pair takes one experiment, and pairs swap halfway if the experiments are short. Not every pair must do every experiment: the replication bonus comes from a second pair repeating someone else's experiment later.

### Session 1 · Baseline: "Meet your ROV" (bench)

**Big question:** *"How late is the pilot's picture, in milliseconds?"*

| Station | Experiment | Time |
|---|---|---|
| Everyone, first 20 min | **E0** inventory: split the tables (computer · cameras · streams · topside) between the pairs, fill them in parallel, then merge | 20 min |
| A | **E1** glass-to-glass | 30 min |
| B | **E6** tether truth, then **E7** bandwidth census | 30 min |
| C | **E20** resolution trap, then **E21** USB bus limit | 30 min |

- **Prepare the day before:** ROV on the bench, props off, all cameras streaming to the GUI; `iperf3 -s` ready on the topside; ms clock open on a second screen.
- **Expect:** see the [answer key](#answer-key-what-to-expect-in-every-experiment). Usually at least one "unknown" in E0 and at least one surprise in E6 (a link at 100 Mb/s that should be 1 Gb/s, or errors).
- **Watch out for:** pairs filling E0 from memory or from the design document. *"Show me the command that says so."*
- **Debrief:** *"Which number surprised you? Which 'unknown' should we fix first?"*
- **Before next week:** every E0 table posted as one issue; it is the baseline for everything else.

### Session 2 · Latency and encoders (bench)

**Big question:** *"Where do the milliseconds go: camera, encoder, network, player or screen?"*

| Station | Experiment | Time |
|---|---|---|
| A | **E2** where do the milliseconds go? (needs the E1 method) | 60 min |
| B | **E3** encoder hold, then **E4** camera switch stopwatch | 30 + 30 min |
| C | **E9** MTU detective, then **E19** encoder capacity | 30 + 40 min |

- **Prepare:** `ffplay` and the Encoding Lab installed on the topside; a USB webcam for the Lab's live camera (E3).
- **Expect:** the network is the *smallest* part of latency on a tether; the player buffer and the encoder are the biggest. That surprises almost everyone; let them discover it.
- **Watch out for:** E2 pairs changing two things at once. E19 pairs forgetting that the test pattern also costs CPU.
- **Debrief:** draw the latency bar on the board, stage by stage, from E2's numbers. *"Which bar do we attack first?"*

### Session 3 · Chaos week (bench, props off)

**Big question:** *"When the network goes bad, does the pilot know?"*

| Station | Experiment | Time |
|---|---|---|
| A | **E10** packet-loss torture | 45 min |
| B | **E11** jitter vs the buffer | 45 min |
| C | **E12** the squeeze | 45 min |
| D (short) | **E13** pull the plug, **E14** does the UI tell the truth?, **E15** recording vs power cut | 20 min each |

- **Safety briefing (5 min, do not skip):** `tc` affects *all* traffic, including control. Props off. Only the person wearing the **red cap** types `tc` commands, one station at a time, and says them out loud.
- **Dead-man switch.** If you work over SSH on the same interface, a bad `tc` rule can lock you out. Always arm an automatic undo first:
  ```bash
  ( sleep 300; sudo tc qdisc del dev $IF root ) &      # removes the rule after 5 minutes, whatever happens
  sudo tc qdisc add dev $IF root netem loss 1%
  ```
- **Clean-up gate:** at the end, run `rov_healthcheck.sh` and look at **E7**. Nobody leaves until it is ✅.
- **Expect:** at least one 🐞 (a frozen frame shown as live, a stream that never recovers, control that stops at 2 Mb/s). Celebrate each one and open the issues together.
- **Debrief:** *"Which failure would hurt us most at competition? Which one do we fix first?"*

### Session 4 · Pool day 1

**Big question:** *"Does our video system still work after 30 minutes in the water with the hull closed?"*

| Station | Experiment | Time |
|---|---|---|
| Runs all session | **E16** 30-minute soak (start it first; read it at the end) | 30 min (in the background) |
| A | **E17** power under thruster load | 45 min |
| B | **E18** record footage for bits-per-pixel (finish the analysis at home) | 20 min + home |
| C | **E23** camera settings under water | 45 min |

- **Pool rules:** the usual pool safety for the team; a dedicated tether handler; thrusters only in the water; dry hands at the topside; nobody opens the hull at the pool.
- **Pre-dive:** health check before the ROV goes in, and at the 30-minute mark. Compare A1, A2 and B5.
- **Time is short at the pool:** set up everything on the bench the day before; bring the command lines printed or ready in a file.
- **Debrief (at the pool or the next day):** *"Bench or pool, what changed in our numbers?"*

### Session 5 · Pool day 2

**Big question:** *"What is the worst video the pilot can still work with?"*

| Station | Experiment | Time |
|---|---|---|
| A | **E24** eye test for the ROV | 45 min |
| B | **E25** pilot blind test (needs a pilot and a timed task) | 60 min |
| C | **E5** the long dive (latency drift), measured during the others | in the background |
| Before the pool | **E22** lights vs backscatter, in a bucket on the bench | 30 min |

- **Prepare:** the laminated eye chart and a way to hold it 1 m from the camera; a coin for the blind test; a hidden order sheet that only the recorder sees.
- **Watch out for:** the pilot memorising the eye chart. Use two charts, or cover rows.
- **Debrief:** the lowest readable bitrate from E24 becomes requirement **N2** for the boss level. Write it on the board and take a photo.

### Session 6 · Advanced and replication (bench)

**Big question:** *"Which of our results would we bet the competition on?"*

| Station | Experiment | Time |
|---|---|---|
| A | **E8** keyframe pile-up (Wireshark) | 90 min |
| B | **E26** the LED race | 90 min |
| C, D | **Replications**: pairs repeat another pair's experiment (+10 each if it matches) | 45 min each |

- **Debrief and season review:** read the leaderboard, announce ranks and badges, and choose the boss-level team. Ask: *"Which three numbers should go in our MATE technical documentation?"*

---

## Answer key: what to expect in every experiment

**For the leader only.** Typical results on a ROV like ours. **Your numbers may differ, and that is the point.** If a pair gets something far away from this, don't say "wrong": ask them to repeat it, or have another pair replicate it. They may have found something real.

| Exp | Time | Typical result | Common mistake to watch for | Debrief question |
|---|---|---|---|---|
| **E0** | 45–60 min | Several "unknown" answers (GOP, B-frames, who decodes on the topside). That is fine: each becomes a task | Filling it from memory or the design doc instead of running the commands | "What surprised you in our own system?" |
| **E1** | 30 min | MJPEG on a clean link: ≈ 60–120 ms. With a default player buffer (VLC caches 1000 ms) or x264 defaults: 300 ms to over 1 s | One photo only; clock digits blurred (auto exposure): make the clock big and bright | "Which stage do you think is the biggest?" (→ E2) |
| **E2** | 60 min | The network is ≈ 1 ms of it. The player buffer and the encoder are usually the biggest parts; a TV adds 50–150 ms | Changing two things at once | "Which bar do we cut first?" |
| **E3** | 45 min | x264 defaults hold about 1 s of frames at 30 fps (the Lab has measured 31 and 41 frames); zerolatency holds 0 | Forgetting B-frames on the ROV pipeline | "Why would an encoder *want* to wait?" (look-ahead, B-frames: better compression) |
| **E4** | 30 min | Up to one GOP plus any reconnect time; ≈ 0.5–1 s with GOP 1 s, several seconds with a long GOP | Judging by eye instead of counting slow-motion frames | "How would you make it instant?" (keyframe on request, or keep a small stream of every camera) |
| **E5** | 40 min (mostly waiting) | Flat with UDP and a GUI that keeps up; a straight rising line with TCP or a slow GUI | Restarting the GUI between measurements | "What grows if the line rises?" (a queue) |
| **E6** | 30 min | TCP ≈ 94 Mb/s on a 100 Mb/s link, ≈ 940 Mb/s on gigabit. Surprises: a link at 100 that should be 1000, half duplex, errors with thrusters on | Testing on a short bench cable instead of the real tether; testing the wrong direction | "Is our budget what we thought?" |
| **E7** | 30 min | MJPEG 720p30: often 10–40 Mb/s per camera depending on quality and scene; H.264: 1–4 Mb/s per camera | Measuring a still bench scene: bitrate rises in murky, moving water | "What is our total against E6?" |
| **E8** | 90 min | At 10 ms resolution the traffic is spiky: keyframes are several times bigger than other frames. Started together, the spikes line up every GOP | 1 s graph interval hides the spikes | "Why are average Mb/s not enough to plan a tether?" |
| **E9** | 30 min | Usually no fragments on a plain tether. Fragments appear with VPNs, some USB-Ethernet adapters or tunnels | Pinging with `-s 1500` (the 28-byte header is extra) | "What happens to a frame when one fragment is lost?" (the whole packet is lost) |
| **E10** | 60 min | 0.1 %: occasional smears; 1 %: frequent smears that last until the next keyframe; 5 %: mostly broken with long GOPs. MJPEG: single bad frames, recovers on the next one | Forgetting to remove netem; measuring loss on the wrong side | "GOP 1 s or 5 s for the pilot camera, and why?" |
| **E11** | 45 min | With 20 ± 10 ms jitter: no buffer stutters; a few tens of ms is smooth; every ms of buffer is added latency | Changing the jitter and the buffer together | "Where on the curve would you put the pilot camera? An aux camera?" |
| **E12** | 60 min | Without priorities all cameras break at once, ping rises to hundreds of ms and control lags. That is the bug to find | Squeezing below what SSH needs without the dead-man switch | "What should break first, and who decides?" |
| **E13** | 45 min | Often 2–4 of 6 drills need a restart the first time. Each one is an issue | Fixing it during the experiment instead of recording it | "Which failure would end our competition run?" |
| **E14** | 20 min | Many GUIs keep showing the last frame as if it were live: 🐞 | Freezing the GUI process instead of the encoder | "How would the pilot know?" |
| **E15** | 20 min | Plain MP4: unplayable ("moov atom not found"). MKV and fragmented MP4: play up to the cut | Stopping with Ctrl-C (a clean stop) instead of `kill -9` | "What does our recorder use today?" |
| **E16** | 45 min (30 waiting) | A Pi 5 without a cooler reaches its throttle point under continuous encoding; with a good heat path it stays well below. Latency should not change | Leaving the hull open | "What carries the heat out of our hull?" |
| **E17** | 45 min | Either nothing (good) or USB resets / under-voltage during thrust reversals | Testing with props out of water (light load) | "Do cameras share power with thrusters?" |
| **E18** | 60 min | A bits-per-pixel value for *our* water; compare with the Lab default 0.045. Murky, particle-rich water usually needs more | Re-encoding while recording (use `-c copy`) | "Is our footage harder than the Lab clip? Why?" |
| **E19** | 60 min | A number N at ≤ 70 % CPU; compare with [Hardware and encoders](../streaming/hardware-and-encoders.md#2-jetson-nano-2gb-vs-raspberry-pi-5-for-our-cameras) | Reading only the first second of `speed=` | "How many cameras can we really run at full quality?" |
| **E20** | 20 min | A (camera mode, copy) costs almost no CPU; B (decode → scale → encode) costs much more | Comparing different frame rates | "Which one does our current setup do?" |
| **E21** | 45 min | Raw YUYV 640×480@30 ≈ 147 Mb/s per camera, so one or two per USB 2 bus at most; MJPEG fits several | Plugging all cameras into one hub "because it is tidy" | "How should we wire the cameras?" |
| **E22** | 30 min | Light next to the lens: many bright specks; to the side and slightly behind: far fewer, better contrast, lower bitrate | Too much milk: start with a pinch | "Where are our lights today?" |
| **E23** | 60 min | Manual exposure and white balance: less noise, more stable colour, lower bitrate on a still scene | Changing settings and forgetting to restore them (`before.txt`) | "Should the pilot be able to change these during a dive?" |
| **E24** | 45 min | A minimum readable bitrate for the smallest mission marking: this becomes requirement N2 | The pilot memorises the chart | "What bitrate do we guarantee the pilot camera?" |
| **E25** | 90 min | Often the faster (lower latency) setting wins on time even when the sharper one wins on ratings | The pilot knows the order; too few attempts | "Do the pilot's ratings agree with the stopwatch?" |
| **E26** | 90 min | Video lags telemetry by roughly the video latency (≈ 100 ms or more) | Toggling too fast to tell the edges apart | "Should the overlay wait for the video?" |

---

## Being the referee: verifying results

Before you add the labels to a result issue, check:

- [ ] **Prediction** was written *before* the measurement (it is on the sticky note or the sheet from the session).
- [ ] **Repeats:** 10 for latency, 3 for most others. Median **and** worst, with **units**.
- [ ] **Conditions:** bench or pool, hull open or closed, how many cameras, software version.
- [ ] **Evidence:** a photo, screenshot, log or the filled table.
- [ ] **Explanation** names a stage and a reason, not just "it was slow".
- [ ] **Plausible** against the answer key. If not, ask for a repeat or a replication; don't reject it.

Then label it, and the board does the rest:

```bash
gh issue edit 123 --add-label "exp:E07,bonus:prediction"        # the experiment + any bonus
gh issue list --state all --label experiment --limit 500 --json number,title,labels,author > experiments.json
python3 docs/experiments/experiment_board.py experiments.json    # leaderboard, ranks, badges, experiments nobody has done
```

**Bonuses at a glance:** `bonus:prediction` (+5, within 20 %) · `bonus:replicated` (+10, give it to *both* pairs) · `bonus:bug` (+20, the defect is now an issue with a fix plan) · `bonus:chart` (+10, chosen at the knowledge exchange).

**Members without GitHub?** Collect the paper result sheets and post them yourself, with their names in the issue. Points still go to them.

---

## Keeping it fun

- **The prediction board.** Sticky notes on a wall, revealed at the end. The closest guess of the season gets a small prize.
- **Badge stickers.** Print the six badge emojis as stickers for laptops. People like collecting them more than points.
- **Promotions out loud.** Announce rank-ups (Technician, Engineer, Chief Engineer) at the knowledge exchange.
- **🐞 Bug bell.** Ring something when a real defect is found. Finding bugs is the goal, not an embarrassment.
- **Myth busters.** Start a session with a team myth and let the experiment confirm or bust it: *"lowering resolution fixes lag"* (E20), *"the network is the slow part"* (E2), *"MP4 is safe"* (E15).
- **New members drive.** Let the newest member be the operator first; the experienced one records.

**Avoid:** turning points into grades, punishing wrong predictions, doing the work yourself, or skipping the debrief because time ran out. The debrief is where the learning happens: cut measuring time first.

---

## Adapting the recipe

| Situation | Change |
|---|---|
| **Small team (2–4)** | One station at a time; spread each session over two meetings |
| **Large team (12+)** | Two parallel groups with a co-leader; one of them replicates the other's results the following week |
| **No pool** | E22–E24 in a bucket or a water tank; E16 with the hull closed on the bench in a warm room; E17 with the thrusters in a bucket of water, ROV restrained |
| **Only 45 minutes** | One experiment for everyone; keep the hook, the debrief and the clean-up; skip the stations |
| **No ROV available this week** | Do the Encoding Lab parts: E3 (live camera), E18 (upload old footage), the Packet-loss lab for E10, and the bandwidth budget |
| **Beginners only** | 🟢 experiments for the first two weeks, then 🟡 |
| **A member who can't attend** | Give them a replication, or the analysis part (charts from `soak.log`, the Wireshark graph) |

---

## After week 6: running the boss level

The boss level (weeks 7–12) is described in the handbook ([👑 Boss level](ROV_Experiments.md#-boss-level-the-6-week-challenge)). Your role changes from facilitator to **product owner**:

| Week | You do |
|---|---|
| 7 | Kick-off: form the team (video software + electronics + at least one pilot); agree the targets in N1–N7 using the season's numbers |
| 8–9 | Design review: insist on at least two options compared *with numbers* before any code |
| 9–11 | Weekly check: what is measured, what is blocked; remind them that a blocker on Monday is a 10-minute fix and on Friday a missed milestone |
| 11 | Dress rehearsal: run the Chaos Monkey drills (E12–E14) and the health check on the new system |
| 12 | Final demonstration, scored with the handbook's table; publish the before/after table at the knowledge exchange |

---

## Result sheet (print one per experiment)

```
EXPERIMENT E__ : ______________________________   Date: ________   Session: __
Pair: operator __________________  recorder __________________  skeptic ______________

PREDICTION (written before measuring, each person):  ____________  ____________  ____________

CONDITIONS:  ☐ bench  ☐ pool   ☐ hull open  ☐ hull closed   cameras streaming: __   thrusters: ☐ off ☐ on
             software version / commit: __________   health check: ☐ all ✅  ☐ problems: ______

RESULT:      median ________ (units)   worst ________   repeats: ____
             (attach the filled table from the handbook)

EVIDENCE:    ☐ photos  ☐ screenshots  ☐ logs  ☐ chart        where: ____________________

EXPLANATION: which stage causes this number, and why?
             __________________________________________________________________________
             __________________________________________________________________________

SURPRISE:    __________________________________________________________________________
NEXT QUESTION: ________________________________________________________________________

Leader:  ☐ verified   points ____   bonus: ☐ prediction ☐ replicated ☐ bug ☐ chart   issue #____
```

---

**Related:** [Member handbook: ROV experiments](ROV_Experiments.md) · [ROV Video Debug Checklist](../debug/ROV_Debug_Checklist.md) · [Measure and diagnose](../streaming/measure-and-diagnose.md) · [Knowledge exchange](https://github.com/YoussefAbbas2001/mia-software-practice/blob/HEAD/docs/knowledge-exchange.md)
