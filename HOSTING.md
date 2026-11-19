> **Want it free on Cloudflare only?** Follow [CLOUDFLARE.md](CLOUDFLARE.md) instead.

# Put SaveClip on the internet (free, step by step)

## Why Cloudflare Workers shows "404"

Cloudflare Workers can only run small JavaScript programs. SaveClip needs **Python**,
**yt-dlp** and **FFmpeg** running on a real server to download and convert videos.
Workers can't run those, so there was nothing there to show and you got a 404.

We'll use **Render** instead. It runs the whole app (page + downloader) from the
`Dockerfile` in this folder, and it has a free plan.

---

## Step 1 – Put the files on GitHub

1. Go to https://github.com/new
2. Repository name: `saveclip`. Choose **Public** or **Private**. Click **Create repository**.
3. On the next page click **"uploading an existing file"**.
4. Unzip `video-downloader.zip`, open the `video-downloader` folder, select **everything inside it**
   (including the `static` folder) and drag it into the GitHub page.
5. Click **Commit changes**.

Check that you can see `Dockerfile`, `app.py`, `render.yaml` and the `static` folder in the repo.

## Step 2 – Create the site on Render

1. Go to https://render.com and click **Get Started**. Sign up **with GitHub**.
2. Click **New +** → **Web Service**.
3. Pick your `saveclip` repository (click "Configure account" if you don't see it, and allow access).
4. Fill in:
   - **Name:** `saveclip`
   - **Language / Runtime:** `Docker` (it's picked automatically)
   - **Instance type:** `Free`
5. Click **Deploy Web Service**.

Wait about 5 minutes. When the log says **"Your service is live"**, open the link at the top,
for example **https://saveclip.onrender.com**. That's your website.

## Step 3 – Updating later

Change a file on GitHub (edit or upload again) → Render rebuilds and updates the site by itself.

---

## Good to know

- **Free plan sleeps.** If nobody uses it for 15 minutes, the next visit takes about 1 minute to wake up.
  Paid plan (~$7/month) stays awake.
- **YouTube often blocks cloud servers.** You may see "Sign in to confirm you're not a bot" for YouTube links.
  Instagram, Facebook, X and TikTok usually work better. For YouTube, running SaveClip on your own
  computer (start-windows.bat) is the most reliable.
- **Limits:** online the site allows files up to 500 MB and videos up to 60 minutes (change
  `MAX_FILESIZE_MB` / `MAX_DURATION_MIN` under Render → Environment).
- **Your own domain:** Render → Settings → Custom Domains. If your domain is on Cloudflare,
  add the CNAME record Render shows you (set it to "DNS only", grey cloud).
- **Public site responsibility:** keep the "only download what you own or have permission to use"
  notice, and add a contact email so rights holders can reach you.

## Other hosts that also work

Anything that can run a Dockerfile: **Railway**, **Fly.io**, **Koyeb**, or your own VPS
(`docker build -t saveclip . && docker run -p 80:8000 saveclip`).
