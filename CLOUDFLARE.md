# SaveClip on Cloudflare (free)

**How it works:** Cloudflare can't run the downloader itself (Python + FFmpeg), so:

- **Cloudflare Worker (free)** shows the website at `https://saveclip.<your-name>.workers.dev`
- **Your computer** does the downloading, connected to Cloudflare through a free **Cloudflare Tunnel**

```
Phone / browser  →  saveclip.<you>.workers.dev (Cloudflare)  →  Tunnel  →  your PC (SaveClip)
```

Cost: **₹0 / $0**. The only catch: your computer must be **on** with SaveClip running for downloads to work.
(The paid alternative is Cloudflare Containers on the $5/month Workers Paid plan, using the Dockerfile.)

---

## Part A – Put the website on Cloudflare (one time, ~5 minutes)

1. Go to https://dash.cloudflare.com → **Workers & Pages**.
2. If you see your old **saveclip** Worker (the one showing 404), open it → **Settings** → bottom → **Delete**.
3. Click **Create** → **Import a repository** → connect **GitHub** → choose **SaveClip**.
4. Leave the settings as they are (project name `saveclip`, no build command) → **Create and deploy**.
5. When it finishes, open the Worker → **Settings** → **Variables and Secrets** → **Add**:
   - Type: **Secret**
   - Name: `SECRET`
   - Value: make up a password, e.g. `srinivas-saveclip-2026` (remember it)
   - Click **Deploy**.

Your website link is shown at the top, like **https://saveclip.bantusrinivas8.workers.dev**.
If you open it now it loads, but downloads say "computer is offline" until Part B is done.

From now on, any change pushed to GitHub updates the website automatically.

## Part B – Connect your computer (one time setup)

1. Install **Python** (python.org, tick "Add to PATH") and **FFmpeg**:
   `winget install ffmpeg`
2. Install **Cloudflare Tunnel**: open Command Prompt and run
   `winget install --id Cloudflare.cloudflared`
3. Download this repo (GitHub → **Code → Download ZIP**) and unzip it.

## Every time you want SaveClip online

Double-click **`start-cloudflare.bat`** (Mac/Linux: `./start-cloudflare-mac-linux.sh`).

The first time it asks for:
- your Worker link (e.g. `https://saveclip.bantusrinivas8.workers.dev`)
- the `SECRET` password from Part A

When you see **"SaveClip is LIVE"**, your workers.dev link works from any phone or computer.
Keep the black window open. Close it (or Ctrl+C) to go offline.

## Browser button and phone app

- **Extension:** in SaveClip settings put your workers.dev link as the server address.
- **Android:** open the workers.dev link in Chrome → ⋮ → **Install app**. Then use **Share → SaveClip** in any app.
- **iPhone:** Safari → Share → **Add to Home Screen**.

## Problems

| You see | Fix |
|---|---|
| "computer is offline" | Start `start-cloudflare.bat` on your PC and keep it open |
| "Wrong secret" in the black window | Delete `cloudflare-settings.txt` and start again, type the same SECRET as in Cloudflare |
| "cloudflared is not installed" | Run `winget install --id Cloudflare.cloudflared`, then reopen |
| YouTube says "sign in / not a bot" | Usually doesn't happen from a home PC; run `pip install -U yt-dlp` |

Only download content you own or have permission to use.
