# Specification — `rov_core` (testing-competition module)

This is the **specification** the software must meet. When the code and this document disagree, **the code is wrong**. Your tests should check *this* behaviour.

Run the starter tests with:

```bash
pip install pytest
cd testing_competition_code
python -m pytest -q
```

---

## 1. `CameraManager`

### Construction
- `CameraManager(link_capacity_mbps=100, headroom=0.7)`.
- `link_capacity_mbps` must be > 0 and `headroom` must be in (0, 1]; otherwise raise `CameraError`.
- The **video budget** is `link_capacity_mbps × headroom` (e.g. 70 Mb/s on a 100 Mb/s link).

### Adding and removing cameras
- `add_camera(camera_id, width, height, fps, bitrate_mbps, priority=5)`.
- At most **8** cameras. Adding a 9th raises `CameraError`.
- A `camera_id` that already exists raises `CameraError` (it must **not** replace the existing camera).
- `width` must be 1…3840 and `height` 1…2160 (inclusive). Otherwise `CameraError`.
- `fps` must be 1…60 (inclusive). Otherwise `CameraError`.
- `bitrate_mbps` must be > 0. Otherwise `CameraError`.
- A camera may only be added if the **sum of all cameras' bitrates, including the new one, is ≤ the video budget** (link × headroom). Otherwise `CameraError`.
- A new camera starts in state `CONNECTING`.
- `remove_camera(camera_id)` removes the camera completely. Removing an unknown camera raises `CameraError`. After removal, every other method must keep working (no crash), and if it was primary, there is no primary.

### Camera state
- `mark_live(id)` → `LIVE`; `on_disconnect(id)` → `LOST`; `on_reconnect(id)` → `CONNECTING`.
- Any method called with an unknown camera id raises `CameraError`.

### Primary camera
- `set_primary(id)` makes the camera primary **only if it is `LIVE`**; otherwise raise `CameraError` and keep the previous primary.
- `primary_is_live()` returns `True` **only** if there is a primary camera **and** its state is `LIVE`. (The pilot UI uses this to decide whether to show the primary video as live or to show a "camera lost" banner. Showing a frozen frame as live is a **critical** defect.)

### Bandwidth
- `total_bitrate()` returns the sum of bitrates of cameras that are **`LIVE` or `CONNECTING`** (a `LOST` camera sends nothing).
- `budget_mbps()` returns link × headroom.
- `allocate(budget_mbps, minimum_mbps=0.2)` returns `{camera_id: Mb/s}` for every `LIVE` camera:
  - cameras are served in priority order (priority 1 = most important; ties: lower `camera_id` first);
  - each camera gets `min(its bitrate, remaining budget)` **if** at least `minimum_mbps` remains, otherwise `0.0` (paused);
  - the sum of the allocation never exceeds `budget_mbps`;
  - non-`LIVE` cameras do not appear in the result.

---

## 2. `CommandValidator`

### Arming and link
- The validator starts **disarmed** and with **no heartbeat**.
- `heartbeat(now_s)` records the time of the last heartbeat from the ROV.
- `link_alive(now_s)` is `True` only if a heartbeat has been received **and** `now_s − last_heartbeat < link_timeout_s` (strictly less). At exactly the timeout, the link is considered **lost**.

### Validation — `validate(command: dict, now_s) -> dict`
- If the link is not alive → raise `CommandRejected`.
- Allowed keys: `surge`, `sway`, `heave`, `yaw`, `gripper`. **Any other key → `CommandRejected`.**
- Axis values must be real numbers (not `bool`, not `NaN`, not `±inf`) in **[−1.0, +1.0]** inclusive. Otherwise `CommandRejected`.
- If the vehicle is **disarmed**, any **non-zero** axis value (**all four axes**) → `CommandRejected`. Zero values are allowed while disarmed.
- `gripper` must be one of `open`, `close`, `hold`. Otherwise `CommandRejected`.
- The returned dict contains exactly the validated keys, with axis values as `float`.
- Sending NaN or an out-of-range value to the thrusters is a **critical** defect.

---

## 3. Severity guide (for bug reports)

| Severity | Meaning | Examples |
|---|---|---|
| **Critical** | Could cause unsafe vehicle behaviour, a crash, or the pilot believing something false | NaN reaches thrusters; frozen camera reported live; crash on normal use |
| **Major** | Wrong result in a realistic situation, with a workaround | bandwidth budget miscalculated; 9th camera accepted |
| **Minor** | Wrong at an edge, low impact | boundary off by one at an unlikely value |
