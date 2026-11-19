"""Collect measured values from the executed notebook (tables + cached files) into deck_data.json."""
import json, re, io, subprocess, html
from pathlib import Path
import numpy as np, pandas as pd, nbformat

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks" / "ROV_Video_Streaming_Workshop.ipynb"; WORK = ROOT / "notebooks" / "work"
nb = nbformat.read(NB, 4)
tables = []
for c in nb.cells:
    if c.cell_type != "code": continue
    for o in c.outputs:
        d = o.get("data", {})
        if "text/html" in d and "<table" in d["text/html"]:
            tables.append(pd.read_html(io.StringIO(d["text/html"]))[0])
def find(col):
    return next(t for t in tables if col in [str(x) for x in t.columns])
num = lambda v: float(re.sub(r"[^\d.\-]", "", str(v)))

e2 = find("compression_ratio"); e2i = e2.set_index("codec")
h264 = e2i.loc[[i for i in e2i.index if i.startswith("H.264")][0]]; mj = e2i.loc[[i for i in e2i.index if i.startswith("MJPEG")][0]]
eq = next(t for t in tables if any("bits_per_pixel" in str(c) for c in t.columns))
cols = [c for c in eq.columns if str(c).startswith("Mb/s @ SSIM")]
low_t, high_t = [str(c).split("SSIM ")[1] for c in cols]
eq_rows = [{"codec": r["codec"].split(" (")[0], "low": round(num(r[cols[0]]), 2), "high": round(num(r[cols[1]]), 2)} for _, r in eq.iterrows()]
mj_row = next(r for r in eq_rows if r["codec"] == "MJPEG"); h_row = next(r for r in eq_rows if r["codec"] == "H.264")
e4 = find("cpu_ms_per_frame")
e5 = find("worst_join_wait_s"); g30 = e5[e5.variant.str.startswith("GOP 30")].iloc[0]
e9 = find("frames held before first output"); e9 = e9.set_index(e9.columns[0])
e8 = find("SSIM (upscaled to 720p)"); e8 = e8.set_index(e8.columns[0])

lt = find("mean damaged (s)")
loss = [{"name": {0: "GOP 30 (I-frame every 1 s)", 1: "GOP 150 (I-frame every 5 s)", 2: "Intra refresh (30 frames)"}[i],
         "s": num(r["mean damaged (s)"]), "worst": num(r["worst (s)"])} for i, (_, r) in enumerate(lt.iterrows())]

def windowed_peak(path, win=0.2):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,size", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    pk = pd.DataFrame([l.split(",")[:2] for l in out.split() if l], columns=["pts", "size"]).astype(float)
    s = pk.groupby(np.floor(pk.pts / win))["size"].sum() * 8 / win / 1e6
    return float(s.max()), float(pk["size"].sum() * 8 / (pk.pts.max() - pk.pts.min() + 1 / 30) / 1e6)
peak, avg = windowed_peak(WORK / "e3_crf23.mp4"); vpeak, _ = windowed_peak(WORK / "e3_vbv_match.mp4")

# Jitter simulation — identical to notebook Experiment 9.2
rng = np.random.default_rng(1); n = 30 * 120
delay = 2.0 + rng.gamma(2.0, 1.5, n) + np.where(rng.random(n) < 0.02, rng.uniform(30, 80, n), 0)
buffers = list(range(0, 101, 5)); late = [round(float((delay > b).mean() * 100), 2) for b in buffers]

dflt = e9.loc["x264 medium (defaults)"]; zl = e9.loc["x264 veryfast + tune zerolatency"]
enc_default_ms = num(dflt["delay from buffering (ms)"]); enc_zl_ms = num(zl["mean time per encode() call (ms)"])
budgets = [{"name": "MJPEG · HTTP · browser", "vals": [33, 10, 3, 15, 5, 25]},
           {"name": "H.264 defaults · RTSP player", "vals": [33, round(enc_default_ms), 3, 1000, 8, 25]},
           {"name": "H.264 zerolatency · WebRTC", "vals": [33, round(enc_zl_ms), 3, 50, 8, 25]}]
for b in budgets: b["total"] = sum(b["vals"])
m, s_, t = [num(e8.iloc[i]["bitrate_Mb/s"]) for i in range(3)]
strat = [{"name": "8 × main", "mbps": 8 * m}, {"name": "2 main + 6 sub", "mbps": 2 * m + 6 * s_}, {"name": "1 main + 7 sub", "mbps": m + 7 * s_}, {"name": "1 main + 3 sub + 4 thumbs", "mbps": m + 3 * s_ + 4 * t}]
D = {
  "img": {"hero": str(WORK / "src_2.5.png"), "hero2": str(WORK / "src_5.0.png"), "frame": str(WORK / "src_0.5.png"),
          "section1": str(WORK / "src_0.5.png"), "section2": str(WORK / "src_5.0.png"), "section3": str(WORK / "src_2.5.png"),
          "loss": [str(p) for p in sorted(WORK.glob("e5_*_after.png"), key=lambda p: ("GOP_30" not in p.name, "GOP_150" not in p.name))]},
  "rawMbps": 332,
  "e2": {"h264": {"mbps": f"{num(h264['bitrate_Mb/s']):.1f}", "ratio": int(num(str(h264["compression_ratio"]).split(":")[0]))},
         "mjpeg": {"mbps": f"{num(mj['bitrate_Mb/s']):.1f}", "ratio": int(num(str(mj["compression_ratio"]).split(":")[0]))}},
  "eqq": {"rows": eq_rows, "low": low_t, "target": high_t, "mjpegVsH264": f"{mj_row['high'] / h_row['high']:.0f}"},
  "crf23": {"avg": f"{avg:.1f}", "peak": f"{peak:.1f}", "vbvPeak": f"{vpeak:.1f}"},
  "e4": [{"preset": r["preset"], "cpu": round(num(r["cpu_ms_per_frame"]), 1), "mbps": round(num(r["bitrate_Mb/s"]), 2)} for _, r in e4.iterrows()],
  "e5": {"iKB": f"{num(g30['avg_I_kB']):.0f}", "pKB": f"{num(g30['avg_P_kB']):.0f}", "ipRatio": f"{num(g30['avg_I_kB'])/num(g30['avg_P_kB']):.0f}", "dropKB": f"{42*188/1000:.0f}",
         "loss": [{"name": l["name"], "s": f"{l['s']:.1f}", "worst": f"{l['worst']:.1f}"} for l in loss]},
  "e9": {"defaultFrames": int(num(dflt["frames held before first output"])), "defaultMs": f"{enc_default_ms:,.0f}", "zlFrames": int(num(zl["frames held before first output"])), "budgets": budgets},
  "jitter": {"buffers": buffers, "late": late},
  "e8": {"main": f"{m:.1f}", "sub": f"{s_:.2f}", "thumb": f"{t:.2f}", "pct1": f"{(m + 7*s_)/(8*m):.0%}", "strategies": [{"name": x["name"], "mbps": round(x["mbps"], 1)} for x in strat]},
}
(Path(__file__).parent / "deck_data.json").write_text(json.dumps(D, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in D.items() if k != "jitter"}, indent=1, ensure_ascii=False)[:3000])
