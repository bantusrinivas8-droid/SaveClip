# SaveClip – Video (MP4) & Audio (MP3) Downloader

Paste a link from YouTube, Instagram, Facebook, X (Twitter), TikTok, Vimeo, SoundCloud
and 1000+ other sites, see the title and thumbnail, then download it as an **MP4 video**
(144p up to 4K, whatever the video has) or an **MP3 song** (128 / 192 / 320 kbps).

It works on phones and computers.

> ⚠️ **Disclaimer:** Only download videos and music that you own or have permission to use.
> Downloading copyrighted content without permission may break the law and the site's terms.
> Private posts and DRM-protected content (Netflix, Spotify, paid movies, etc.) are **not** supported.

---

## How to run it (simple steps)

### Step 1 – Install 2 free programs (only once)

1. **Python** (version 3.9 or newer): https://www.python.org/downloads/
   - On Windows, tick **"Add python.exe to PATH"** on the first install screen.
2. **FFmpeg** (needed for MP3 and for joining video + sound):
   - **Windows:** open *Command Prompt* and run: `winget install ffmpeg`
   - **Mac:** install Homebrew (https://brew.sh), then run: `brew install ffmpeg`
   - **Linux (Ubuntu):** `sudo apt install ffmpeg`

Close and reopen the terminal after installing.

### Step 2 – Start the website

- **Windows:** double-click **`start-windows.bat`**
- **Mac / Linux:** open Terminal in this folder and run `./start-mac-linux.sh`

The first time it installs everything (takes 1–2 minutes).

### Step 3 – Use it

Open **http://127.0.0.1:8000** in your browser, paste a link, press **Get video**,
pick MP4 or MP3 and a quality. The file goes to your Downloads folder.

To stop the website, press **Ctrl + C** in the black window.

---

## Manual run (if you prefer typing commands)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Use it from your phone on the same Wi‑Fi

Start it with `HOST=0.0.0.0 python app.py` (Windows: `set HOST=0.0.0.0` then `python app.py`),
find your computer's IP (e.g. `192.168.1.5`) and open `http://192.168.1.5:8000` on your phone.

---

## If something stops working

Social media sites change often. Most problems are fixed by updating the download engine:

```bash
pip install -U yt-dlp
```

(The start scripts already do this every time you start.)

| Message | What it means |
|---|---|
| "private or needs a login" | The post is private / age-restricted. Only public posts work. |
| "isn't supported" | That website isn't supported or the link is wrong. |
| "DRM-protected" | Protected content, can't be downloaded. |
| Download is slow | Long or 4K videos take time; the server downloads first, then sends it to you. |

---

## Settings (optional)

| Variable | Default | Meaning |
|---|---|---|
| `HOST` | `127.0.0.1` | Use `0.0.0.0` to open it to other devices |
| `PORT` | `8000` | Port number |
| `MAX_FILESIZE_MB` | `1024` | Biggest file allowed |
| `MAX_DURATION_MIN` | `180` | Longest video allowed (minutes) |

## Project files

```
app.py              backend (FastAPI + yt-dlp + ffmpeg)
static/index.html   the web page
requirements.txt    Python packages
start-windows.bat   one-click start for Windows
start-mac-linux.sh  one-click start for Mac/Linux
```

## Putting it on the internet

You can host it on any server that runs Python and has FFmpeg (a VPS, Render, Railway, etc.)
with `uvicorn app:app --host 0.0.0.0 --port 8000`. Note that big sites (especially YouTube)
often block downloads from data-center IPs, so it works most reliably when run from a home connection.
If you make it public, add rate limiting and a clear terms-of-use page.
