#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "First time setup, please wait..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -U -r requirements.txt
echo
echo "SaveClip is running. Open http://127.0.0.1:8000 in your browser."
echo "Press Ctrl+C to stop."
python app.py
