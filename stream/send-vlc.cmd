@echo off
rem Stream a file, webcam, or screen as MJPEG over HTTP with VLC, for GUERILLA_MASK on the same hotspot.
rem   stream\send-vlc.cmd clip.mp4           loops a file on port 8080
rem   stream\send-vlc.cmd dshow://           webcam
rem   stream\send-vlc.cmd screen://          share this screen
rem   stream\send-vlc.cmd clip.mp4 8090 1280 port, width
rem Viewer URL: http://<this-ip>:PORT/stream.mjpg   (ipconfig shows the IP). Allow vlc.exe through the firewall when asked.
rem VLC adds no CORS header: projects fine, effects cannot read it.
setlocal
set SRC=%~1
set PORT=%~2
set WIDTH=%~3
if "%SRC%"=="" ( findstr /b "rem " "%~f0" & exit /b 1 )
if "%PORT%"=="" set PORT=8080
if "%WIDTH%"=="" set WIDTH=960
set VLC=%ProgramFiles%\VideoLAN\VLC\vlc.exe
if not exist "%VLC%" set VLC=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe
if not exist "%VLC%" ( echo VLC not found. Install from videolan.org & exit /b 1 )
set LOOP=--loop
echo %SRC% | findstr /c:"://" >nul && set LOOP=
echo Streaming %SRC%  -^>  http://^<this-ip^>:%PORT%/stream.mjpg   (close window to stop)
"%VLC%" -I dummy "%SRC%" %LOOP% --no-audio --screen-fps=15 --sout "#transcode{vcodec=MJPG,venc=ffmpeg{strict=1},fps=15,width=%WIDTH%}:standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:%PORT%/stream.mjpg}"
