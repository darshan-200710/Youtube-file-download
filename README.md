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

## Run FastAPI API

```powershell
py -m uvicorn api:app --reload
```

Endpoints:

- `GET /health`
- `POST /info` with `{ "url": "https://www.youtube.com/watch?v=..." }`
- `POST /download` with `{ "url": "...", "format_id": "..." }`

Downloaded files are saved in the local `downloads` folder.
