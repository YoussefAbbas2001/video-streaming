#!/usr/bin/env bash
# What cameras do we have, which bus are they on, and which ones can encode H.264 themselves?
#   ./camera_inventory.sh                        # USB cameras
#   ./camera_inventory.sh rtsp://192.168.2.10/0  # also probe IP cameras (any number of URLs)
set -uo pipefail
echo "== USB topology (cameras sharing a 480M bus share 480 Mb/s) =="
if command -v lsusb >/dev/null; then lsusb -t; else echo "lsusb not installed (apt install usbutils)"; fi
echo
echo "== V4L2 video devices =="
if command -v v4l2-ctl >/dev/null; then
  shopt -s nullglob; devs=(/dev/video*)
  [[ ${#devs[@]} -eq 0 ]] && echo "no /dev/video* devices found"
  for d in "${devs[@]}"; do
    fmts=$(v4l2-ctl -d "$d" --list-formats 2>/dev/null | grep -o "'[A-Z0-9]*'" | tr -d "'" | sort -u | tr '\n' ' ')
    [[ -z "$fmts" ]] && continue   # metadata nodes have no capture formats
    name=$(v4l2-ctl -d "$d" --info 2>/dev/null | awk -F': ' '/Card type/ {print $2}')
    enc="no  → the SBC must encode"
    [[ "$fmts" == *H264* ]] && enc="YES → camera encodes H.264, the SBC can just forward it"
    printf "%-12s %-32s formats: %-22s onboard H.264: %s\n" "$d" "${name:0:32}" "$fmts" "$enc"
  done
  echo "(details: v4l2-ctl -d /dev/videoN --list-formats-ext)"
else
  echo "v4l2-ctl not installed (apt install v4l-utils)"
fi
for url in "$@"; do
  echo; echo "== $url =="
  ffprobe -hide_banner -v error -rtsp_transport tcp -show_entries stream=codec_name,width,height,avg_frame_rate,bit_rate -of default=nw=1 "$url" \
    || echo "could not open $url"
done
