# Two numbers every pilot GUI should show: throughput and loss

*M.I.A Robotics · streaming docs · 21 Nov 2026*

**Recommendation.** Give every camera tile in the pilot GUI two live numbers:

- **Throughput:** the Mb/s this stream is using right now.
- **Loss:** the % of its packets that never arrived.

Add one total for the whole tether. Most "the video is bad" reports from the pool are one of these two numbers going wrong. Without them the team argues; with them it knows within a second whether the problem is bandwidth, loss or something else, such as the encoder or the camera.

## What to show

| Where | Metric | How it is computed | Green | Amber | Red |
|---|---|---|---|---|---|
| Each camera tile | **↓ Mb/s** | bytes received in the last 1 s × 8 | ≤ this camera's budget | ≤ 1.3 × budget | > 1.3 × budget |
| Each camera tile | **Loss %** | RTP packets missing from the sequence numbers, last 1 s (and last 60 s in the tooltip) | < 0.1 % | 0.1–1 % | > 1 % |
| Each camera tile | **STALE** badge | no packet for 500 ms | — | — | shown |
| Status bar | **Tether** | sum of all streams ÷ the tether throughput you measured with iperf3 | < 70 % | 70–90 % | > 90 % |
| Tooltip | Jitter | RFC 3550 interarrival jitter, ms | < 10 ms | 10–30 ms | > 30 ms |

**Why the loss thresholds are this low.** With a 1 s GOP, one lost packet corrupts the picture until the next keyframe, up to a second later (Encoding Lab → Packet loss tab). Half a percent of loss is very visible.

**Why STALE matters.** It is the "never show success the system hasn't confirmed" rule from the UX slides. A frozen last frame looks exactly like a still scene, so the pilot must be told.

## "Bit loss" is packet loss

On Ethernet a corrupted frame fails its CRC and is **dropped whole**, so the receiver never sees wrong bits, only missing packets. The application-level measure of "bit loss" is therefore **packet loss**, and RTP makes it easy:

- every packet carries a 16-bit **sequence number** that goes up by one;
- a gap means lost packets;
- a packet that arrives after a later one is late (reordered), not lost.

Lost bits ≈ lost packets × average packet size, if you want a bit count.

## How to get the numbers

### A. Any player (ffplay, VLC, OpenCV, browser): put the probe in front

`encoding_lab/tools/rtp_probe.py` listens on the camera's port, measures every packet, and forwards it unchanged to the player:

```bash
# the ROV sends camera 1 to the GUI computer on port 5600
python3 encoding_lab/tools/rtp_probe.py --port 5600 --forward 5700 --json   # one JSON line per second
ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -flags low_delay cam1_5700.sdp   # the sender's .sdp with "m=video 5600" changed to 5700
```

The JSON looks like this; the GUI reads one line per second per camera:

```json
{"throughput_mbps": 2.96, "loss_pct_window": 1.40, "loss_pct_total": 1.83, "lost_packets": 28, "received_packets": 1501, "jitter_ms": 0.3, "reordered": 0}
```

**Tested:** an FFmpeg 3 Mb/s H.264 RTP stream went through a relay that dropped 2.22 % of packets at random. The probe reported 2.23 % total loss and 2.8–3.0 Mb/s (unit tests: `encoding_lab/tests/test_rtp_probe.py`).

### B. Inside a Python GUI: import it

```python
from rtp_probe import RtpStats          # encoding_lab/tools/rtp_probe.py, standard library only
stats = {cam: RtpStats() for cam in cameras}
# in the thread that receives each camera's UDP datagrams:
stats[cam].feed(datagram)
# once a second, on the GUI thread (Qt: a QTimer; never touch widgets from the receive thread):
s = stats[cam].snapshot()
tile.set_throughput(s["throughput_mbps"]); tile.set_loss(s["loss_pct_window"])
```

### C. A GStreamer receiver: read the jitter buffer's own counters

If the GUI already receives through GStreamer, `rtpjitterbuffer` counts lost packets itself. Name it and read its `stats` once a second, and count bytes with a pad probe on `udpsrc`:

```python
pipeline = Gst.parse_launch(
    'udpsrc name=src port=5600 caps="application/x-rtp,media=video,encoding-name=H264,payload=96" ! '
    'rtpjitterbuffer name=jb latency=50 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink name=sink')
nbytes = 0
def count(pad, info):
    global nbytes
    nbytes += info.get_buffer().get_size(); return Gst.PadProbeReturn.OK
pipeline.get_by_name("src").get_static_pad("src").add_probe(Gst.PadProbeType.BUFFER, count)

def every_second():                      # e.g. GLib.timeout_add_seconds(1, every_second)
    global nbytes
    st = pipeline.get_by_name("jb").get_property("stats")
    lost, pushed = st.get_value("num-lost"), st.get_value("num-pushed")
    mbps, nbytes = nbytes * 8 / 1e6, 0
    ...                                  # loss % = Δlost / (Δlost + Δpushed) since the last call
    return True
```

(Option C is a reference pattern and was not run here. Options A and B were tested.)

### D. Total tether use without touching the streams

The operating system already counts every byte per network interface. This gives the status-bar total, including control traffic:

```python
import psutil, time                       # pip install psutil
a = psutil.net_io_counters(pernic=True)["eth0"].bytes_recv; time.sleep(1)
b = psutil.net_io_counters(pernic=True)["eth0"].bytes_recv
print((b - a) * 8 / 1e6, "Mb/s on the tether")
```

## Check that the metrics tell the truth

Before trusting the GUI, break the link on purpose and see whether the numbers react:

```bash
sudo tc qdisc add dev eth0 root netem loss 1%            # 1 % random loss on the GUI computer's interface
sudo tc qdisc change dev eth0 root netem rate 5mbit      # squeeze the bandwidth
sudo tc qdisc del dev eth0 root                          # back to normal
```

The loss widget should read about 1 % and turn amber. Under the rate limit, throughput should flatten at about 5 Mb/s while the picture degrades. File the result as a test case in the Bug Hunt League.
