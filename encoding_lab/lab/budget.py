"""Tether and encoder budget planner: will these cameras fit the tether, and can the ROV computer encode them?

Everything here is a pure function of a camera list and a few settings, so the Lab's
*Bandwidth budget* tab and the tests use the same maths. The numbers are rules of thumb:

* **Bitrate** — bits-per-pixel × pixels × fps (``engine.camera_mbps``), times a quality tier,
  plus the transport's packet overhead. Calibrate bits-per-pixel with your own footage
  in the Encode tab.
* **Encoder load** — pixel rate against what the encode computer can do: the Jetson Nano's
  hardware budget (NVIDIA: 4 × 1080p30 ≈ 250 Mpx/s), or CPU cores for software x264
  (Raspberry Pi white paper, 28 Apr 2026: 1080p30 low-latency ≈ 0.62–0.9 of one Pi 5 core).
  A benchmark of *this* computer replaces the estimate when one has been run.
* **Packet loss** — every lost packet breaks an H.264/H.265 picture until the next keyframe
  (on average half a GOP); an MJPEG stream only loses that one frame.
* **Keyframe pile-up** — a keyframe is several times bigger than the frames around it. If the
  cameras start together with the same GOP, their keyframes land on the same frame.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import engine as E

HEADROOM = 0.70                      # plan to use at most 70 % of the CPU (the tether headroom is a setting)
IFRAME_RATIO = 6.0                   # keyframe ÷ neighbouring frame size, typical 5–10× for live H.264 without a VBV cap
CAMERA_ENCODER_PENALTY = 1.5         # a UVC camera's built-in H.264 encoder needs ≈ 1.5× the bits of x264 for the same picture
QUALITY = {"Lean": 0.6, "Standard": 1.0, "Crisp": 1.6}    # × the codec's bits-per-pixel (Standard ≈ SSIM 0.98 on our clip)
PAYLOAD_BYTES = {"RTP/UDP": 1400, "MPEG-TS/UDP": 1316, "WebRTC": 1200, "HTTP/TCP": 1448}
RESOLUTIONS = ["320×180", "640×360", "640×480", "800×600", "1280×720", "1920×1080", "2560×1440", "3840×2160"]


@dataclass(frozen=True)
class Pipeline:
    """How one camera's picture gets onto the tether."""
    key: str
    codec: str                       # what travels on the wire
    rov_encode: bool                 # the ROV computer runs a video encoder (H.264/H.265)
    jpeg_decode: bool                # the ROV computer decodes the camera's JPEGs
    jpeg_encode: bool                # the ROV computer re-encodes JPEGs (resize trap)
    help: str
    bpp_factor: float = 1.0


PIPELINES = {p.key: p for p in [
    Pipeline("MJPEG passthrough", "MJPEG", False, False, False,
             "The camera's own JPEGs are copied to the tether (mjpg-streamer input_uvc). Almost no CPU, most bits."),
    Pipeline("Camera H.264 (UVC)", "H.264", False, False, False,
             "The camera has a built-in H.264 encoder. No ROV CPU, but cruder compression and fewer knobs.", CAMERA_ENCODER_PENALTY),
    Pipeline("MJPEG → H.264 on ROV", "H.264", True, True, False,
             "Decode the camera's JPEGs and encode H.264 on the ROV. 5–8× fewer bits than MJPEG."),
    Pipeline("MJPEG → H.265 on ROV", "H.265", True, True, False,
             "Like H.264 with ≈ 20–30 % fewer bits; costs more CPU, and the pilot laptop must decode H.265."),
    Pipeline("MJPEG resized on ROV", "MJPEG", False, True, True,
             "The resolution trap: decode, shrink and re-encode every JPEG. Pays CPU and still sends MJPEG. "
             "Ask the camera for the smaller mode instead."),
]}


@dataclass(frozen=True)
class Computer:
    """What the ROV computer can encode. Hardware budgets are in Mpx/s; software costs in CPU cores per Mpx/s."""
    key: str
    cores: int
    hw_video_mpx: float = 0.0        # hardware H.264/H.265 encode budget (0 = no hardware encoder)
    hw_jpeg_mpx: float = 0.0         # hardware JPEG decode/encode budget
    h264_core_per_mpx: float = 0.0   # software x264 ultrafast + zerolatency
    h265_factor: float = 4.0         # x265 ultrafast ≈ 4× the CPU of x264 ultrafast
    jpeg_core_per_mpx: float = 0.0   # software JPEG decode (encode costs about the same)
    note: str = ""


# Pi 5: 1080p30 = 62.2 Mpx/s at ≈ 0.76 core (white paper midpoint) → 0.0122 core per Mpx/s.
# JPEG decode with libjpeg-turbo on a Cortex-A76 ≈ 130 Mpx/s per core.
PI5 = Computer("Raspberry Pi 5 (software x264)", 4, h264_core_per_mpx=0.0122, jpeg_core_per_mpx=0.0077,
               note="No hardware H.264 encoder: every stream costs CPU. Estimate from the Raspberry Pi white paper (Apr 2026).")
COMPUTERS = {c.key: c for c in [
    Computer("Jetson Nano 2GB (hardware NVENC)", 4, hw_video_mpx=249.0, hw_jpeg_mpx=600.0, jpeg_core_per_mpx=0.019,
             note="NVIDIA: 4 × 1080p30 or 9 × 720p30 H.264/H.265, JPEG 600 Mpx/s. Use GStreamer nvv4l2h264enc / nvv4l2decoder mjpeg=1."),
    PI5,
    Computer("Jetson Orin Nano (software!)", 6, h264_core_per_mpx=0.0135, jpeg_core_per_mpx=0.0085,
             note="Trap: the Orin Nano has NO hardware video encoder, so it encodes in software like a Pi 5 (6 cores)."),
]}


@dataclass
class Camera:
    """One row of the planner's camera table."""
    name: str
    pipeline: str
    stream_res: str
    fps: float
    quality: str = "Standard"
    gop_s: float = 1.0
    camera_res: str = ""             # what the camera captures; only matters when the ROV decodes its JPEGs
    on: bool = True

    @property
    def pipe(self) -> Pipeline:
        return PIPELINES[self.pipeline]


def parse_res(res: str) -> tuple[int, int]:
    w, h = str(res).replace("x", "×").split("×")
    return int(w), int(h)


def video_mbps(cam: Camera, bpp: dict[str, float] | None = None) -> float:
    """Video bitrate of one camera, before packet overhead."""
    if not cam.on:
        return 0.0
    bpp = bpp or E.DEFAULT_BPP
    w, h = parse_res(cam.stream_res)
    return E.camera_mbps(bpp[cam.pipe.codec] * QUALITY[cam.quality] * cam.pipe.bpp_factor, w, h, float(cam.fps))


def encoder_cost(cam: Camera, pc: Computer, measured_core_per_mpx: float | None = None) -> dict[str, float]:
    """Load this camera puts on the ROV computer: hardware Mpx/s and CPU cores."""
    out = {"hw_video_mpx": 0.0, "hw_jpeg_mpx": 0.0, "cores": 0.0}
    if not cam.on:
        return out
    p = cam.pipe
    sw, sh = parse_res(cam.stream_res)
    cw, ch = parse_res(cam.camera_res or cam.stream_res)
    out_mpx = sw * sh * cam.fps / 1e6
    in_mpx = cw * ch * cam.fps / 1e6
    per_mpx = measured_core_per_mpx or pc.h264_core_per_mpx
    jpeg_per_mpx = pc.jpeg_core_per_mpx if measured_core_per_mpx is None else measured_core_per_mpx * pc.jpeg_core_per_mpx / max(pc.h264_core_per_mpx, 1e-9)
    if p.jpeg_decode:
        if pc.hw_jpeg_mpx:
            out["hw_jpeg_mpx"] += in_mpx
        else:
            out["cores"] += in_mpx * jpeg_per_mpx
    if p.jpeg_encode:
        if pc.hw_jpeg_mpx:
            out["hw_jpeg_mpx"] += out_mpx
        else:
            out["cores"] += out_mpx * jpeg_per_mpx
    if p.rov_encode:
        if pc.hw_video_mpx:
            out["hw_video_mpx"] += out_mpx
        else:
            out["cores"] += out_mpx * per_mpx * (pc.h265_factor if p.codec == "H.265" else 1.0)
    return out


def load_fractions(total: dict[str, float], pc: Computer) -> dict[str, float]:
    """Share of each resource used: hardware budgets in full, CPU against cores × HEADROOM."""
    f = {"CPU": total["cores"] / (pc.cores * HEADROOM)}
    if pc.hw_video_mpx:
        f["Video encoder"] = total["hw_video_mpx"] / pc.hw_video_mpx
    if pc.hw_jpeg_mpx:
        f["JPEG engine"] = total["hw_jpeg_mpx"] / pc.hw_jpeg_mpx
    return f


def loss_impact(cam: Camera, wire_mbps: float, loss_pct: float, transport: str) -> dict[str, float | str]:
    """How often one camera glitches at a given packet-loss rate, and for how long."""
    if not cam.on or wire_mbps <= 0:
        return {"glitch_every_s": math.inf, "broken_pct": 0.0, "effect": "—"}
    pkts = wire_mbps * 1e6 / 8 / PAYLOAD_BYTES[transport]
    events = pkts * loss_pct / 100
    if transport == "HTTP/TCP":
        return {"glitch_every_s": 1 / events if events else math.inf, "broken_pct": 0.0, "effect": "stalls (retransmit)"}
    if cam.pipe.codec == "MJPEG":
        damage, effect = 1 / cam.fps, "one frame lost"
    else:
        damage, effect = cam.gop_s / 2 + 1 / cam.fps, f"broken ≈ {cam.gop_s / 2:.1f} s"
    broken = 1 - math.exp(-events * damage)
    return {"glitch_every_s": 1 / events if events else math.inf, "broken_pct": 100 * broken, "effect": effect}


def keyframe_pileup(cams: list[Camera], wire: list[float], link_mbps: float, control_mbps: float) -> dict[str, float]:
    """Worst case: every H.264/H.265 camera sends its keyframe in the same frame interval."""
    burst_bits, base_bits, interval = 0.0, control_mbps * 1e6 / 30, 1 / 30
    for cam, mbps in zip(cams, wire):
        if not cam.on or mbps <= 0:
            continue
        per_frame = mbps * 1e6 / cam.fps
        if cam.pipe.codec == "MJPEG":
            base_bits += mbps * 1e6 * interval
            continue
        n = max(cam.gop_s * cam.fps, 1)
        p_bits = per_frame * n / (n - 1 + IFRAME_RATIO)
        burst_bits += IFRAME_RATIO * p_bits
    need = burst_bits + base_bits
    can = link_mbps * 1e6 * interval
    return {"burst_mbps": need / interval / 1e6, "extra_ms": max(0.0, need - can) / (link_mbps * 1e6) * 1000}


@dataclass
class Plan:
    """Everything the tab shows, computed from the inputs."""
    rows: list[dict] = field(default_factory=list)
    video_wire: float = 0.0
    total: float = 0.0
    plan_mbps: float = 0.0
    loads: dict[str, float] = field(default_factory=dict)
    pileup: dict[str, float] = field(default_factory=dict)
    worst_broken: float = 0.0
    status: str = "good"
    headline: str = ""


def plan(cams: list[Camera], pc: Computer, link_mbps: float, headroom: float, control_mbps: float, transport: str,
         loss_pct: float, bpp: dict[str, float] | None = None, measured_core_per_mpx: float | None = None) -> Plan:
    """Bitrate, encoder load, loss and keyframe pile-up for the whole ROV."""
    P = Plan(plan_mbps=link_mbps * headroom)
    tot = {"hw_video_mpx": 0.0, "hw_jpeg_mpx": 0.0, "cores": 0.0}
    wires = []
    for c in cams:
        v = video_mbps(c, bpp)
        wire = v * (1 + E.OVERHEAD[transport])
        cost = encoder_cost(c, pc, measured_core_per_mpx)
        for k in tot:
            tot[k] += cost[k]
        li = loss_impact(c, wire, loss_pct, transport)
        wires.append(wire)
        P.rows.append({"Camera": c.name, "On": c.on, "Pipeline": c.pipeline, "Codec": c.pipe.codec, "Stream": f"{c.stream_res} @ {c.fps:g}",
                       "Mb/s": wire, "Cores": cost["cores"], "HW Mpx/s": cost["hw_video_mpx"] + cost["hw_jpeg_mpx"],
                       "Glitch every (s)": li["glitch_every_s"], "Broken %": li["broken_pct"], "On a lost packet": li["effect"]})
    P.video_wire = sum(wires)
    P.total = P.video_wire + control_mbps
    P.loads = load_fractions(tot, pc)
    P.pileup = keyframe_pileup(cams, wires, link_mbps, control_mbps)
    P.worst_broken = max([r["Broken %"] for r in P.rows if r["On"]] or [0.0])
    worst_load = max(P.loads.values()) if P.loads else 0.0
    if P.total > link_mbps or worst_load > 1 / HEADROOM:
        P.status = "bad"
    elif P.total > P.plan_mbps or worst_load > 1.0 or P.worst_broken > 5:
        P.status = "warn"
    parts = []
    parts.append("tether " + ("does NOT fit" if P.total > link_mbps else ("over plan" if P.total > P.plan_mbps else "fits")))
    parts.append("encoder " + ("overloaded" if worst_load > 1 / HEADROOM else ("over plan" if worst_load > 1.0 else "OK")))
    if P.worst_broken > 5:
        parts.append("loss hurts")
    P.headline = " · ".join(parts)
    return P


def suggestions(cams: list[Camera], pc: Computer, link_mbps: float, headroom: float, control_mbps: float, transport: str,
                loss_pct: float, bpp: dict[str, float] | None = None, measured_core_per_mpx: float | None = None, top: int = 6) -> list[dict]:
    """One-change fixes, ranked by bits saved: what each costs the pilot and the encoder."""
    base = plan(cams, pc, link_mbps, headroom, control_mbps, transport, loss_pct, bpp, measured_core_per_mpx)
    out = []
    for i, c in enumerate(cams):
        if not c.on:
            continue
        cands = []
        if c.fps > 10:
            cands.append((f"{c.name}: {c.fps:g} → {max(10, c.fps / 2):g} fps", {"fps": max(10.0, c.fps / 2)}, "less smooth"))
        ri = RESOLUTIONS.index(c.stream_res) if c.stream_res in RESOLUTIONS else -1
        if ri > 0:
            lower = RESOLUTIONS[ri - 1]
            how = "set the camera mode (v4l2-ctl), don't resize" if c.pipe.codec == "MJPEG" or not c.pipe.rov_encode else "less detail"
            cands.append((f"{c.name}: {c.stream_res} → {lower}", {"stream_res": lower, "pipeline": "MJPEG passthrough"
                          if c.pipeline == "MJPEG resized on ROV" else c.pipeline}, how))
        if c.pipe.codec == "MJPEG":
            cands.append((f"{c.name}: MJPEG → H.264 on the ROV", {"pipeline": "MJPEG → H.264 on ROV"}, "needs encoder capacity"))
        if c.quality != "Lean":
            lower_q = list(QUALITY)[list(QUALITY).index(c.quality) - 1]
            cands.append((f"{c.name}: quality {c.quality} → {lower_q}", {"quality": lower_q}, "softer picture"))
        for label, change, cost in cands:
            trial = [Camera(**{**vars(x), **change}) if j == i else x for j, x in enumerate(cams)]
            t = plan(trial, pc, link_mbps, headroom, control_mbps, transport, loss_pct, bpp, measured_core_per_mpx)
            saved = base.total - t.total
            if saved <= 0.05:
                continue
            load_delta = max(t.loads.values()) - max(base.loads.values())
            out.append({"Change": label, "Saves Mb/s": saved, "Encoder load": f"{max(t.loads.values()):.0%} ({load_delta:+.0%})",
                        "Trade-off": cost, "fits_encoder": max(t.loads.values()) <= 1.0})
    out.sort(key=lambda r: (not r["fits_encoder"], -r["Saves Mb/s"]))
    return out[:top]


def spare_streams(p: Plan, link_mbps: float, transport: str, bpp: dict[str, float] | None = None) -> int:
    """How many more 720p30 H.264 Standard streams fit in the planned tether budget."""
    one = video_mbps(Camera("x", "MJPEG → H.264 on ROV", "1280×720", 30), bpp) * (1 + E.OVERHEAD[transport])
    return max(0, int((p.plan_mbps - p.total) // one))


SCENARIOS: dict[str, tuple[str, list[Camera]]] = {
    "What we fly now: mjpg-streamer, USB cameras": ("Raspberry Pi 5 (software x264)", [
        Camera("Pilot", "MJPEG passthrough", "1280×720", 30), Camera("Manipulator", "MJPEG passthrough", "1280×720", 30),
        Camera("Rear", "MJPEG passthrough", "640×480", 15), Camera("Aux 1", "MJPEG resized on ROV", "640×360", 15, camera_res="1920×1080"),
    ]),
    "Recommended: Jetson Nano, H.264 in hardware": ("Jetson Nano 2GB (hardware NVENC)", [
        Camera("Pilot", "MJPEG → H.264 on ROV", "1920×1080", 30, camera_res="1920×1080"),
        Camera("Manipulator", "MJPEG → H.264 on ROV", "1280×720", 30, camera_res="1280×720"),
        Camera("Rear", "MJPEG → H.264 on ROV", "640×360", 15, camera_res="640×360"),
        Camera("Aux 1", "MJPEG → H.264 on ROV", "640×360", 15, camera_res="640×360"),
        Camera("Aux 2", "MJPEG passthrough", "640×480", 10), Camera("Aux 3", "MJPEG passthrough", "640×480", 10),
    ]),
    "Raspberry Pi 5: low-latency software": ("Raspberry Pi 5 (software x264)", [
        Camera("Pilot", "MJPEG → H.264 on ROV", "1280×720", 30, camera_res="1280×720"),
        Camera("Manipulator", "MJPEG → H.264 on ROV", "1280×720", 30, camera_res="1280×720"),
        Camera("Rear", "MJPEG passthrough", "640×480", 15), Camera("Aux 1", "MJPEG passthrough", "640×480", 10),
    ]),
    "Eight cameras, everything on": ("Jetson Nano 2GB (hardware NVENC)", [
        Camera("Pilot", "MJPEG → H.264 on ROV", "1920×1080", 30, camera_res="1920×1080"),
        Camera("Manipulator", "MJPEG → H.264 on ROV", "1280×720", 30, camera_res="1280×720"),
        Camera("Rear", "MJPEG → H.264 on ROV", "640×360", 15, camera_res="640×360"),
        Camera("Aux 1", "MJPEG → H.264 on ROV", "640×360", 15, camera_res="640×360"),
        Camera("Aux 2", "MJPEG → H.264 on ROV", "640×360", 15, camera_res="640×360"),
        Camera("Aux 3", "MJPEG passthrough", "640×480", 15), Camera("Aux 4", "MJPEG passthrough", "640×480", 10),
        Camera("Aux 5", "Camera H.264 (UVC)", "1280×720", 30),
    ]),
}

TETHERS = {   # name → typical measured TCP throughput (Mb/s); measure yours with iperf3
    "Fast Ethernet, 100BASE-TX (Cat5e)": 94.0,
    "Gigabit Ethernet (Cat5e/Cat6, all 4 pairs)": 940.0,
    "Powerline over 2 wires (Fathom-X / HomePlug AV)": 40.0,
    "Long or damaged tether (fell back)": 10.0,
}


def plan_markdown(p: Plan, cams: list[Camera], pc: Computer, link: float, headroom: float, control: float,
                  transport: str, loss_pct: float, fixes: list[dict]) -> str:
    """The plan as a Markdown reference card for the team docs or a GitHub issue."""
    L = ["# ROV tether and encoder budget", "",
         f"- Tether: **{link:g} Mb/s measured**, plan ≤ {headroom:.0%} = {p.plan_mbps:.1f} Mb/s; control + telemetry {control:g} Mb/s; {transport}",
         f"- Encode computer: **{pc.key}** ({pc.note})",
         f"- Expected packet loss: {loss_pct:g} %", "",
         f"**Verdict: {p.headline}.** Total {p.total:.1f} Mb/s = {p.total / link:.0%} of the tether. "
         + ", ".join(f"{k} {v:.0%}" for k, v in p.loads.items()) + " of the encode computer's planned capacity.", "",
         "| Camera | Pipeline | Stream | Mb/s on the wire | CPU cores | HW Mpx/s | Glitch every | Broken picture |",
         "|---|---|---|---:|---:|---:|---:|---:|"]
    for r in p.rows:
        if r["On"]:
            g = "never" if math.isinf(r["Glitch every (s)"]) else f"{r['Glitch every (s)']:.0f} s"
            L.append(f"| {r['Camera']} | {r['Pipeline']} | {r['Stream']} | {r['Mb/s']:.1f} | {r['Cores']:.2f} | {r['HW Mpx/s']:.0f} | {g} | {r['Broken %']:.1f} % |")
    L += ["", f"Keyframe pile-up (all keyframes in one frame): {p.pileup['burst_mbps']:.0f} Mb/s for 33 ms, "
              f"adds ≈ {p.pileup['extra_ms']:.0f} ms of delay. Stagger keyframes or use intra refresh.", ""]
    if fixes:
        L += ["## Cheapest fixes", "", "| Change | Saves | Encoder load after | Trade-off |", "|---|---:|---|---|"]
        L += [f"| {f['Change']} | {f['Saves Mb/s']:.1f} Mb/s | {f['Encoder load']} | {f['Trade-off']} |" for f in fixes]
    L += ["", "_Rules of thumb from the ROV Encoding Lab. Calibrate bits-per-pixel with your footage and measure the tether with iperf3._"]
    return "\n".join(L)
