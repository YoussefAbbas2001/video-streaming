"""FFmpeg-backed engine for the Encoding Lab: prepare a reference clip, encode with any settings,
measure size / speed / quality, extract frames, and simulate packet loss.

Everything is plain functions over files in a work directory, so the Streamlit UI stays thin and
every function can be tested without a browser.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------- binaries
FFMPEG = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = os.environ.get("FFPROBE_BIN") or shutil.which("ffprobe") or "ffprobe"


@dataclass
class RunInfo:
    wall_s: float
    cpu_s: float
    stderr: str
    returncode: int


def run(cmd: list[str], check: bool = True) -> RunInfo:
    """Run a command, measuring wall time and the child's CPU time (user + sys)."""
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    wall = time.perf_counter() - t0
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    if check and p.returncode != 0:
        raise RuntimeError(f"{Path(str(cmd[0])).name} failed: {p.stderr.strip()[-800:]}")
    return RunInfo(wall, cpu, p.stderr + p.stdout, p.returncode)


def ffmpeg_version() -> str:
    try:
        return run([FFMPEG, "-hide_banner", "-version"]).stderr.splitlines()[0]
    except Exception as exc:  # pragma: no cover - shown in the UI
        return f"FFmpeg not found ({exc})"


_CAPS: dict[str, bool] | None = None


def capabilities() -> dict[str, bool]:
    """Which encoders / filters this FFmpeg build has."""
    global _CAPS
    if _CAPS is None:
        enc = run([FFMPEG, "-hide_banner", "-encoders"], check=False).stderr
        flt = run([FFMPEG, "-hide_banner", "-filters"], check=False).stderr
        _CAPS = {n: f" {n} " in enc for n in ("libx264", "libx265", "libsvtav1", "mjpeg")}
        _CAPS["libvmaf"] = " libvmaf " in flt
    return _CAPS


# ----------------------------------------------------------------------------- codecs
@dataclass(frozen=True)
class CodecSpec:
    label: str
    encoder: str
    container: str
    q_name: str          # name of the quality knob
    q_range: tuple[int, int]
    q_default: int
    q_better: str        # "lower" or "higher" is better quality
    has_preset: bool
    has_gop: bool
    has_bitrate: bool
    blurb: str


CODECS: dict[str, CodecSpec] = {
    "H.264 (x264)": CodecSpec("H.264 (x264)", "libx264", "mp4", "CRF", (0, 51), 23, "lower", True, True, True,
                              "The universal codec: every browser and hardware decoder plays it. Jetson Nano encodes it in hardware."),
    "H.265 (x265)": CodecSpec("H.265 (x265)", "libx265", "mp4", "CRF", (0, 51), 28, "lower", True, True, True,
                              "Newer and usually more efficient, but much slower in software and not every browser decodes it."),
    "AV1 (SVT-AV1)": CodecSpec("AV1 (SVT-AV1)", "libsvtav1", "mkv", "CRF", (1, 63), 35, "lower", True, True, True,
                               "Royalty-free and very efficient, but expensive to encode. No hardware encoder on Jetson Nano or Pi 5."),
    "MJPEG": CodecSpec("MJPEG", "mjpeg", "mkv", "q:v", (2, 31), 5, "lower", False, False, False,
                       "Every frame is an independent JPEG: trivial to decode, no error propagation, but many more bits."),
}
PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
SVT_PRESET = {"ultrafast": 12, "superfast": 11, "veryfast": 10, "faster": 9, "fast": 8, "medium": 6, "slow": 5, "slower": 4, "veryslow": 3}


@dataclass
class EncodeSettings:
    codec: str = "H.264 (x264)"
    rate_mode: str = "crf"           # "crf" or "bitrate"
    quality: int = 23                # CRF or q:v
    bitrate_kbps: int = 2000
    buffer_s: float = 0.5            # VBV buffer, in seconds of bitrate
    preset: str = "medium"
    gop_s: float = 1.0               # keyframe interval in seconds
    bframes: int = 3
    zerolatency: bool = False
    scale: float = 1.0               # fraction of the reference resolution
    fps: int = 0                     # 0 = same as reference
    threads: int = 0                 # 0 = automatic

    def key(self) -> str:
        return hashlib.sha1(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]

    def short(self) -> str:
        spec = CODECS[self.codec]
        q = f"{spec.q_name} {self.quality}" if self.rate_mode == "crf" else f"{self.bitrate_kbps / 1000:g} Mb/s"
        bits = [self.codec.split(" ")[0], q]
        if spec.has_preset:
            bits.append(self.preset)
        if spec.has_gop:
            bits.append(f"GOP {self.gop_s:g}s")
        if self.zerolatency:
            bits.append("zerolatency")
        if self.scale != 1.0:
            bits.append(f"{int(self.scale * 100)}%")
        if self.fps:
            bits.append(f"{self.fps} fps")
        return " · ".join(bits)


# ----------------------------------------------------------------------------- reference clip
@dataclass
class Source:
    name: str
    mkv: Path
    yuv: Path
    width: int
    height: int
    fps: int
    frames: int
    workdir: Path
    sid: str = field(default="")

    @property
    def seconds(self) -> float:
        return self.frames / self.fps

    def raw_input(self) -> list[str]:
        return ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{self.width}x{self.height}", "-r", str(self.fps), "-i", str(self.yuv)]

    @property
    def raw_mbps(self) -> float:
        return self.width * self.height * 12 * self.fps / 1e6


def _probe(path: Path) -> dict:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True).stdout
    return json.loads(out or "{}")


def synth_underwater(path: Path, w: int, h: int, fps: int, n: int, seed: int = 7) -> None:
    """Generate a synthetic underwater inspection clip (colour cast, caustics, marine snow, noise, a camera cut)."""
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    pan = max(1, round(3 * w / 1280))
    tex_w = w + pan * n + w // 2
    lo = gaussian_filter(rng.standard_normal((h, tex_w)), 18 * h / 720); lo /= np.abs(lo).max()
    hi = gaussian_filter(rng.standard_normal((h, tex_w)), 1.5); hi /= np.abs(hi).max()
    tex = 0.55 + 0.25 * lo + 0.12 * hi
    yy = np.arange(h)[:, None]
    pipe = np.exp(-((yy - 0.58 * h) / (0.11 * h)) ** 2)
    seams = (np.sin(np.arange(tex_w) / (55.0 * w / 1280)) > 0.985).astype(float)
    tex = tex * (1 - 0.6 * pipe) + pipe * (0.75 + 0.15 * hi + 0.4 * seams[None, :])
    tex = np.clip(tex + gaussian_filter((rng.random((h, tex_w)) > 0.996).astype(float), 3) * 25 * pipe, 0, 1.4)
    depth = np.linspace(0, 1, h)[:, None]
    water = np.array([18, 92, 110]) / 255.0
    tint = np.array([0.35, 0.85, 0.95])
    xs = np.arange(w)[None, :]
    k = int(250 * w * h / (1280 * 720)) + 50
    px, py = rng.uniform(0, w, k), rng.uniform(0, h, k)
    vx, vy = rng.normal(0.4, 0.5, k), rng.normal(-0.6, 0.4, k)
    cut = int(0.66 * n)
    proc = subprocess.Popen([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                             "-r", str(fps), "-i", "-", "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        if i < cut:
            view, turb = tex[:, i * pan:i * pan + w], 0.35
        else:
            off = min(tex_w - w, w // 2 + (i - cut) * pan)
            view, turb = np.roll(tex[:, off:off + w], h // 4, axis=0) * 0.85, 0.5
        caustic = (np.sin(xs / (37.0 * w / 1280) + 2.1 * t) * np.sin(yy / (23.0 * h / 720) - 1.7 * t + xs / 90.0)) ** 2
        lum = view * (0.75 + 0.35 * caustic * np.exp(-3 * depth)) * (1.05 - 0.55 * depth)
        rgb = lum[..., None] * tint[None, None, :]
        haze = turb * (0.4 + 0.6 * depth)[..., None]
        rgb = rgb * (1 - haze) + water[None, None, :] * haze
        px += vx; py += vy; px %= w; py %= h
        np.add.at(rgb, (py.astype(int), px.astype(int)), 0.5)
        rgb += rng.normal(0, 0.004, rgb.shape)
        proc.stdin.write((np.clip(rgb, 0, 1) * 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()


def prepare_source(workdir: Path, upload: Path | None, seconds: float, height: int, fps: int = 30, start_s: float = 0.0) -> Source:
    """Create a lossless reference clip (FFV1 + raw YUV) from an uploaded file or the synthetic generator."""
    workdir.mkdir(parents=True, exist_ok=True)
    width = int(round(height * 16 / 9 / 2) * 2)
    tag = hashlib.sha1(f"{upload and upload.stat().st_size}-{upload}-{seconds}-{height}-{fps}-{start_s}".encode()).hexdigest()[:10]
    sdir = workdir / f"src_{tag}"; sdir.mkdir(exist_ok=True)
    mkv, yuv = sdir / "reference.mkv", sdir / "reference.yuv"
    frames = int(round(seconds * fps))
    if not mkv.exists():
        tmp = sdir / "tmp.mkv"
        if upload is None:
            synth_underwater(tmp, width, height, fps, frames)
        else:
            run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", str(start_s), "-i", str(upload), "-t", str(seconds), "-an",
                 "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p",
                 "-c:v", "ffv1", str(tmp)])
        tmp.rename(mkv)
    if not yuv.exists():
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(mkv), "-f", "rawvideo", "-pix_fmt", "yuv420p", str(yuv)])
    frames = yuv.stat().st_size // (width * height * 3 // 2)
    name = "Synthetic underwater clip" if upload is None else upload.name
    return Source(name, mkv, yuv, width, height, fps, int(frames), workdir, tag)


# ----------------------------------------------------------------------------- encoding
@dataclass
class EncodeResult:
    settings: dict
    path: str
    width: int
    height: int
    fps: int
    size_bytes: int
    bitrate_mbps: float
    encode_s: float
    cpu_s: float
    encode_fps: float
    cores: float
    psnr: float | None = None
    ssim: float | None = None
    vmaf: float | None = None
    psnr_frames: list[float] | None = None
    ssim_frames: list[float] | None = None
    compression_ratio: float = 0.0
    label: str = ""

    @property
    def bpp(self) -> float:
        return self.bitrate_mbps * 1e6 / (self.width * self.height * self.fps)


def ffmpeg_args(s: EncodeSettings, src: Source) -> tuple[list[str], str, int, int, int]:
    """Translate settings into FFmpeg output arguments. Returns (args, extension, width, height, fps)."""
    spec = CODECS[s.codec]
    w = int(round(src.width * s.scale / 2) * 2); h = int(round(src.height * s.scale / 2) * 2)
    fps = s.fps or src.fps
    vf = []
    if (w, h) != (src.width, src.height):
        vf.append(f"scale={w}:{h}:flags=area")
    if fps != src.fps:
        vf.append(f"fps={fps}")
    a: list[str] = ["-vf", ",".join(vf)] if vf else []
    gop = max(1, int(round(s.gop_s * fps)))
    kbps = int(s.bitrate_kbps); buf = max(1, int(kbps * s.buffer_s))
    if spec.encoder == "libx264":
        a += ["-c:v", "libx264", "-preset", s.preset, "-pix_fmt", "yuv420p", "-g", str(gop)]
        if s.zerolatency:
            a += ["-tune", "zerolatency"]
        else:
            a += ["-bf", str(s.bframes)]
        a += ["-crf", str(s.quality)] if s.rate_mode == "crf" else ["-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{buf}k"]
    elif spec.encoder == "libx265":
        params = [f"keyint={gop}", "log-level=error"] + ([] if s.zerolatency else [f"bframes={s.bframes}"])
        a += ["-c:v", "libx265", "-preset", s.preset, "-pix_fmt", "yuv420p", "-tag:v", "hvc1", "-x265-params", ":".join(params)]
        if s.zerolatency:
            a += ["-tune", "zerolatency"]
        a += ["-crf", str(s.quality)] if s.rate_mode == "crf" else ["-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{buf}k"]
    elif spec.encoder == "libsvtav1":
        a += ["-c:v", "libsvtav1", "-preset", str(SVT_PRESET[s.preset]), "-pix_fmt", "yuv420p", "-g", str(gop)]
        a += ["-crf", str(s.quality)] if s.rate_mode == "crf" else ["-b:v", f"{kbps}k"]
        if s.zerolatency:
            a += ["-svtav1-params", "pred-struct=1"]   # low-delay prediction structure
    else:  # MJPEG
        a += ["-c:v", "mjpeg", "-pix_fmt", "yuvj420p"]
        a += ["-q:v", str(s.quality)] if s.rate_mode == "crf" else ["-b:v", f"{kbps}k"]
    if s.threads:
        a += ["-threads", str(s.threads)]
    return a, spec.container, w, h, fps


def encode(src: Source, s: EncodeSettings, with_quality: bool = True, with_vmaf: bool = False) -> EncodeResult:
    """Encode the reference with `s` (cached by settings) and measure size, speed and quality."""
    args, ext, w, h, fps = ffmpeg_args(s, src)
    out = src.workdir / f"src_{src.sid}" / f"enc_{s.key()}.{ext}"
    meta = out.with_suffix(".json")
    if out.exists() and meta.exists():
        cached = json.loads(meta.read_text())
        if not with_vmaf or cached.get("vmaf") is not None:
            return EncodeResult(**cached)
    r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *src.raw_input(), *args, "-an", str(out)])
    size = out.stat().st_size
    duration = src.frames / src.fps
    frames_out = int(round(duration * fps))
    res = EncodeResult(settings=asdict(s), path=str(out), width=w, height=h, fps=fps, size_bytes=size,
                       bitrate_mbps=size * 8 / duration / 1e6, encode_s=r.wall_s, cpu_s=r.cpu_s,
                       encode_fps=frames_out / max(r.wall_s, 1e-6), cores=r.cpu_s / max(r.wall_s, 1e-6),
                       compression_ratio=(src.width * src.height * 12 * src.frames / 8) / size, label=s.short())
    if with_quality:
        q = quality(out, src, with_vmaf=with_vmaf)
        res.psnr, res.ssim, res.vmaf, res.psnr_frames, res.ssim_frames = q["psnr"], q["ssim"], q.get("vmaf"), q["psnr_frames"], q["ssim_frames"]
    meta.write_text(json.dumps(asdict(res)))
    return res


def quality(path: Path | str, src: Source, with_vmaf: bool = False) -> dict:
    """Full-reference PSNR/SSIM (and VMAF if requested and available), per frame and average.

    The encoded video is scaled back to the reference size and timestamps are snapped to the reference
    frame grid (settb), so lower-resolution, lower-fps and MKV (ms-timestamp) outputs compare correctly.
    """
    d = Path(path).parent
    plog, slog = d / "psnr.log", d / "ssim.log"
    sync = f"setpts=PTS-STARTPTS,settb=1/{src.fps}"
    graph = (f"[0:v]scale={src.width}:{src.height}:flags=bicubic,format=yuv420p,fps={src.fps},{sync},split=3[d1][d2][d3];"
             f"[1:v]format=yuv420p,{sync},split=3[r1][r2][r3];"
             f"[d1][r1]psnr=stats_file={plog}[o1];[d2][r2]ssim=stats_file={slog}[o2]")
    maps = ["-map", "[o1]", "-f", "null", "-", "-map", "[o2]", "-f", "null", "-"]
    vmaf_on = with_vmaf and capabilities().get("libvmaf")
    if vmaf_on:
        graph += ";[d3][r3]libvmaf[o3]"; maps += ["-map", "[o3]", "-f", "null", "-"]
    else:
        graph += ";[d3]nullsink;[r3]nullsink"
    r = run([FFMPEG, "-hide_banner", "-i", str(path), *src.raw_input(), "-lavfi", graph, *maps])
    psnr = float(re.search(r"PSNR .*average:([\d.]+|inf)", r.stderr).group(1).replace("inf", "99"))
    ssim = float(re.search(r"SSIM .*All:([\d.]+)", r.stderr).group(1))
    pf = [min(float(m.group(1).replace("inf", "99")), 99.0) for m in re.finditer(r"psnr_avg:([\d.]+|inf)", plog.read_text())]
    sf = [float(m.group(1)) for m in re.finditer(r"All:([\d.]+)", slog.read_text())]
    out = {"psnr": psnr, "ssim": ssim, "psnr_frames": pf, "ssim_frames": sf}
    if vmaf_on:
        m = re.search(r"VMAF score: ([\d.]+)", r.stderr)
        out["vmaf"] = float(m.group(1)) if m else None
    return out


# ----------------------------------------------------------------------------- inspection
def frame_table(path: Path | str):
    """Per-frame picture type and compressed size, in presentation order."""
    import pandas as pd
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pict_type,pkt_size,best_effort_timestamp_time",
                          "-of", "json", str(path)], capture_output=True, text=True).stdout
    rows = [(float(f.get("best_effort_timestamp_time", 0) or 0), f.get("pict_type", "?"), int(f.get("pkt_size", 0) or 0)) for f in json.loads(out).get("frames", [])]
    df = pd.DataFrame(rows, columns=["t", "type", "bytes"])
    df["t"] -= df["t"].min() if len(df) else 0
    return df.reset_index(names="frame")


def grab_frame(path: Path | str, index: int, src: Source) -> np.ndarray:
    """Decode one frame (by index, at the reference size) as an RGB array."""
    t = index / src.fps
    p = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.4f}", "-i", str(path), "-frames:v", "1",
                        "-vf", f"scale={src.width}:{src.height}:flags=bicubic", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    data = np.frombuffer(p.stdout, np.uint8)
    if data.size < src.width * src.height * 3:
        return np.zeros((src.height, src.width, 3), np.uint8)
    return data[: src.width * src.height * 3].reshape(src.height, src.width, 3)


def browser_preview(path: Path | str, src: Source, side_by_side: bool = False) -> Path:
    """A small H.264 MP4 any browser can play (optionally reference | encoded side by side)."""
    p = Path(path)
    out = p.with_name(p.stem + ("_sbs" if side_by_side else "_preview") + ".mp4")
    if out.exists():
        return out
    if side_by_side:
        graph = (f"[0:v]scale={src.width}:{src.height},setsar=1,fps={src.fps}[e];[1:v]setsar=1[r];"
                 f"[r][e]hstack=inputs=2,scale=-2:'min(540,ih)'[v]")
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(p), "-i", str(src.mkv), "-filter_complex", graph, "-map", "[v]"]
    else:
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(p), "-vf", f"scale={src.width}:{src.height},fps={src.fps}"]
    run(cmd + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)])
    return out


# ----------------------------------------------------------------------------- packet loss
def packet_loss_experiment(src: Source, variant: str, loss_kb: int, loss_at_s: float, bitrate_kbps: int = 2000) -> dict:
    """Encode an MPEG-TS live stream, delete `loss_kb` of packets at `loss_at_s`, decode, and score every frame."""
    gop = {"GOP 0.5 s": 0.5, "GOP 1 s": 1.0, "GOP 2 s": 2.0, "GOP 5 s": 5.0}
    sdir = src.workdir / f"src_{src.sid}"
    tag = re.sub(r"\W+", "_", f"{variant}_{bitrate_kbps}")
    ts = sdir / f"loss_{tag}.ts"
    extra = ["-g", str(src.fps), "-sc_threshold", "0", "-x264-params", "intra-refresh=1"] if variant == "Intra refresh (1 s)" \
        else ["-g", str(int(gop[variant] * src.fps)), "-keyint_min", str(int(gop[variant] * src.fps)), "-sc_threshold", "0"]
    if not ts.exists():
        run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *src.raw_input(), "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
             "-threads", "1", "-b:v", f"{bitrate_kbps}k", "-maxrate", f"{bitrate_kbps}k", "-bufsize", f"{bitrate_kbps // 3}k", *extra,
             "-pix_fmt", "yuv420p", "-an", "-f", "mpegts", str(ts)])
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,pos", "-of", "csv=p=0", str(ts)],
                         capture_output=True, text=True).stdout
    pk = [(float(a), int(b)) for a, b, *_ in (l.split(",") for l in out.split()) if a not in ("", "N/A") and b not in ("", "N/A")]
    t0 = min(p[0] for p in pk)
    pos = min(pk, key=lambda p: abs(p[0] - t0 - loss_at_s))[1]
    pos -= pos % 188
    n_ts = max(1, int(loss_kb * 1000 / 188))
    data = ts.read_bytes()
    dmg = sdir / f"loss_{tag}_{loss_kb}_{loss_at_s:.2f}.ts"
    dmg.write_bytes(data[:pos] + data[pos + 188 * n_ts:])
    dec = dmg.with_suffix(".mkv")
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(dmg), "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(dec)])
    clean, damaged = quality(ts, src), quality(dec, src)
    n = min(len(clean["psnr_frames"]), len(damaged["psnr_frames"]))
    c, d = np.array(clean["psnr_frames"][:n]), np.array(damaged["psnr_frames"][:n])
    bad = np.where(c - d > 3)[0]
    return {"clean": c.tolist(), "damaged": d.tolist(), "decoded": str(dec), "ts": str(ts),
            "damaged_s": float((bad.max() - bad.min() + 1) / src.fps) if len(bad) else 0.0,
            "first_bad": int(bad.min()) if len(bad) else None, "lost_bytes": n_ts * 188}


# ----------------------------------------------------------------------------- bandwidth model
DEFAULT_BPP = {"H.264": 0.045, "H.265": 0.058, "AV1": 0.074, "MJPEG": 0.34}   # workshop clip, SSIM ≈ 0.98
OVERHEAD = {"RTP/UDP": 0.053, "MPEG-TS/UDP": 0.073, "WebRTC": 0.07, "HTTP/TCP": 0.06}


def camera_mbps(bpp: float, w: int, h: int, fps: float, ref_pixels: int = 1280 * 720) -> float:
    """Rule-of-thumb bitrate: bpp × pixels × fps, with bits-per-pixel falling slowly as frames grow."""
    return bpp * w * h * fps * (ref_pixels / (w * h)) ** 0.25 / 1e6
