"""Benchmarking and performance calculations for the Encoding Lab.

* system_info()        what machine is this (CPU, cores, RAM, board model, FFmpeg)
* hw_encoders()        which hardware H.264/H.265 encoders FFmpeg lists, and which ones actually work
* encoder_capacity()   one-core encode speed → how many real-time streams this computer can carry
* decode_speed()       how fast this computer decodes a stream (the pilot laptop's side)
* encoder_hold()       frames the encoder keeps before emitting the first one (measured with PyAV, else estimated)
* latency_budget()     glass-to-glass estimate, stage by stage, labelled measured / estimated / your input
* SysMon               live CPU per core, temperature, clock, Pi throttling, network Mb/s (reads /proc and /sys)
* report_markdown()    one Markdown report with everything above

Like engine.py, nothing here imports Streamlit, so every function is testable on its own.
"""
from __future__ import annotations

import glob
import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

from . import engine as E

HEADROOM = 0.70            # plan to use at most 70 % of CPU or link capacity
VIRTUAL_IFACES = ("lo", "ifb", "veth", "docker", "br-", "virbr", "tun", "tap")   # not a real tether
HW_ENCODERS = {
    "h264_nvenc": "NVIDIA GPU (desktop / laptop)", "hevc_nvenc": "NVIDIA GPU (desktop / laptop)",
    "h264_v4l2m2m": "V4L2 mem2mem (Raspberry Pi 4, some ARM boards)", "h264_vaapi": "Intel / AMD VA-API (Linux)",
    "h264_qsv": "Intel Quick Sync", "h264_videotoolbox": "Apple macOS", "h264_amf": "AMD (Windows)", "h264_omx": "OpenMAX (old Raspberry Pi OS)",
}
# x264 rate-control lookahead per preset (x264 defaults); used only when PyAV is unavailable
X264_LOOKAHEAD = {"ultrafast": 0, "superfast": 0, "veryfast": 10, "faster": 20, "fast": 30, "medium": 40, "slow": 50, "slower": 60, "veryslow": 60}


# ----------------------------------------------------------------------------- system
def _read(path: str) -> str:
    try:
        return Path(path).read_text(errors="ignore").strip("\x00\n ")
    except OSError:
        return ""


def system_info() -> dict:
    cpu = ""
    for line in _read("/proc/cpuinfo").splitlines():
        if line.lower().startswith(("model name", "hardware", "cpu model")):
            cpu = line.split(":", 1)[1].strip(); break
    mem_gb = None
    for line in _read("/proc/meminfo").splitlines():
        if line.startswith("MemTotal"):
            mem_gb = int(line.split()[1]) / 1024 / 1024; break
    board = _read("/proc/device-tree/model") or _read("/sys/firmware/devicetree/base/model")
    return {"Board": board or "PC / laptop (no device-tree model)", "CPU": cpu or platform.processor() or platform.machine(),
            "Logical cores": os.cpu_count() or 1, "RAM (GB)": round(mem_gb, 1) if mem_gb else None,
            "OS": f"{platform.system()} {platform.release()}", "Architecture": platform.machine(),
            "FFmpeg": " ".join(E.ffmpeg_version().split()[:3]), "Python": platform.python_version()}


_HW: list[dict] | None = None


def hw_encoders() -> list[dict]:
    """Listed ≠ working: try a 1-second test encode with every hardware encoder FFmpeg lists."""
    global _HW
    if _HW is not None:
        return _HW
    listed = E.run([E.FFMPEG, "-hide_banner", "-encoders"], check=False).stderr
    rows = []
    for name, what in HW_ENCODERS.items():
        if f" {name} " not in listed:
            rows.append({"encoder": name, "hardware": what, "listed by FFmpeg": False, "test encode": "—"}); continue
        try:
            p = subprocess.run([E.FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=1",
                                "-c:v", name, "-f", "null", "-"], capture_output=True, text=True, timeout=20)
            ok = p.returncode == 0
            lines = [l for l in p.stderr.strip().splitlines() if l and "Nothing was written" not in l and not l.startswith("Error opening output")]
            why = next((l.split("] ", 1)[-1] for l in lines if any(k in l for k in ("Cannot", "cannot", "No ", "not ", "Failed", "failed", "Error", "error"))), lines[0] if lines else "no device")
            note = "works ✅" if ok else f"fails ❌ ({why.strip()[:60]})"
        except subprocess.TimeoutExpired:
            note = "timed out ❌"
        rows.append({"encoder": name, "hardware": what, "listed by FFmpeg": True, "test encode": note})
    _HW = rows
    return rows


# ----------------------------------------------------------------------------- capacity
@dataclass
class Capacity:
    label: str
    width: int
    height: int
    fps: int
    one_core_fps: float          # frames per second ONE thread sustains
    ms_per_frame: float          # CPU milliseconds per frame
    streams_per_core: float      # real-time streams one core can carry
    streams_machine: float       # on all cores, at HEADROOM
    all_cores_fps: float         # encode speed using every core
    realtime_factor: float       # all-cores fps ÷ stream fps
    bitrate_mbps: float


def encoder_capacity(src: E.Source, s: E.EncodeSettings) -> Capacity:
    """Benchmark encode speed with ONE thread (clean per-core cost) and with all threads."""
    one = E.encode(src, E.EncodeSettings(**{**asdict(s), "threads": 1}), with_quality=False)
    allc = E.encode(src, E.EncodeSettings(**{**asdict(s), "threads": 0}), with_quality=False)
    frames = max(1, int(round(src.seconds * one.fps)))
    ms = 1000 * one.cpu_s / frames
    one_fps = frames / max(one.encode_s, 1e-6)
    per_core = (1000 / ms) / one.fps if ms > 0 else 0.0
    cores = os.cpu_count() or 1
    return Capacity(s.short(), one.width, one.height, one.fps, one_fps, ms, per_core, per_core * cores * HEADROOM,
                    allc.encode_fps, allc.encode_fps / one.fps, allc.bitrate_mbps)


def decode_speed(path: str | Path, threads: int = 1) -> dict:
    """Decode a file as fast as possible (no display) and report fps and CPU ms per frame."""
    r = E.run([E.FFMPEG, "-hide_banner", "-threads", str(threads), "-i", str(path), "-f", "null", "-"])
    import re
    m = re.findall(r"frame=\s*(\d+)", r.stderr)
    frames = int(m[-1]) if m else 0
    return {"frames": frames, "fps": frames / max(r.wall_s, 1e-6), "ms_per_frame": 1000 * r.cpu_s / max(frames, 1), "threads": threads}


# ----------------------------------------------------------------------------- encoder hold
def _pyav():
    try:
        import av  # noqa: F401
        return av
    except ImportError:
        return None


def encoder_hold(src: E.Source, s: E.EncodeSettings, max_frames: int = 90) -> dict:
    """How many input frames the encoder swallows before it emits the first packet.

    Measured by feeding frames one at a time through PyAV (if installed) with the same x264/x265 options;
    otherwise estimated from x264's preset defaults (lookahead + B-frames).
    """
    spec = E.CODECS[s.codec]
    fps = s.fps or src.fps
    av = _pyav()
    if av is not None and spec.encoder in ("libx264", "libx265"):
        w, h = src.width, src.height
        fsize = w * h * 3 // 2
        n = min(max_frames, src.frames)
        raw = np.fromfile(src.yuv, dtype=np.uint8, count=fsize * n)
        ctx = av.CodecContext.create(spec.encoder, "w")
        ctx.width, ctx.height, ctx.pix_fmt = w, h, "yuv420p"
        ctx.time_base = Fraction(1, src.fps); ctx.framerate = Fraction(src.fps, 1)
        opts = {"preset": s.preset}
        if s.zerolatency:
            opts["tune"] = "zerolatency"
        elif spec.encoder == "libx264":
            opts["bf"] = str(s.bframes)
        if spec.encoder == "libx264":
            opts["g"] = str(max(1, int(round(s.gop_s * src.fps))))
        if s.rate_mode == "crf":
            opts["crf"] = str(s.quality)
        else:
            opts["b"] = f"{s.bitrate_kbps}k"
        if spec.encoder == "libx265":
            opts["x265-params"] = "log-level=error"
        ctx.options = opts
        held, times = None, []
        for i in range(n):
            fr = av.VideoFrame.from_ndarray(raw[i * fsize:(i + 1) * fsize].reshape(h * 3 // 2, w), format="yuv420p")
            fr.pts = i
            t0 = time.perf_counter(); pk = ctx.encode(fr); times.append(time.perf_counter() - t0)
            if pk and held is None:
                held = i
        ctx.encode(None)
        held = n if held is None else held
        return {"frames": held, "ms": held * 1000 / fps, "method": "measured (PyAV)",
                "encode_call_ms": 1000 * float(np.median(times[min(5, len(times) - 1):])) if times else None}
    if spec.encoder == "mjpeg":
        return {"frames": 0, "ms": 0.0, "method": "by design (every frame is independent)", "encode_call_ms": None}
    est = 0 if s.zerolatency else X264_LOOKAHEAD.get(s.preset, 40) + (s.bframes if spec.encoder in ("libx264", "libx265") else 0)
    return {"frames": est, "ms": est * 1000 / fps, "method": "estimated (install PyAV to measure)", "encode_call_ms": None}


# ----------------------------------------------------------------------------- latency budget
def latency_budget(fps: float, hold_frames: float, encode_ms: float, avg_frame_bytes: float, peak_frame_bytes: float,
                   link_mbps: float, network_ms: float, jitter_ms: float, decode_ms: float, refresh_hz: float,
                   capture_frames: float = 1.0) -> list[dict]:
    """Glass-to-glass latency, stage by stage (typical case; the worst-case column adds the I-frame and a full refresh)."""
    frame_ms = 1000 / fps
    tx_avg = avg_frame_bytes * 8 / (link_mbps * 1e6) * 1000
    tx_peak = peak_frame_bytes * 8 / (link_mbps * 1e6) * 1000
    disp = 1000 / refresh_hz
    return [
        {"stage": "Capture (exposure + driver buffers)", "typical_ms": capture_frames * frame_ms, "worst_ms": (capture_frames + 1) * frame_ms, "source": "estimated"},
        {"stage": "Encoder hold (lookahead / B-frames)", "typical_ms": hold_frames * frame_ms, "worst_ms": hold_frames * frame_ms, "source": "measured"},
        {"stage": "Encode one frame", "typical_ms": encode_ms, "worst_ms": encode_ms * 1.5, "source": "measured"},
        {"stage": "Send over the tether", "typical_ms": float(tx_avg), "worst_ms": float(tx_peak), "source": "measured sizes · your link"},
        {"stage": "Network (switches, cable)", "typical_ms": network_ms, "worst_ms": network_ms * 2, "source": "your input"},
        {"stage": "Receiver jitter buffer", "typical_ms": jitter_ms, "worst_ms": jitter_ms, "source": "your input"},
        {"stage": "Decode", "typical_ms": decode_ms, "worst_ms": decode_ms * 1.5, "source": "measured"},
        {"stage": "Display (render + refresh)", "typical_ms": disp * 1.5, "worst_ms": disp * 2, "source": "estimated"},
    ]


# ----------------------------------------------------------------------------- live monitor
class SysMon:
    """Rates need two samples: call sample() once per refresh; it returns deltas since the previous call."""

    def __init__(self) -> None:
        self._cpu = self._read_cpu(); self._net = self._read_net(); self._t = time.time()

    @staticmethod
    def _read_cpu() -> dict[str, tuple[int, int]]:
        out = {}
        for line in _read("/proc/stat").splitlines():
            if line.startswith("cpu"):
                name, *v = line.split(); v = list(map(int, v))
                out[name] = (sum(v), v[3] + (v[4] if len(v) > 4 else 0))
        return out

    @staticmethod
    def _read_net() -> dict[str, tuple[int, int]]:
        out = {}
        for line in _read("/proc/net/dev").splitlines()[2:]:
            name, data = line.split(":", 1); f = data.split()
            out[name.strip()] = (int(f[0]), int(f[8]))
        return out

    @staticmethod
    def temps() -> dict[str, float]:
        t = {}
        for z in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
            kind, val = _read(f"{z}/type"), _read(f"{z}/temp")
            if val.lstrip("-").isdigit():
                t[kind or Path(z).name] = int(val) / 1000
        return t

    @staticmethod
    def freq_mhz() -> float | None:
        v = [int(x) / 1000 for f in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq") if (x := _read(f)).isdigit()]
        return sum(v) / len(v) if v else None

    @staticmethod
    def throttled() -> str | None:
        if not shutil.which("vcgencmd"):
            return None
        try:
            return subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2).stdout.strip().split("=")[1]
        except Exception:
            return None

    def sample(self) -> dict:
        cpu, net, t = self._read_cpu(), self._read_net(), time.time()
        dt = max(t - self._t, 1e-3)
        use = {}
        for k, (tot, idle) in cpu.items():
            t0, i0 = self._cpu.get(k, (tot, idle))
            use[k] = 100 * (1 - (idle - i0) / (tot - t0)) if tot > t0 else 0.0
        rates = {k: ((net[k][0] - self._net[k][0]) * 8 / dt / 1e6, (net[k][1] - self._net[k][1]) * 8 / dt / 1e6)
                 for k in net if k in self._net and not k.startswith(VIRTUAL_IFACES)}
        self._cpu, self._net, self._t = cpu, net, t
        temps = self.temps()
        return {"time": time.strftime("%H:%M:%S"), "cpu_total": use.get("cpu", 0.0),
                "cores": [v for k, v in sorted(use.items(), key=lambda kv: int(kv[0][3:]) if kv[0] != "cpu" else -1) if k != "cpu"],
                "temp_max": max(temps.values()) if temps else None, "temps": temps, "freq_mhz": self.freq_mhz(),
                "throttled": self.throttled(), "net": rates}


# ----------------------------------------------------------------------------- report
def report_markdown(sysinfo: dict, runs: list[dict], capacity: list[dict], hold: dict | None, budget: list[dict] | None,
                    decode: dict | None, hw: list[dict] | None) -> str:
    L = ["# ROV Encoding Lab: benchmark report", "", f"Generated {time.strftime('%Y-%m-%d %H:%M')}", "", "## This computer", ""]
    L += [f"- **{k}:** {v}" for k, v in sysinfo.items()]
    if hw:
        L += ["", "## Hardware encoders", "", "| Encoder | Hardware | Listed | Test encode |", "|---|---|---|---|"]
        L += [f"| {r['encoder']} | {r['hardware']} | {'yes' if r['listed by FFmpeg'] else 'no'} | {r['test encode']} |" for r in hw]
    if runs:
        L += ["", "## Encodes", "", "| Settings | Resolution | Mb/s | PSNR (dB) | SSIM | Encode fps | Cores | Ratio |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {r['label']} | {r['width']}×{r['height']}@{r['fps']} | {r['bitrate_mbps']:.2f} | {r['psnr'] or 0:.1f} | {r['ssim'] or 0:.4f} | "
              f"{r['encode_fps']:.0f} | {r['cores']:.1f} | {r['compression_ratio']:.0f}:1 |" for r in runs]
    if capacity:
        L += ["", "## Encoder capacity (one core → whole machine at 70 % headroom)", "",
              "| Settings | Resolution | fps on one core | CPU ms/frame | Streams per core | Streams on this machine | Real-time factor (all cores) |",
              "|---|---|---|---|---|---|---|"]
        L += [f"| {c['label']} | {c['width']}×{c['height']}@{c['fps']} | {c['one_core_fps']:.0f} | {c['ms_per_frame']:.1f} | {c['streams_per_core']:.2f} | "
              f"{c['streams_machine']:.1f} | {c['realtime_factor']:.1f}× |" for c in capacity]
    if decode:
        L += ["", f"## Decode speed", "", f"{decode['fps']:.0f} fps on {decode['threads']} thread(s), {decode['ms_per_frame']:.1f} CPU ms per frame."]
    if hold:
        L += ["", "## Encoder hold", "", f"{hold['frames']} frames ({hold['ms']:.0f} ms) — {hold['method']}."]
    if budget:
        tot = sum(b["typical_ms"] for b in budget); worst = sum(b["worst_ms"] for b in budget)
        L += ["", "## Glass-to-glass latency budget", "", "| Stage | Typical (ms) | Worst (ms) | Source |", "|---|---|---|---|"]
        L += [f"| {b['stage']} | {b['typical_ms']:.1f} | {b['worst_ms']:.1f} | {b['source']} |" for b in budget]
        L += [f"| **Total** | **{tot:.0f}** | **{worst:.0f}** | |", "", "Confirm with a real glass-to-glass measurement (photograph a phone stopwatch next to the pilot screen)."]
    L += ["", "> Speed and CPU numbers describe the computer that ran the lab. Run it on the ROV's computer for the numbers that matter."]
    return "\n".join(L)
