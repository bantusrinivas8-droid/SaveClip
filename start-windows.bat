@echo off
cd /d "%~dp0"
if not exist .venv (
  echo First time setup, please wait...
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -q -U -r requirements.txt
echo.
echo SaveClip is running. Open http://127.0.0.1:8000 in your browser.
echo Press Ctrl+C to stop.
start "" http://127.0.0.1:8000
python app.py
pause
