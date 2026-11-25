#!/usr/bin/env bash
# Tests for the parsers in rov_healthcheck.sh, using sample output in the formats of old and new usbutils
# (lsusb -t), Linux and macOS ping, and typical FFmpeg / GStreamer command lines.
#   bash docs/debug/test_healthcheck.sh
# shellcheck source=rov_healthcheck.sh
source "$(dirname "$0")/rov_healthcheck.sh"
fails=0
expect() {  # expect "name" "actual" "expected"
  if [[ $2 == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1"; echo "     got:      [$2]"; echo "     expected: [$3]"; fails=$((fails + 1)); fi
}

expect "throttled 0x0"      "$(decode_throttled 0x0)"     ""
expect "throttled 0x50005"  "$(decode_throttled 0x50005)" "under-voltage NOW,throttled NOW,under-voltage since boot,throttled since boot"
expect "throttled 0x80000"  "$(decode_throttled 0x80000)" "soft temperature limit since boot"

LSUSB_OLD='/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 5000M
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/1p, 480M
    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/4p, 480M
        |__ Port 1: Dev 3, If 0, Class=Video, Driver=uvcvideo, 480M
        |__ Port 1: Dev 3, If 1, Class=Video, Driver=uvcvideo, 480M
        |__ Port 2: Dev 4, If 0, Class=Video, Driver=uvcvideo, 480M
        |__ Port 2: Dev 4, If 1, Class=Video, Driver=uvcvideo, 480M
        |__ Port 3: Dev 5, If 0, Class=Video, Driver=uvcvideo, 480M
        |__ Port 3: Dev 5, If 1, Class=Video, Driver=uvcvideo, 480M
        |__ Port 4: Dev 6, If 0, Class=Human Interface Device, Driver=usbhid, 12M'
expect "lsusb -t (old format): 3 cameras on bus 1" "$(usb_cameras <<<"$LSUSB_OLD")" $'1 480M\n1 480M\n1 480M'

LSUSB_NEW='/:  Bus 003.Port 001: Dev 001, Class=root_hub, Driver=xhci-hcd/2p, 480M
    |__ Port 001: Dev 002, If 0, Class=Video, Driver=uvcvideo, 480M
    |__ Port 001: Dev 002, If 1, Class=Video, Driver=uvcvideo, 480M
/:  Bus 001.Port 001: Dev 001, Class=root_hub, Driver=xhci-hcd/2p, 480M
    |__ Port 002: Dev 003, If 0, Class=Hub, Driver=hub/4p, 12M
        |__ Port 001: Dev 004, If 0, Class=Video, Driver=uvcvideo, 12M
        |__ Port 001: Dev 004, If 1, Class=Video, Driver=uvcvideo, 12M'
expect "lsusb -t (new format): one at 480M, one at 12M" "$(usb_cameras <<<"$LSUSB_NEW")" $'3 480M\n1 12M'

PING_OK='PING 192.168.2.1 (192.168.2.1) 56(84) bytes of data.
--- 192.168.2.1 ping statistics ---
20 packets transmitted, 20 received, 0% packet loss, time 3805ms
rtt min/avg/max/mdev = 0.312/0.455/1.020/0.140 ms'
expect "ping, healthy"  "$(parse_ping <<<"$PING_OK")" "0 0.312 0.455 1.020"
PING_LOSS='20 packets transmitted, 17 received, 15% packet loss, time 3810ms
rtt min/avg/max/mdev = 0.401/12.522/48.003/14.980 ms'
expect "ping, lossy"    "$(parse_ping <<<"$PING_LOSS")" "15 0.401 12.522 48.003"
PING_DEAD='20 packets transmitted, 0 received, +20 errors, 100% packet loss, time 3999ms'
expect "ping, no reply" "$(parse_ping <<<"$PING_DEAD")" "100 - - -"
PING_MAC='--- 192.168.2.1 ping statistics ---
20 packets transmitted, 20 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 0.302/0.410/0.800/0.100 ms'
expect "ping, BSD/macOS format" "$(parse_ping <<<"$PING_MAC")" "0.0 0.302 0.410 0.800"

GOOD='ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -i /dev/video0 -c:v libx264 -preset ultrafast -tune zerolatency -bf 0 -g 30 -f rtp rtp://192.168.2.1:5600'
expect "pipeline: low-latency x264 is fine" "$(pipeline_findings <<<"$GOOD")" ""
BAD='ffmpeg -rtsp_transport tcp -i rtsp://cam/stream -c:v libx264 -g 250 -f rtp rtp://192.168.2.1:5602
ffmpeg -f v4l2 -input_format mjpeg -video_size 1920x1080 -i /dev/video2 -vf scale=640:360 -c:v mjpeg -f mjpeg udp://192.168.2.1:5604'
expect "pipeline: x264 defaults, TCP, long GOP, resolution trap" "$(pipeline_findings <<<"$BAD" | cut -d'|' -f1 | tr '\n' ' ')" "D4 D6 D3 C5 "
GST='gst-launch-1.0 v4l2src ! nvv4l2h264enc iframeinterval=300 ! rtph264pay ! udpsink host=192.168.2.1 port=5600
gst-launch-1.0 udpsrc port=5600 ! rtpjitterbuffer latency=500 ! rtph264depay ! avdec_h264 ! autovideosink'
expect "pipeline: Jetson GOP, no SPS/PPS, big jitter buffer" "$(pipeline_findings <<<"$GST" | cut -d'|' -f1 | tr '\n' ' ')" "D3 D5 F3 "

echo; (( fails )) && { echo "$fails test(s) failed"; exit 1; }; echo "all tests passed"
