#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then echo "First time setup, please wait..."; python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -U -r requirements.txt
python cloudflare_connect.py
