# Weekly Knowledge Exchange

*M.I.A Robotics · engineering practice · run by the mentors (alumni)*

**What it is.** One hour, every week, same day and time. Every sub-team says what it improved, then one or two members teach a topic they were assigned. It spreads knowledge that otherwise stays in one person's head, gives juniors a reason to go deep, and over a season builds next year's onboarding library.

## The hour

| Time | Part | Rules |
|---|---|---|
| 0–15 min | **Team updates** | Each sub-team (mechanical, electrical, software, GUI, CV, …) gets 2–3 minutes: **one technical enhancement** since last week (with a number if there is one: "camera switch now 0.4 s, was 1.8 s") and **one blocker**. Not a status report, and no slides. Blockers get an owner, not a discussion. |
| 15–50 min | **1–2 topic talks** | 15–20 min each, given by the member the topic was assigned to. Live demo beats slides. End with "how this applies to our ROV". |
| 50–60 min | **Q&A + next week** | Questions, then confirm next week's topics and presenters. |

## How topics are chosen and assigned

1. **Backlog.** Mentors keep the topics as GitHub issues labelled `knowledge`. Anyone can propose one: open an issue with the topic and why the team needs it.
2. **Assignment, two weeks ahead.** Mentors assign 1–2 topics a week. Match topics to people who need to learn them, not only to people who already know them. Pair a junior with a senior for hard topics.
3. **Outline review.** Three days before, the presenter sends the mentor a 5-line outline: the question, the 3 key points, the demo, and how it applies to our ROV.
4. **After the talk.** A one-page summary goes into `docs/knowledge/YYYY-MM-DD-topic.md` with the slides, and the recording goes to the team Drive. The issue is closed with links to both.

## Starter backlog

| Area | Topic |
|---|---|
| Streaming | RTP vs RTSP vs WebRTC on our tether · reading an encoder's frame sizes (Encoding Lab) · why we never shrink MJPEG in software |
| Hardware | Jetson Nano 2GB vs Pi 5 measurements · thermal design of the ROV computer enclosure · USB bandwidth with 8 cameras |
| Control | depth-hold PID tuning on real data · thruster mixing |
| Software | writing a pytest for the camera manager · reviewing a PR without reviewing the person · Git branching that survives competition week |
| GUI / UX | showing stale video honestly · the two metrics every camera tile needs (throughput, loss) |
| CV | dataset recording from MJPEG streams · what compression does to detection accuracy |

## Roles

- **Mentor of the month (an alumnus):** keeps the backlog, assigns topics, reviews outlines, keeps time.
- **Presenter:** prepares the talk and the one-page summary.
- **Note-taker (rotates):** writes down blockers and their owners during the updates and posts them in the team channel the same day.

## Is it working?

Review after a **6-week pilot**, in a retro, with numbers:

- topics delivered per month (target 4–6);
- share of members who have presented at least once this season (target: everyone by mid-season);
- how often a past talk is linked when answering a question or reviewing a PR;
- blockers raised in the updates that were resolved within a week.

Keep what works and drop what doesn't. The point is a faster team, not a perfect meeting.
