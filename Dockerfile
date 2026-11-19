FROM python:3.12-slim

# ffmpeg is needed for MP3 conversion and joining video + audio
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY static ./static

ENV HOST=0.0.0.0 PORT=8000 MAX_FILESIZE_MB=500 MAX_DURATION_MIN=60
EXPOSE 8000
# Update yt-dlp on every start, because sites change often
CMD pip install -q -U yt-dlp; uvicorn app:app --host 0.0.0.0 --port ${PORT}
