# YouTube Video Downloader

FastAPI + Streamlit + yt-dlp downloader with metadata lookup, resolution selection, graceful error messages, and local file output.

## Setup

```powershell
cd "D:\projects\board\yt do"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

The app uses `imageio-ffmpeg` from `requirements.txt`, so you do not need to manually add `ffmpeg` to Windows `PATH`. YouTube often serves high-resolution video and audio as separate streams, and ffmpeg is needed to merge them.

## Run Streamlit UI

```powershell
py -m streamlit run app.py
```

## Streamlit Cloud note

The app works by making server-side requests to YouTube through `yt-dlp`. Streamlit Community Cloud may be blocked by YouTube's anti-bot checks because it runs from shared data-center IP addresses. If the hosted app says YouTube is blocking the hosted server, the URL is usually not the problem.

For reliable downloads, run the app locally or deploy it on a server/network that YouTube allows.

## Run FastAPI API

```powershell
py -m uvicorn api:app --reload
```

Endpoints:

- `GET /health`
- `POST /info` with `{ "url": "https://www.youtube.com/watch?v=..." }`
- `POST /download` with `{ "url": "...", "format_id": "..." }`

Downloaded files are saved in the local `downloads` folder.
