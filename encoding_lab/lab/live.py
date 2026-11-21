"""Live camera pipeline for the Encoding Lab: camera → (decode → scale →) encode → (decode →) browser.

The point of this module is to make every stage of a live pipeline *visible and timed*:

    camera ──JPEG──► [decode] ─► [scale] ─► [encode] ──packets──► [pilot decode] ─► browser
       │                                                                              ▲
       └──────────────── MJPEG passthrough: the camera's JPEG goes straight there ────┘

* Capture runs in an FFmpeg CLI subprocess. It asks the camera for its own MJPEG mode and copies
  it untouched (`-c:v copy`), exactly like a well-configured ROV sender. Cameras without MJPEG
  fall back to raw frames. A test pattern and a looped clip simulate an MJPEG camera.
* Processing runs in one worker thread with PyAV, so each stage gets its own clock:
  JPEG decode, scaling, encoder latency (including frames the encoder holds back), the pilot-side
  decode, output size and bitrate.
* A tiny HTTP server serves the result as an MJPEG stream (`/stream.mjpg`) plus live numbers as
  JSON (`/stats`) for the head-up display drawn by the browser.

Nothing here imports Streamlit. One `LiveManager` per process (the camera can only be opened once).
Thread model: the reader thread owns the FFmpeg pipe, the worker thread owns every PyAV codec,
HTTP handler threads only read snapshots taken under `_lock`.
"""
from __future__ import annotations

import io
import json
import os
import platform
import re
import socket
import subprocess
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from . import engine as E

try:  # PyAV does the per-frame work; the rest of the lab works without it
    import av
    HAVE_AV = True
except ImportError:  # pragma: no cover - reported in the UI
    av = None
    HAVE_AV = False

PASSTHROUGH = "mjpeg-pass"
os.environ.setdefault("SVT_LOG", "1")          # SVT-AV1: errors only, keep the console readable
DECODER_FOR = {"H.264": "h264", "H.265": "hevc", "AV1": "libdav1d", "MJPEG": "mjpeg"}   # what the pilot laptop runs


# ----------------------------------------------------------------------------- encoders
@dataclass(frozen=True)
class LiveEncoder:
    """One choice in the encoder picker."""
    key: str            # PyAV encoder name, or PASSTHROUGH
    label: str
    codec: str          # what travels on the wire
    hardware: str       # "" for software
    pix_fmt: str        # pixel format the encoder wants
    blurb: str


ENCODERS: dict[str, LiveEncoder] = {e.key: e for e in [
    LiveEncoder(PASSTHROUGH, "MJPEG passthrough", "MJPEG", "camera chip", "",
                "The camera's own JPEGs go straight to the screen: no decode, no encode, almost no CPU. Biggest bitrate."),
    LiveEncoder("mjpeg", "MJPEG re-encode", "MJPEG", "", "yuvj420p",
                "Decode the camera's JPEG, (resize,) encode a new JPEG. What mjpeg-streamer and OpenCV pipelines do every frame."),
    LiveEncoder("libx264", "H.264 · x264", "H.264", "", "yuv420p", "The reference software encoder. Fast presets + zerolatency for live video."),
    LiveEncoder("h264_nvenc", "H.264 · NVENC", "H.264", "NVIDIA GPU", "yuv420p", "NVIDIA's hardware encoder: almost no CPU, very low latency."),
    LiveEncoder("hevc_nvenc", "H.265 · NVENC", "H.265", "NVIDIA GPU", "yuv420p", "H.265 on the NVIDIA encoder: fewer bits than H.264 at the same quality."),
    LiveEncoder("h264_qsv", "H.264 · Quick Sync", "H.264", "Intel GPU", "nv12", "Intel's hardware encoder (most Intel laptops)."),
    LiveEncoder("h264_amf", "H.264 · AMF", "H.264", "AMD GPU", "nv12", "AMD's hardware encoder (Windows)."),
    LiveEncoder("h264_videotoolbox", "H.264 · VideoToolbox", "H.264", "Apple", "nv12", "Apple's hardware encoder (macOS)."),
    LiveEncoder("h264_v4l2m2m", "H.264 · V4L2 M2M", "H.264", "SoC (Pi 4 etc.)", "yuv420p", "Linux mem2mem hardware encoder on ARM boards (Raspberry Pi 4; not Pi 5)."),
    LiveEncoder("libx265", "H.265 · x265", "H.265", "", "yuv420p", "Software H.265: fewer bits, much more CPU."),
    LiveEncoder("libsvtav1", "AV1 · SVT-AV1", "AV1", "", "yuv420p", "Software AV1: the most efficient, the most CPU."),
]}

_PROBED: dict[str, tuple[bool, str]] = {}


def encoder_options(key: str, *, preset_speed: int, zerolatency: bool, bitrate_kbps: int, fps: int, mjpeg_q: int) -> dict[str, str]:
    """Encoder-specific options for one speed / latency choice.

    preset_speed: 1 (fastest, least efficient) … 5 (slowest that is still live-friendly).
    """
    x264 = ["ultrafast", "superfast", "veryfast", "faster", "fast"][preset_speed - 1]
    nv = f"p{preset_speed}"                       # p1 fastest … p7 best
    rate = {"b": f"{bitrate_kbps}k", "maxrate": f"{bitrate_kbps}k", "bufsize": f"{max(1, bitrate_kbps // 2)}k"}
    if key == "mjpeg":
        return {"qmin": str(mjpeg_q), "qmax": str(mjpeg_q)}
    if key == "libx264":
        o = {"preset": x264, **rate}
        if zerolatency:
            o.update({"tune": "zerolatency", "bf": "0"})
        return o
    if key in ("h264_nvenc", "hevc_nvenc"):
        o = {"preset": nv, "rc": "cbr", **rate}
        o.update({"tune": "ull", "zerolatency": "1", "delay": "0", "bf": "0"} if zerolatency else {"tune": "hq"})
        return o
    if key == "h264_qsv":
        return {"preset": ["veryfast", "veryfast", "faster", "fast", "medium"][preset_speed - 1], **rate,
                **({"async_depth": "1", "look_ahead": "0", "bf": "0"} if zerolatency else {})}
    if key == "h264_amf":
        return {"usage": "ultralowlatency" if zerolatency else "transcoding", "quality": "speed" if preset_speed <= 2 else "balanced", **rate}
    if key == "h264_videotoolbox":
        return {"realtime": "1" if zerolatency else "0", **rate}
    if key == "libx265":
        return {"preset": x264, **rate, "x265-params": "log-level=error", **({"tune": "zerolatency"} if zerolatency else {})}
    if key == "libsvtav1":   # VBR only (no maxrate); pred-struct=1 = low delay
        if zerolatency:      # low-delay prediction requires CBR in SVT-AV1
            return {"preset": str(13 - preset_speed), "svtav1-params": f"pred-struct=1:rc=2:tbr={bitrate_kbps}"}
        return {"preset": str(13 - preset_speed), "b": f"{bitrate_kbps}k"}
    return dict(rate)


def probe_encoder(key: str) -> tuple[bool, str]:
    """Listed ≠ working: open the encoder and push a few frames through it. Cached per process."""
    if key == PASSTHROUGH:
        return True, "no encoder needed"
    if not HAVE_AV:
        return False, "PyAV not installed (pip install av)"
    if key in _PROBED:
        return _PROBED[key]
    spec = ENCODERS[key]
    if key not in av.codecs_available:
        _PROBED[key] = (False, "not in this PyAV/FFmpeg build")
        return _PROBED[key]
    logs: list = []
    try:
        prev_level = av.logging.get_level()
        av.logging.set_level(av.logging.ERROR)     # PyAV forwards nothing unless a level is set
        cap = av.logging.Capture()
        logs = cap.__enter__()
        ctx = av.CodecContext.create(key, "w")
        ctx.width, ctx.height, ctx.pix_fmt = 640, 360, spec.pix_fmt
        ctx.time_base = Fraction(1, 30); ctx.framerate = Fraction(30, 1)
        ctx.options = encoder_options(key, preset_speed=1, zerolatency=True, bitrate_kbps=1000, fps=30, mjpeg_q=5)
        ctx.open()
        img = np.zeros((360, 640, 3), np.uint8)
        got = 0
        for i in range(4):
            f = av.VideoFrame.from_ndarray(img, format="rgb24").reformat(format=spec.pix_fmt)
            f.pts = i
            got += len(ctx.encode(f))
        got += len(ctx.encode(None))
        _PROBED[key] = (got > 0, "works" if got else "opened but produced no packets")
    except Exception as exc:  # the reason is shown to the user
        _PROBED[key] = (False, _reason(exc, logs))
    finally:
        try:
            cap.__exit__(None, None, None)
            av.logging.set_level(prev_level)
        except NameError:
            pass
    return _PROBED[key]


def _reason(exc: Exception, logs) -> str:
    """The most useful line: FFmpeg's own error log ("Cannot load libcuda.so.1") beats PyAV's errno text."""
    lines = [str(m[2]).strip() for m in (logs or []) if len(m) > 2 and m[0] <= av.logging.ERROR] if HAVE_AV else []
    keys = ("Cannot", "cannot", "No ", "not ", "Failed", "failed", "unsupported", "Unsupported", "Error", "error")
    why = next((l for l in lines if any(k in l for k in keys)), lines[0] if lines else "")
    return (why or getattr(exc, "strerror", None) or type(exc).__name__)[:110]


def available_encoders() -> dict[str, tuple[bool, str]]:
    return {k: probe_encoder(k) for k in ENCODERS}


# ----------------------------------------------------------------------------- cameras
def list_cameras() -> list[tuple[str, str]]:
    """[(label, device spec)] for this OS. The spec is what `capture_command` expects."""
    system = platform.system()
    out: list[tuple[str, str]] = []
    try:
        if system == "Windows":
            p = subprocess.run([E.FFMPEG, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                               capture_output=True, text=True, timeout=15)
            for line in p.stderr.splitlines():
                m = re.search(r'"([^"]+)"\s+\(video\)', line)
                if m:
                    out.append((m.group(1), f"dshow:{m.group(1)}"))
        elif system == "Darwin":
            p = subprocess.run([E.FFMPEG, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                               capture_output=True, text=True, timeout=15)
            for line in p.stderr.split("audio devices")[0].splitlines():
                m = re.search(r"\[(\d+)\]\s+(.+)$", line)
                if m and "Capture screen" not in m.group(2):
                    out.append((m.group(2).strip(), f"avfoundation:{m.group(1)}"))
        else:
            import glob
            for dev in sorted(glob.glob("/dev/video*"), key=lambda d: int(re.sub(r"\D", "", d) or 0)):
                try:
                    name = open(f"/sys/class/video4linux/{os.path.basename(dev)}/name").read().strip()
                except OSError:
                    name = ""
                out.append((f"{dev}" + (f" · {name}" if name else ""), f"v4l2:{dev}"))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return out


SYNTHETIC = {"Test pattern (simulated MJPEG camera)": "test:", "Lab clip, looped (simulated MJPEG camera)": "clip:"}


def capture_command(device: str, width: int, height: int, fps: int, want_mjpeg: bool, clip: str | None = None) -> tuple[list[str], bool]:
    """FFmpeg command that writes the camera to stdout. Returns (command, output_is_jpeg).

    MJPEG cameras: `-c:v copy` into a multipart stream, so the bytes are the camera's own JPEGs.
    Raw cameras: fixed-size yuv420p frames.
    """
    kind, _, spec = device.partition(":")
    head = [E.FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin"]
    if kind in ("test", "clip"):
        src = (["-re", "-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate={fps}"] if kind == "test" else
               ["-re", "-stream_loop", "-1", "-i", clip or "", "-vf", f"scale={width}:{height},fps={fps}"])
        # the "camera chip" makes the JPEGs here, in its own process, like a real UVC camera
        return head + src + ["-c:v", "mjpeg", "-q:v", "5", "-pix_fmt", "yuvj420p", "-f", "mpjpeg", "pipe:1"], True
    if kind == "dshow":
        inp = ["-f", "dshow", "-rtbufsize", "64M", "-video_size", f"{width}x{height}", "-framerate", str(fps)]
        inp += (["-vcodec", "mjpeg"] if want_mjpeg else []) + ["-i", f"video={spec}"]
    elif kind == "avfoundation":       # macOS cameras deliver raw frames only
        inp, want_mjpeg = ["-f", "avfoundation", "-framerate", str(fps), "-video_size", f"{width}x{height}", "-i", f"{spec}:none"], False
    else:
        inp = ["-f", "v4l2"] + (["-input_format", "mjpeg"] if want_mjpeg else []) + ["-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", spec]
    if want_mjpeg:
        return head + inp + ["-an", "-c:v", "copy", "-f", "mpjpeg", "pipe:1"], True
    return head + inp + ["-an", "-vf", f"scale={width}:{height}", "-pix_fmt", "yuv420p", "-f", "rawvideo", "pipe:1"], False


def read_multipart_jpegs(stream, on_jpeg, stop: threading.Event) -> None:
    """Parse FFmpeg's mpjpeg output (headers carry Content-length) and call on_jpeg(bytes) per frame."""
    while not stop.is_set():
        line = stream.readline()
        if not line:
            return
        if not line.lower().startswith(b"content-length"):
            continue
        n = int(line.split(b":", 1)[1].strip())
        while stream.readline().strip():       # rest of the part headers
            pass
        data = stream.read(n)
        if len(data) < n:
            return
        on_jpeg(data)


# ----------------------------------------------------------------------------- config + stats
@dataclass
class LiveConfig:
    device: str = "test:"
    width: int = 1280
    height: int = 720
    fps: int = 30
    camera_mjpeg: bool = True          # ask the camera for MJPEG (else raw frames)
    encoder: str = PASSTHROUGH
    out_scale: float = 1.0             # < 1: shrink after capture (needs decode + encode)
    bitrate_kbps: int = 2000
    gop_s: float = 1.0
    preset_speed: int = 2              # 1 fastest … 5
    zerolatency: bool = True
    mjpeg_q: int = 5                   # 2 (best) … 31
    clip: str | None = None

    def needs_transcode(self) -> bool:
        return self.encoder != PASSTHROUGH or self.out_scale != 1.0 or not self.camera_mjpeg

    def label(self) -> str:
        enc = ENCODERS[self.encoder].label
        if self.encoder == PASSTHROUGH and self.needs_transcode():
            enc = "MJPEG re-encode"
        size = f"{int(self.width * self.out_scale) // 2 * 2}×{int(self.height * self.out_scale) // 2 * 2}"
        return f"{enc} · {size}@{self.fps}"


@dataclass
class FrameStat:
    t: float
    in_bytes: int
    out_bytes: int
    key: bool
    decode_ms: float
    scale_ms: float
    encode_ms: float | None      # time the frame spent inside the encoder (incl. hold), when it came out
    pilot_ms: float
    hold: int


@dataclass
class RunSummary:
    pipeline: str
    encoder: str
    hardware: str
    resolution: str
    fps: float
    mbps: float
    bpp: float
    encode_ms: float
    encode_p95: float
    hold_frames: int
    decode_scale_ms: float
    cpu_pct: float
    drops: int
    seconds: float


def _pct(a: list[float], q: float) -> float:
    return float(np.percentile(a, q)) if a else 0.0


# ----------------------------------------------------------------------------- the pipeline
class LivePipeline:
    """One running camera pipeline. Create, start(), read snapshot()/latest_jpeg(), stop()."""

    WINDOW_S = 1.0

    def __init__(self, cfg: LiveConfig):
        self.cfg = cfg
        self.status = "starting"
        self.error = ""
        self.camera_desc = ""
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._new = threading.Condition(self._lock)
        self._in: tuple[float, bytes | np.ndarray] | None = None     # latest captured frame (reader → worker)
        self._jpeg: bytes | None = None                              # latest display JPEG (worker → HTTP)
        self._seq = 0
        self._stats: deque[FrameStat] = deque(maxlen=900)
        self.history: deque[dict] = deque(maxlen=300)                # one entry per second
        self._captured = 0
        self._processed = 0
        self._drops = 0
        self._t_start = 0.0
        self._cpu0 = (0.0, 0.0)
        self._proc: subprocess.Popen | None = None
        self._threads: list[threading.Thread] = []
        self.out_w = max(2, int(cfg.width * cfg.out_scale) // 2 * 2)
        self.out_h = max(2, int(cfg.height * cfg.out_scale) // 2 * 2)

    # ---- lifecycle
    def start(self) -> None:
        self._t_start = time.time(); self._cpu0 = (time.process_time(), time.time()); self._cpu_pct = 0.0
        self._spawn(self.cfg.camera_mjpeg)
        self._threads = [threading.Thread(target=self._work, name="live-worker", daemon=True),
                         threading.Thread(target=self._tick, name="live-tick", daemon=True)]
        for t in self._threads:
            t.start()

    def _spawn(self, want_mjpeg: bool) -> None:
        cmd, is_jpeg = capture_command(self.cfg.device, self.cfg.width, self.cfg.height, self.cfg.fps, want_mjpeg, self.cfg.clip)
        self._is_jpeg = is_jpeg
        self.camera_desc = ("camera MJPEG" if is_jpeg else "camera raw frames") + f" {self.cfg.width}×{self.cfg.height}@{self.cfg.fps}"
        if self.cfg.device.split(":")[0] in ("test", "clip"):
            self.camera_desc = "simulated MJPEG camera " + f"{self.cfg.width}×{self.cfg.height}@{self.cfg.fps}"
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)   # buffered: read(n) returns n bytes
        rd = threading.Thread(target=self._read, args=(self._proc, is_jpeg), name="live-reader", daemon=True)
        rd.start(); self._threads.append(rd)

    def stop(self) -> RunSummary | None:
        summary = self.summary()
        self._stop.set()
        with self._lock:
            self._new.notify_all()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        for t in self._threads:
            if t is not threading.current_thread():
                t.join(timeout=3)
        self.status = "stopped"
        return summary

    # ---- reader: FFmpeg pipe → latest frame only (older ones are counted as drops)
    def _read(self, proc: subprocess.Popen, is_jpeg: bool) -> None:
        def put(item):
            with self._lock:
                if self._in is not None:
                    self._drops += 1
                self._in = (time.perf_counter(), item)
                self._captured += 1
                self._new.notify_all()
        try:
            if is_jpeg:
                read_multipart_jpegs(proc.stdout, put, self._stop)
            else:
                n = self.cfg.width * self.cfg.height * 3 // 2
                while not self._stop.is_set():
                    buf = proc.stdout.read(n)
                    if not buf or len(buf) < n:
                        break
                    put(np.frombuffer(buf, np.uint8).reshape(self.cfg.height * 3 // 2, self.cfg.width))
        finally:
            if not self._stop.is_set():
                err = (proc.stderr.read() or b"").decode(errors="ignore").strip().splitlines() if proc.poll() is not None else []
                if is_jpeg and self._captured == 0 and self.cfg.device.split(":")[0] in ("dshow", "v4l2"):
                    self.status = "camera has no MJPEG mode at this size: falling back to raw frames"
                    self.cfg.camera_mjpeg = False
                    self._spawn(False)          # same pipeline, raw input
                    return
                self.error = (err[-1] if err else "capture ended")[:200]
                self.status = "error"

    # ---- worker: everything that costs CPU, each stage timed
    def _work(self) -> None:
        if not HAVE_AV and self.cfg.needs_transcode():
            self.error, self.status = "PyAV is needed for anything but MJPEG passthrough (pip install av)", "error"
            return
        cfg = self.cfg
        spec = ENCODERS[cfg.encoder if cfg.encoder != PASSTHROUGH else "mjpeg"]
        jdec = enc = pilot = disp = None
        submit: dict[int, float] = {}
        n = 0
        self.status = "running"
        while not self._stop.is_set():
            with self._lock:
                while self._in is None and not self._stop.is_set():
                    self._new.wait(timeout=0.5)
                if self._stop.is_set():
                    return
                t_arr, item = self._in; self._in = None
            try:
                is_jpeg = isinstance(item, (bytes, bytearray))
                if is_jpeg and not cfg.needs_transcode():
                    self._publish(item, FrameStat(time.time(), len(item), len(item), True, 0, 0, 0.0, 0, 0))
                    continue
                # 1 · decode the camera's JPEG (the step a passthrough never pays)
                t0 = time.perf_counter()
                if is_jpeg:
                    if jdec is None:
                        jdec = av.CodecContext.create("mjpeg", "r")
                    frames = jdec.decode(av.Packet(item))
                    if not frames:
                        continue
                    frame = frames[0]
                else:
                    frame = av.VideoFrame.from_ndarray(item, format="yuv420p")
                t1 = time.perf_counter()
                # 2 · scale / convert to what the encoder wants
                frame = frame.reformat(width=self.out_w, height=self.out_h, format=spec.pix_fmt)
                t2 = time.perf_counter()
                # 3 · encode
                if enc is None:
                    enc = av.CodecContext.create(spec.key, "w")
                    enc.width, enc.height, enc.pix_fmt = self.out_w, self.out_h, spec.pix_fmt
                    enc.time_base = Fraction(1, cfg.fps); enc.framerate = Fraction(cfg.fps, 1)
                    enc.gop_size = max(1, int(round(cfg.gop_s * cfg.fps)))
                    enc.options = encoder_options(spec.key, preset_speed=cfg.preset_speed, zerolatency=cfg.zerolatency,
                                                  bitrate_kbps=cfg.bitrate_kbps, fps=cfg.fps, mjpeg_q=cfg.mjpeg_q)
                    enc.open()
                frame.pts = n; submit[n] = t2
                packets = enc.encode(frame)
                t3 = time.perf_counter()
                n += 1
                if not packets:   # held inside the encoder (lookahead / B-frames)
                    self._record(FrameStat(time.time(), len(item) if is_jpeg else item.nbytes, 0, False,
                                           (t1 - t0) * 1e3, (t2 - t1) * 1e3, None, 0, n - 1 - min(submit)))
                    continue
                for pkt in packets:
                    pts = int(pkt.pts) if pkt.pts is not None else n - 1
                    enc_ms = (t3 - submit.pop(pts, t2)) * 1e3
                    hold = (n - 1) - pts
                    for k in [k for k in submit if k < pts - 64]:
                        submit.pop(k, None)
                    # 4 · what the pilot's computer does: decode it again, then show it
                    if spec.key == "mjpeg":
                        out_jpeg, pilot_ms = bytes(pkt), 0.0   # the browser decodes JPEG itself
                    else:
                        if pilot is None:
                            name = DECODER_FOR[spec.codec]
                            pilot = av.CodecContext.create(name if name in av.codecs_available else "av1", "r")
                        t4 = time.perf_counter()
                        dec_frames = pilot.decode(pkt)
                        pilot_ms = (time.perf_counter() - t4) * 1e3
                        if not dec_frames:
                            continue
                        if disp is None:   # display-only JPEG: not part of the measured pipeline
                            disp = av.CodecContext.create("mjpeg", "w")
                            disp.width, disp.height, disp.pix_fmt = self.out_w, self.out_h, "yuvj420p"
                            disp.time_base = Fraction(1, cfg.fps); disp.options = {"qmin": "3", "qmax": "3"}
                            disp.open()
                        dp = disp.encode(dec_frames[0].reformat(format="yuvj420p"))
                        if not dp:
                            continue
                        out_jpeg = bytes(dp[0])
                    self._publish(out_jpeg, FrameStat(time.time(), len(item) if is_jpeg else item.nbytes, pkt.size, bool(pkt.is_keyframe),
                                                      (t1 - t0) * 1e3, (t2 - t1) * 1e3, enc_ms, pilot_ms, hold))
            except Exception as exc:  # shown in the HUD and the tab, never silently ignored
                self.error, self.status = f"{type(exc).__name__}: {str(exc)[:160]}", "error"
                return

    def _record(self, st: FrameStat) -> None:
        with self._lock:
            self._stats.append(st)
            self._processed += 1

    def _publish(self, jpeg: bytes, st: FrameStat) -> None:
        with self._lock:
            self._jpeg = jpeg; self._seq += 1
            self._stats.append(st)
            self._processed += 1
            self._new.notify_all()

    # ---- once a second: append to history (for the charts)
    def _tick(self) -> None:
        while not self._stop.wait(1.0):
            pt, wt = time.process_time(), time.time()     # whole lab process: capture parsing, codecs, HTTP
            self._cpu_pct = 100 * (pt - self._cpu0[0]) / max(wt - self._cpu0[1], 1e-6)
            self._cpu0 = (pt, wt)
            s = self.snapshot()
            if s["frames"]:
                self.history.append({"t": round(time.time() - self._t_start, 1), "mbps": s["mbps"], "encode_ms": s["encode_ms"],
                                     "encode_p95": s["encode_p95"], "fps": s["out_fps"], "cpu": s["cpu_pct"], "kb": s["kb_avg"]})

    # ---- read side (any thread)
    def latest_jpeg(self, after_seq: int, timeout: float = 1.0) -> tuple[int, bytes | None]:
        with self._lock:
            if self._seq <= after_seq:
                self._new.wait(timeout)
            return self._seq, self._jpeg

    def snapshot(self) -> dict:
        now = time.time()
        with self._lock:
            win = [s for s in self._stats if now - s.t <= self.WINDOW_S]
            drops, captured = self._drops, self._captured
        cpu = getattr(self, "_cpu_pct", 0.0)
        out = [s for s in win if s.out_bytes]
        enc = [s.encode_ms for s in win if s.encode_ms is not None]
        fps = len(out) / self.WINDOW_S
        bits = sum(s.out_bytes for s in out) * 8 / self.WINDOW_S
        cfg = self.cfg
        return {
            "status": self.status, "error": self.error, "pipeline": cfg.label(), "encoder": ENCODERS[cfg.encoder].label,
            "hardware": ENCODERS[cfg.encoder].hardware, "camera": self.camera_desc, "out_res": f"{self.out_w}×{self.out_h}",
            "transcode": cfg.needs_transcode(), "frames": len(win), "out_fps": round(fps, 1),
            "mbps": round(bits / 1e6, 3), "kb_avg": round(np.mean([s.out_bytes for s in out]) / 1e3, 1) if out else 0.0,
            "kb_last": round(out[-1].out_bytes / 1e3, 1) if out else 0.0, "key_recent": any(s.key and now - s.t < 0.35 for s in out),
            "bpp": round(bits / max(fps, 1e-6) / (self.out_w * self.out_h), 3) if fps else 0.0,
            "encode_ms": round(float(np.mean(enc)), 2) if enc else 0.0, "encode_p95": round(_pct(enc, 95), 2),
            "hold": max((s.hold for s in win), default=0),
            "decode_ms": round(float(np.mean([s.decode_ms for s in win])), 2) if win else 0.0,
            "scale_ms": round(float(np.mean([s.scale_ms for s in win])), 2) if win else 0.0,
            "pilot_ms": round(float(np.mean([s.pilot_ms for s in out])), 2) if out else 0.0,
            "cpu_pct": round(cpu, 0), "cores": os.cpu_count() or 1, "drops": drops, "captured": captured,
            "uptime": round(now - self._t_start, 1),
        }

    def summary(self) -> RunSummary | None:
        with self._lock:
            stats = list(self._stats)
        out = [s for s in stats if s.out_bytes]
        if len(out) < 5:
            return None
        span = max(out[-1].t - out[0].t, 1e-3)
        enc = [s.encode_ms for s in stats if s.encode_ms is not None]
        bits = sum(s.out_bytes for s in out) * 8 / span
        fps = (len(out) - 1) / span
        h = list(self.history)
        cfg = self.cfg
        pipe = "passthrough" if not cfg.needs_transcode() else ("decode → scale → encode" if cfg.out_scale != 1 else "decode → encode")
        return RunSummary(pipe, ENCODERS[cfg.encoder].label if cfg.encoder != PASSTHROUGH or not cfg.needs_transcode() else "MJPEG re-encode",
                          ENCODERS[cfg.encoder].hardware or "software", f"{self.out_w}×{self.out_h}", round(fps, 1), round(bits / 1e6, 2),
                          round(bits / max(fps, 1e-6) / (self.out_w * self.out_h), 3), round(float(np.mean(enc)), 2) if enc else 0.0,
                          round(_pct(enc, 95), 2), max((s.hold for s in stats), default=0),
                          round(float(np.mean([s.decode_ms + s.scale_ms for s in stats])), 2),
                          round(float(np.mean([x["cpu"] for x in h])) if h else 0.0, 0), self._drops, round(span, 1))


# ----------------------------------------------------------------------------- HTTP server + manager
class _Handler(BaseHTTPRequestHandler):
    manager: "LiveManager"

    def log_message(self, *a):  # keep the Streamlit console clean
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/stats"):
            body = json.dumps(self.manager.stats()).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self._cors()
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            return
        if self.path.startswith("/stream.mjpg"):
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame"); self.end_headers()
            seq = 0
            try:
                while not self.manager.closed:
                    pipe = self.manager.pipeline
                    if pipe is None:
                        time.sleep(0.2); continue
                    seq2, jpeg = pipe.latest_jpeg(seq)
                    if jpeg is None or seq2 == seq:
                        if pipe is not self.manager.pipeline:
                            seq = 0
                        continue
                    seq = seq2
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        self.send_response(404); self.end_headers()


class LiveManager:
    """Process-wide owner of the HTTP server and (at most) one running pipeline."""

    def __init__(self, host: str | None = None, port: int | None = None):
        self.host = host or os.environ.get("LAB_LIVE_HOST", "127.0.0.1")
        self.pipeline: LivePipeline | None = None
        self.runs: list[dict] = []
        self.closed = False
        handler = type("Handler", (_Handler,), {"manager": self})
        want = port or int(os.environ.get("LAB_LIVE_PORT", "8765"))
        last_err = None
        for p in range(want, want + 20):
            try:
                self.server = ThreadingHTTPServer((self.host, p), handler)
                break
            except OSError as exc:
                last_err = exc
        else:
            raise OSError(f"no free port from {want}: {last_err}")
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, name="live-http", daemon=True).start()

    def start(self, cfg: LiveConfig) -> None:
        self.stop()
        self.pipeline = LivePipeline(cfg)
        self.pipeline.start()

    def stop(self) -> None:
        if self.pipeline is not None:
            s = self.pipeline.stop()
            if s:
                self.runs.append(asdict(s))
            self.pipeline = None

    def stats(self) -> dict:
        p = self.pipeline
        return p.snapshot() if p else {"status": "idle"}

    def close(self) -> None:
        self.stop(); self.closed = True; self.server.shutdown()
