#!/usr/bin/env python3
"""Live streaming-health monitor for the ROV computer (Raspberry Pi, Jetson or any Linux PC).

Shows, once per second: CPU per core, CPU used by video processes (ffmpeg, gst-launch, …), clock speed,
temperature, Raspberry Pi throttling flags, and tether bandwidth per network interface against your budget.
Optionally writes every sample to CSV, which is what you want for a 30-minute soak test.

No dependencies: it only reads /proc and /sys (and calls `vcgencmd` if it exists).

    python3 monitor.py                              # live view
    python3 monitor.py --iface eth0 --link-mbps 100 # utilisation of a 100 Mb/s tether (70 % = budget line)
    python3 monitor.py --csv soak.csv --duration 1800 --plain
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

VIDEO_PROCESSES = ("ffmpeg", "gst-launch-1.0", "gst-launch", "mediamtx", "python3", "rpicam-vid", "ffplay")
TEMP_WARN_C = 75.0      # warn before the 80 °C Raspberry Pi soft-throttle point
TEMP_THROTTLE_C = 80.0
HEADROOM = 0.70         # plan to use at most 70 % of measured tether throughput
CLK_TCK = os.sysconf("SC_CLK_TCK")
# vcgencmd get_throttled bits (Raspberry Pi documentation)
THROTTLE_BITS = {0: "under-voltage NOW", 1: "freq capped NOW", 2: "throttled NOW", 3: "soft temp limit NOW",
                 16: "under-voltage occurred", 17: "freq cap occurred", 18: "throttling occurred", 19: "soft temp limit occurred"}


def read_cpu_times() -> dict[str, tuple[int, int]]:
    out = {}
    for line in Path("/proc/stat").read_text().splitlines():
        if line.startswith("cpu"):
            name, *vals = line.split()
            vals = list(map(int, vals))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            out[name] = (sum(vals), idle)
    return out


def read_net() -> dict[str, tuple[int, int]]:
    out = {}
    for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
        name, data = line.split(":", 1)
        f = data.split()
        out[name.strip()] = (int(f[0]), int(f[8]))   # rx bytes, tx bytes
    return out


def read_proc_cpu() -> dict[int, tuple[str, int]]:
    """CPU ticks (user+system) of processes whose name looks like part of the video pipeline."""
    out = {}
    for stat in glob.glob("/proc/[0-9]*/stat"):
        try:
            raw = Path(stat).read_text()
            name = raw[raw.index("(") + 1: raw.rindex(")")]
            if not any(name.startswith(p[:15]) for p in VIDEO_PROCESSES):
                continue
            fields = raw[raw.rindex(")") + 2:].split()
            out[int(stat.split("/")[2])] = (name, int(fields[11]) + int(fields[12]))
        except (OSError, ValueError, IndexError):
            continue   # the process ended while we were reading it
    return out


def read_temps() -> dict[str, float]:
    temps = {}
    for zone in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        try:
            kind = Path(zone, "type").read_text().strip()
            temps[kind] = int(Path(zone, "temp").read_text()) / 1000.0
        except (OSError, ValueError):
            continue
    return temps


def read_freq_mhz() -> float | None:
    vals = []
    for f in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"):
        try:
            vals.append(int(Path(f).read_text()) / 1000.0)
        except (OSError, ValueError):
            pass
    return sum(vals) / len(vals) if vals else None


def read_throttled() -> tuple[str, list[str]] | None:
    if not shutil.which("vcgencmd"):
        return None
    try:
        raw = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2).stdout.strip()
        value = int(raw.split("=")[1], 16)
    except (subprocess.SubprocessError, IndexError, ValueError):
        return None
    return hex(value), [msg for bit, msg in THROTTLE_BITS.items() if value & (1 << bit)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iface", action="append", help="interface(s) to show (default: all except lo)")
    ap.add_argument("--link-mbps", type=float, default=100.0, help="measured tether throughput in Mb/s (iperf3)")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--duration", type=float, default=0, help="stop after N seconds (0 = until Ctrl+C)")
    ap.add_argument("--csv", help="append one row per sample to this CSV file")
    ap.add_argument("--plain", action="store_true", help="print one line per sample instead of a refreshing screen")
    a = ap.parse_args()

    cpu0, net0, proc0 = read_cpu_times(), read_net(), read_proc_cpu()
    ifaces = a.iface or [i for i in net0 if i != "lo"]
    writer, fh = None, None
    if a.csv:
        new = not Path(a.csv).exists()
        fh = open(a.csv, "a", newline="")
        writer = csv.writer(fh)
        if new:
            writer.writerow(["time", "cpu_total_pct", "cpu_max_core_pct", "video_proc_cores", "freq_mhz", "temp_max_c",
                             "throttled_hex", *[f"{i}_rx_mbps" for i in ifaces], *[f"{i}_tx_mbps" for i in ifaces]])
    t_start = time.time()
    try:
        while True:
            time.sleep(a.interval)
            cpu1, net1, proc1 = read_cpu_times(), read_net(), read_proc_cpu()
            usage = {}
            for k, (tot, idle) in cpu1.items():
                t0, i0 = cpu0.get(k, (tot, idle))
                usage[k] = 100.0 * (1 - (idle - i0) / (tot - t0)) if tot > t0 else 0.0
            cores = {k: v for k, v in usage.items() if k != "cpu"}
            rates = {}
            for i in ifaces:
                if i in net1 and i in net0:
                    rates[i] = tuple((net1[i][j] - net0[i][j]) * 8 / a.interval / 1e6 for j in (0, 1))
            procs = []
            for pid, (name, ticks) in proc1.items():
                if pid in proc0:
                    procs.append((name, pid, (ticks - proc0[pid][1]) / CLK_TCK / a.interval))
            procs.sort(key=lambda p: -p[2])
            video_cores = sum(p[2] for p in procs)
            temps = read_temps(); tmax = max(temps.values()) if temps else None
            freq = read_freq_mhz(); thr = read_throttled()

            lines = [f"ROV streaming monitor · {time.strftime('%H:%M:%S')} · {len(cores)} cores · Ctrl+C to stop", ""]
            lines.append("CPU   " + "  ".join(f"{k[3:]}:{v:5.1f}%" for k, v in sorted(cores.items(), key=lambda kv: int(kv[0][3:]))) +
                         f"   total {usage.get('cpu', 0):5.1f}%" + (f"   clock {freq:,.0f} MHz" if freq else ""))
            if procs:
                lines.append("VIDEO " + "  ".join(f"{n}[{pid}] {c:.2f} cores" for n, pid, c in procs[:4]))
            if tmax is not None:
                state = "THROTTLING RANGE" if tmax >= TEMP_THROTTLE_C else ("WARNING" if tmax >= TEMP_WARN_C else "ok")
                lines.append(f"TEMP  {tmax:5.1f} °C ({state})   " + "  ".join(f"{k}:{v:.0f}" for k, v in list(temps.items())[:4]))
            if thr:
                lines.append(f"PI    get_throttled={thr[0]}  " + (", ".join(thr[1]) if thr[1] else "never throttled since boot"))
            total_mbps = 0.0
            for i, (rx, tx) in rates.items():
                total_mbps += max(rx, tx)
                lines.append(f"NET   {i:10} rx {rx:7.2f} Mb/s   tx {tx:7.2f} Mb/s")
            if rates:
                util = total_mbps / a.link_mbps
                flag = "OVER BUDGET" if util > HEADROOM else "ok"
                lines.append(f"      busiest direction ≈ {total_mbps:.2f} Mb/s = {util:.0%} of {a.link_mbps:g} Mb/s "
                             f"(budget {HEADROOM:.0%}) → {flag}")
            if a.plain:
                print(" | ".join(l for l in lines[2:]), flush=True)
            else:
                sys.stdout.write("\033[2J\033[H" + "\n".join(lines) + "\n"); sys.stdout.flush()
            if writer:
                writer.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), f"{usage.get('cpu', 0):.1f}", f"{max(cores.values(), default=0):.1f}",
                                 f"{video_cores:.2f}", f"{freq:.0f}" if freq else "", f"{tmax if tmax is not None else ''}", thr[0] if thr else "",
                                 *[f"{rates.get(i, (0, 0))[0]:.3f}" for i in ifaces], *[f"{rates.get(i, (0, 0))[1]:.3f}" for i in ifaces]])
                fh.flush()
            cpu0, net0, proc0 = cpu1, net1, proc1
            if a.duration and time.time() - t_start >= a.duration:
                break
    except KeyboardInterrupt:
        pass
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    main()
