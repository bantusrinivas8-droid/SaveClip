"""Run SaveClip on this computer and connect it to your Cloudflare Worker (free).

1. Starts the SaveClip server (app.py) on http://127.0.0.1:8000
2. Opens a free Cloudflare Tunnel (cloudflared) to it
3. Tells your Worker the tunnel address, so https://saveclip.<you>.workers.dev works

Settings are kept in cloudflare-settings.txt next to this file.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = os.path.join(HERE, "cloudflare-settings.txt")
PORT = os.getenv("PORT", "8000")


def load_settings():
    cfg = {}
    if os.path.exists(SETTINGS):
        for line in open(SETTINGS, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    if not cfg.get("WORKER_URL") or not cfg.get("SECRET"):
        print("\nFirst time setup")
        print("----------------")
        cfg["WORKER_URL"] = input("Your Worker link (e.g. https://saveclip.yourname.workers.dev): ").strip().rstrip("/")
        cfg["SECRET"] = input("The SECRET you added in Cloudflare: ").strip()
        with open(SETTINGS, "w", encoding="utf-8") as f:
            f.write("# SaveClip Cloudflare settings (keep this private)\n")
            f.write(f"WORKER_URL={cfg['WORKER_URL']}\nSECRET={cfg['SECRET']}\n")
        print(f"Saved to {SETTINGS}\n")
    if not cfg["WORKER_URL"].startswith("http"):
        cfg["WORKER_URL"] = "https://" + cfg["WORKER_URL"]
    return cfg


def register(cfg, tunnel_url):
    req = urllib.request.Request(
        cfg["WORKER_URL"] + "/api/_register",
        data=json.dumps({"url": tunnel_url, "secret": cfg["SECRET"]}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "SaveClip-connector"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200, ""
    except urllib.error.HTTPError as e:
        try:
            return False, json.load(e).get("detail", str(e))
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def main():
    cloudflared = shutil.which("cloudflared")
    if not cloudflared:
        print("cloudflared is not installed.")
        print("Windows: open Command Prompt and run:  winget install --id Cloudflare.cloudflared")
        print("Mac:     brew install cloudflared")
        print("Then close this window and start again.")
        input("Press Enter to close...")
        sys.exit(1)

    cfg = load_settings()

    env = dict(os.environ, HOST="127.0.0.1", PORT=PORT)
    server = subprocess.Popen([sys.executable, os.path.join(HERE, "app.py")], env=env)
    tunnel = subprocess.Popen(
        [cloudflared, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )

    found = {"url": None}

    def read_tunnel():
        for line in tunnel.stdout:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m and not found["url"]:
                found["url"] = m.group(0)

    threading.Thread(target=read_tunnel, daemon=True).start()

    print("Starting SaveClip and the Cloudflare Tunnel...")
    for _ in range(60):
        if found["url"]:
            break
        time.sleep(1)
    if not found["url"]:
        print("Could not open the Cloudflare Tunnel. Check your internet and try again.")
        server.terminate(); tunnel.terminate()
        input("Press Enter to close...")
        sys.exit(1)

    time.sleep(5)  # give the new tunnel a moment to come online
    ok, err = register(cfg, found["url"])
    if not ok:
        print(f"\nCouldn't connect to your Worker: {err}")
        print(f"Check WORKER_URL and SECRET in {SETTINGS} (delete the file to enter them again).")
    else:
        print("\n==============================================")
        print(" SaveClip is LIVE at:", cfg["WORKER_URL"])
        print(" Keep this window open. Ctrl+C to stop.")
        print("==============================================\n")

    try:
        while server.poll() is None and tunnel.poll() is None:
            time.sleep(600)
            register(cfg, found["url"])  # refresh, in case the Worker was redeployed
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate(); tunnel.terminate()
        print("SaveClip stopped.")


if __name__ == "__main__":
    main()
