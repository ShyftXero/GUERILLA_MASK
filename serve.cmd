@echo off
rem Serve GUERILLA_MASK over http://localhost:8000/ (needed for YouTube embeds).
cd /d "%~dp0"
echo GUERILLA_MASK -^> http://localhost:8000/   (Ctrl+C to stop)
python -m http.server 8000 --bind 127.0.0.1
