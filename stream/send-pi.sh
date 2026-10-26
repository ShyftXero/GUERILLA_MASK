#!/usr/bin/env bash
# Stream a USB or Pi camera as MJPEG with ustreamer (preferred) or mjpg-streamer.
#   stream/send-pi.sh                        /dev/video0, 1280x720, port 8080
#   stream/send-pi.sh /dev/video2 8081 640x480
# Install: sudo apt install ustreamer     (or: sudo apt install mjpg-streamer)
# Viewer URL: ustreamer      http://<pi-ip>:8080/stream
#             mjpg-streamer  http://<pi-ip>:8080/?action=stream
# ustreamer sends the CORS header, so effects in GUERILLA_MASK can read it.
set -euo pipefail
DEV="${1:-/dev/video0}"; PORT="${2:-8080}"; RES="${3:-1280x720}"; FPS="${FPS:-15}"; QUALITY="${QUALITY:-60}"
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<pi-ip>")
if command -v ustreamer >/dev/null; then
  echo "ustreamer $DEV $RES  ->  http://$IP:$PORT/stream"
  exec ustreamer --device="$DEV" --resolution="$RES" --desired-fps="$FPS" --quality="$QUALITY" \
    --host=0.0.0.0 --port="$PORT" --allow-origin='*' --format=MJPEG --encoder=HW 2>/dev/null \
    || exec ustreamer --device="$DEV" --resolution="$RES" --desired-fps="$FPS" --quality="$QUALITY" --host=0.0.0.0 --port="$PORT" --allow-origin='*'
elif command -v mjpg_streamer >/dev/null; then
  echo "mjpg-streamer $DEV $RES  ->  http://$IP:$PORT/?action=stream"
  exec mjpg_streamer -i "input_uvc.so -d $DEV -r $RES -f $FPS -q $QUALITY" -o "output_http.so -p $PORT"
else
  echo "Neither ustreamer nor mjpg_streamer installed. sudo apt install ustreamer"; exit 1
fi
