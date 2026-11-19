@echo off
cd /d "%~dp0"
if not exist .venv (
  echo First time setup, please wait...
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -q -U -r requirements.txt
python cloudflare_connect.py
pause
