# Streaming video into GUERILLA_MASK

GUERILLA_MASK plays streams, it does not make them. Anyone on the hotspot who can put an MJPEG stream on the network can have it on the wall: phone camera, laptop webcam, video file, screen, Pi.

MJPEG over HTTP is one GET that never ends, JPEG after JPEG. Browsers play it in an `<img>` with no plugin. RTSP, AVI, and HLS do not play in a browser.

## On the projection laptop

1. Open `index.html` from disk, or run `./serve.sh`. Not the https Pages URL: https pages cannot load `http://` streams.
2. Library, `+ URL`, paste the stream URL. Example `http://192.168.43.12:8080/video`.
3. Use it like any media: on a quad, in a physics arena, as an effect source.

Stream status shows in the inspector. It reconnects by itself if the sender drops; `↻ Reconnect` forces it. Add `#mjpeg` to the URL if the app tries to play it as a video file.

Effects (feedback, reaction-diffusion, motion cut, filter) read pixels, and the browser only allows that when the sender sends a CORS header. ustreamer and ffmpeg do. VLC, mjpg-streamer, and most phone apps do not: those still project, no effects. The inspector says which case you are in.

## Senders

Same Wi-Fi or hotspot. Sender needs its own IP (`ip a`, `ipconfig`, or the phone app shows it). Firewall must allow the port.

### Phone

Android: IP Webcam (free, Play Store). Start server. URL is `http://<phone-ip>:8080/video`. Set 640x480 or 1280x720, quality 50. Lower if the hotspot chokes.

iPhone: no clean free option. Use a laptop with VLC and the phone as a webcam via Continuity Camera, or AirDrop the clip to a laptop.

### Laptop with VLC (file, webcam, or screen)

`stream/send-vlc.sh` (Linux, macOS) or `stream/send-vlc.cmd` (Windows).

```
stream/send-vlc.sh clip.mp4             # loops a file
stream/send-vlc.sh /dev/video0          # Linux webcam
stream/send-vlc.sh screen://            # share the screen
stream/send-vlc.sh clip.mp4 8090 1280   # port and width
```

URL: `http://<laptop-ip>:8080/stream.mjpg`. Windows: `send-vlc.cmd clip.mp4`, webcam is `dshow://`. macOS webcam is `avcapture://`.

### Raspberry Pi or Linux box with a USB/Pi camera

`stream/send-pi.sh`. Prefers ustreamer (hardware JPEG on a Pi, multi-client, CORS flag), falls back to mjpg-streamer.

```
sudo apt install ustreamer      # or: sudo apt install mjpg-streamer
stream/send-pi.sh               # /dev/video0, 1280x720, port 8080
stream/send-pi.sh /dev/video2 8081 640x480
```

URL: ustreamer `http://<pi-ip>:8080/stream`, mjpg-streamer `http://<pi-ip>:8080/?action=stream`.

### Anything else: ffmpeg

`stream/send-ffmpeg.sh`. Takes whatever ffmpeg can open, including RTSP cameras, and re-serves it as MJPEG with the CORS header. One client at a time.

```
stream/send-ffmpeg.sh rtsp://admin:pw@10.0.0.5/stream1
stream/send-ffmpeg.sh clip.mp4 8090
```

URL: `http://<ip>:8080/stream.mjpg`.

### IP cameras

Most have an MJPEG URL already:

- Axis `/mjpg/video.mjpg`
- Hikvision `/ISAPI/Streaming/channels/102/httpPreview`
- Dahua, Amcrest `/cgi-bin/mjpg/video.cgi?channel=1&subtype=1`
- Foscam, cheap clones `/videostream.cgi?user=admin&pwd=`
- ESP32-CAM `http://<ip>:81/stream`

## Bandwidth

A hotspot carries maybe 20 Mbit/s shared. 640x480 at 15 fps, quality 50, is about 2 Mbit/s per stream. Each stream holds one TCP connection per viewer; Chrome allows six per host.

## Troubleshooting

- Black thumbnail, "connecting…": wrong IP or port, firewall, or sender not started. Open the URL in a browser tab on the projection laptop. If a tab shows it, the app will.
- Plays in a tab, not in the app: page is https. Use `file://` or `./serve.sh`.
- Freezes, then comes back: normal. Watchdog reconnects after 8 s of no change.
- Effect on it is black: no CORS header from the sender. Use ustreamer or ffmpeg, or put the stream on a quad without effects.
- VLC "no suitable encoder": add `venc=ffmpeg{strict=1}` (the script does).
