"""SaveClip: paste a social media link, download MP4 video or MP3 audio.

Backend: FastAPI + yt-dlp (+ ffmpeg for merging/conversion).
Only download content you own or have permission to use.
"""
import ipaddress
import os
import re
import shutil
import socket
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

MAX_FILESIZE = int(os.getenv("MAX_FILESIZE_MB", "1024")) * 1024 * 1024
MAX_DURATION = int(os.getenv("MAX_DURATION_MIN", "180")) * 60
VIDEO_HEIGHTS = [2160, 1440, 1080, 720, 480, 360, 240, 144]
MP3_BITRATES = {"128", "192", "320"}

app = FastAPI(title="SaveClip")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# The browser extension and the Cloudflare-hosted page call this API from other origins.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], expose_headers=["Content-Disposition"])


class InfoRequest(BaseModel):
    url: str


def check_url(url: str) -> str:
    """Allow only public http(s) links (blocks localhost / private network)."""
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(400, "Please paste a valid http(s) link.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        # Can't resolve locally (e.g. behind a proxy): let yt-dlp try it.
        return url
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise HTTPException(400, "That link is not allowed.")
    return url


def base_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "max_filesize": MAX_FILESIZE,
        "socket_timeout": 30,
    }


def friendly_error(e: Exception) -> str:
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e))
    msg = msg.replace("ERROR: ", "")
    low = msg.lower()
    if "drm" in low:
        return "This video is DRM-protected and can't be downloaded."
    if "private" in low or "login" in low or "sign in" in low:
        return "This post is private or needs a login, so it can't be downloaded."
    if "unsupported url" in low:
        return "This website or link type isn't supported."
    return msg[:300] or "Something went wrong."


@app.post("/api/info")
def get_info(req: InfoRequest):
    url = check_url(req.url)
    try:
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:  # yt-dlp raises many error types
        raise HTTPException(400, friendly_error(e))
    if info.get("_type") == "playlist":
        entries = [x for x in (info.get("entries") or []) if x]
        if not entries:
            raise HTTPException(400, "No video found at this link.")
        info = entries[0]

    heights = sorted(
        {f["height"] for f in info.get("formats") or []
         if f.get("height") and f.get("vcodec") not in (None, "none")},
        reverse=True,
    )
    qualities = [h for h in VIDEO_HEIGHTS if any(x >= h for x in heights)] if heights else []
    return {
        "title": info.get("title") or "video",
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "site": info.get("extractor_key"),
        "has_video": bool(heights) or info.get("vcodec") != "none",
        "video_qualities": qualities,
    }


def safe_name(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n]+', " ", title).strip()
    return (name or "download")[:120]


def build_opts(kind: str, quality: str, tmp: str) -> dict:
    opts = base_opts()
    opts["outtmpl"] = os.path.join(tmp, "%(title).100B.%(ext)s")
    opts["match_filter"] = yt_dlp.utils.match_filter_func(f"duration <=? {MAX_DURATION}")
    if kind == "mp3":
        bitrate = quality if quality in MP3_BITRATES else "192"
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate},
            {"key": "FFmpegMetadata"},
        ]
    else:
        h = f"[height<={int(quality)}]" if quality.isdigit() else ""
        opts["format"] = (
            f"bestvideo{h}[ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo{h}+bestaudio/best{h}[ext=mp4]/best{h}/best"
        )
        opts["merge_output_format"] = "mp4"
        # Re-encode to MP4 only when the source isn't already MP4-compatible.
        opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    return opts


def fetch_file(url: str, kind: str, quality: str, tmp: str, progress=None):
    """Download + convert into tmp. Returns (path, filename). Raises HTTPException."""
    opts = build_opts(kind, quality, tmp)
    if progress:
        opts["progress_hooks"] = [progress]
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info.get("_type") == "playlist":
                info = next((x for x in info.get("entries") or [] if x), info)
    except Exception as e:
        raise HTTPException(400, friendly_error(e))
    want_ext = ".mp3" if kind == "mp3" else ".mp4"
    files = [f for f in os.listdir(tmp) if f.endswith(want_ext)]
    if not files:
        raise HTTPException(400, "Download failed (file too big, too long, or not available).")
    return os.path.join(tmp, files[0]), safe_name(info.get("title") or "download") + want_ext


def media_type(kind: str) -> str:
    return "audio/mpeg" if kind == "mp3" else "video/mp4"


@app.get("/api/download")
def download(
    url: str,
    kind: str = Query("mp4", pattern="^(mp4|mp3)$"),
    quality: str = "best",
):
    """One-shot download (fine locally; behind Cloudflare use /api/jobs for long videos)."""
    url = check_url(url)
    tmp = tempfile.mkdtemp(prefix="saveclip_")
    try:
        path, filename = fetch_file(url, kind, quality, tmp)
    except HTTPException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return FileResponse(path, media_type=media_type(kind), filename=filename,
                        background=BackgroundTask(shutil.rmtree, tmp, ignore_errors=True))


# ---- Background jobs: start -> poll progress -> fetch file -------------------
# Cloudflare closes requests that wait more than ~100 seconds for an answer, so
# long videos are prepared in the background while the page polls for progress.

JOB_TTL = 30 * 60
JOBS: dict = {}
JOBS_LOCK = threading.Lock()
EXECUTOR = ThreadPoolExecutor(max_workers=int(os.getenv("MAX_PARALLEL_JOBS", "3")))


class JobRequest(BaseModel):
    url: str
    kind: str = "mp4"
    quality: str = "best"


def cleanup_jobs():
    now = time.time()
    with JOBS_LOCK:
        old = [k for k, j in JOBS.items() if now - j["created"] > JOB_TTL]
        for k in old:
            shutil.rmtree(JOBS.pop(k)["tmp"], ignore_errors=True)


def run_job(job_id: str):
    job = JOBS[job_id]
    job["status"] = "working"

    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                job["progress"] = min(99, int(d.get("downloaded_bytes", 0) * 100 / total))
        elif d.get("status") == "finished":
            job["progress"] = 99

    try:
        path, filename = fetch_file(job["url"], job["kind"], job["quality"], job["tmp"], hook)
        job.update(status="done", progress=100, path=path, filename=filename)
    except HTTPException as e:
        job.update(status="error", error=e.detail)
    except Exception as e:  # never leave a job stuck in "working"
        job.update(status="error", error=friendly_error(e))


@app.post("/api/jobs")
def create_job(req: JobRequest):
    cleanup_jobs()
    if req.kind not in ("mp4", "mp3"):
        raise HTTPException(400, "Choose mp4 or mp3.")
    url = check_url(req.url)
    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {"url": url, "kind": req.kind, "quality": req.quality or "best",
                        "status": "queued", "progress": 0, "created": time.time(),
                        "tmp": tempfile.mkdtemp(prefix="saveclip_")}
    EXECUTOR.submit(run_job, job_id)
    return {"id": job_id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "This download expired. Please try again.")
    return {"status": job["status"], "progress": job["progress"],
            "error": job.get("error"), "filename": job.get("filename")}


@app.get("/api/jobs/{job_id}/file")
def job_file(job_id: str):
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "This download isn't ready or has expired.")
    return FileResponse(job["path"], media_type=media_type(job["kind"]), filename=job["filename"])


@app.get("/api/health")
def health():
    return {"ok": True, "ffmpeg": bool(shutil.which("ffmpeg")), "yt_dlp": yt_dlp.version.__version__}


app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
