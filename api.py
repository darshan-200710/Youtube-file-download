from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from downloader import DownloaderError, download_video, fetch_video_info


app = FastAPI(title="YouTube Downloader API", version="1.0.0")


class InfoRequest(BaseModel):
    url: HttpUrl


class DownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/info")
def info(payload: InfoRequest) -> dict:
    try:
        video = fetch_video_info(str(payload.url))
    except DownloaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": video.id,
        "title": video.title,
        "webpage_url": video.webpage_url,
        "thumbnail": video.thumbnail,
        "duration": video.duration,
        "uploader": video.uploader,
        "formats": [format_item.__dict__ for format_item in video.formats],
    }


@app.post("/download")
def download(payload: DownloadRequest) -> FileResponse:
    try:
        output_path = download_video(str(payload.url), payload.format_id)
    except DownloaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    path = Path(output_path)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=path.name,
    )
