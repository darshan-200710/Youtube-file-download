from __future__ import annotations

import re
import shutil
import threading
import uuid
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError


ProgressCallback = Callable[[dict], None]


class DownloaderError(Exception):
    """Base exception for user-facing downloader failures."""


class InvalidURLError(DownloaderError):
    """Raised when a URL is missing or is not a supported video URL."""


class VideoUnavailableError(DownloaderError):
    """Raised when YouTube refuses access to the video metadata or media."""


@dataclass(frozen=True)
class VideoFormat:
    format_id: str
    label: str
    height: int
    extension: str
    filesize: int | None
    fps: float | None
    note: str | None


@dataclass(frozen=True)
class VideoInfo:
    id: str
    title: str
    webpage_url: str
    thumbnail: str | None
    duration: int | None
    uploader: str | None
    formats: list[VideoFormat]


YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be|m\.youtube\.com|music\.youtube\.com)/.+",
    re.IGNORECASE,
)


DOWNLOAD_DIR = Path(__file__).resolve().parent / "downloads"


def validate_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        raise InvalidURLError("Paste a YouTube video URL first.")
    if not YOUTUBE_URL_RE.match(cleaned):
        raise InvalidURLError("That does not look like a supported YouTube URL.")
    return cleaned


@lru_cache(maxsize=1)
def get_ffmpeg_location() -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def has_ffmpeg() -> bool:
    return get_ffmpeg_location() is not None


def _base_options(progress_hook: ProgressCallback | None = None) -> dict:
    options: dict = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 5,
        "file_access_retries": 5,
        "concurrent_fragment_downloads": 1,
        "continuedl": True,
        "nopart": False,
        "windowsfilenames": True,
        "restrictfilenames": False,
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if progress_hook:
        options["progress_hooks"] = [progress_hook]
    ffmpeg_location = get_ffmpeg_location()
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    return options


def _map_download_error(exc: Exception) -> DownloaderError:
    message = str(exc)
    lower = message.lower()

    if any(term in lower for term in ("private video", "members-only", "sign in to confirm")):
        return VideoUnavailableError(
            "This video is private, members-only, or requires sign-in. It cannot be downloaded here."
        )
    if any(term in lower for term in ("age-restricted", "confirm your age", "age restricted")):
        return VideoUnavailableError(
            "This video appears to be age-restricted. This app does not bypass age gates."
        )
    if any(term in lower for term in ("video unavailable", "removed by the uploader", "copyright claim")):
        return VideoUnavailableError("This video is unavailable on YouTube.")
    if "unsupported url" in lower:
        return InvalidURLError("The URL is not supported by yt-dlp.")
    if "requested format is not available" in lower:
        return VideoUnavailableError(
            "That resolution is not currently available for this video. Click Fetch Info again and choose another resolution."
        )
    return VideoUnavailableError("Could not process this video. Check the URL and try again.")


def _format_filesize(size: int | None) -> str:
    if not size:
        return "unknown size"

    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return "unknown size"


def _iter_video_formats(raw_formats: Iterable[dict]) -> list[VideoFormat]:
    seen_heights: set[int] = set()
    results: list[VideoFormat] = []

    for item in raw_formats:
        height = item.get("height")
        vcodec = item.get("vcodec")
        if not height or height < 144 or vcodec in (None, "none"):
            continue

        ext = item.get("ext") or "mp4"
        filesize = item.get("filesize") or item.get("filesize_approx")
        fps = item.get("fps")
        note = item.get("format_note")
        label = f"{height}p"
        if fps and fps >= 50:
            label += f"{int(fps)}"
        label += f" - {ext.upper()} - {_format_filesize(filesize)}"

        # Prefer the best entry yt-dlp exposes for each height to keep the UI compact.
        if height in seen_heights:
            continue
        seen_heights.add(height)

        results.append(
            VideoFormat(
                format_id=f"height:{int(height)}",
                label=label,
                height=int(height),
                extension=ext,
                filesize=filesize,
                fps=fps,
                note=note,
            )
        )

    sorted_results = sorted(results, key=lambda fmt: fmt.height, reverse=True)
    if sorted_results:
        sorted_results.insert(
            0,
            VideoFormat(
                format_id="best",
                label="Best available",
                height=0,
                extension="mp4",
                filesize=None,
                fps=None,
                note="Automatic",
            ),
        )
    return sorted_results


def fetch_video_info(url: str) -> VideoInfo:
    clean_url = validate_url(url)

    options = _base_options()
    options.update({"skip_download": True, "format": "bestvideo+bestaudio/best"})

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            raw = ydl.extract_info(clean_url, download=False)
    except (DownloadError, ExtractorError, ValueError) as exc:
        raise _map_download_error(exc) from exc

    formats = _iter_video_formats(raw.get("formats", []))
    if not formats:
        raise VideoUnavailableError("No downloadable video formats were found for this URL.")

    return VideoInfo(
        id=raw.get("id") or uuid.uuid4().hex,
        title=raw.get("title") or "Untitled video",
        webpage_url=raw.get("webpage_url") or clean_url,
        thumbnail=raw.get("thumbnail"),
        duration=raw.get("duration"),
        uploader=raw.get("uploader"),
        formats=formats,
    )


def build_format_selector(format_id: str) -> str:
    # Best selected video-only stream plus best compatible audio. If the chosen
    # format already has audio, yt-dlp simply uses it.
    if format_id == "best":
        if has_ffmpeg():
            return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        return "best"

    if format_id.startswith("height:"):
        try:
            height = int(format_id.split(":", 1)[1])
        except ValueError:
            return build_format_selector("best")

        if has_ffmpeg():
            return (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            )
        return f"best[height<={height}]/best"

    if has_ffmpeg():
        return f"{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/{format_id}/best"
    return f"{format_id}/best"


def _is_format_unavailable_error(exc: Exception) -> bool:
    return "requested format is not available" in str(exc).lower()


def download_video(
    url: str,
    format_id: str,
    progress_hook: ProgressCallback | None = None,
    output_dir: Path | None = None,
) -> Path:
    clean_url = validate_url(url)
    destination = output_dir or DOWNLOAD_DIR
    destination.mkdir(parents=True, exist_ok=True)

    unique_prefix = uuid.uuid4().hex[:8]
    options = _base_options(progress_hook)

    postprocessors = []
    if has_ffmpeg():
        postprocessors.append(
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        )
        # Embed downloaded subtitles/captions into the MP4 container
        postprocessors.append(
            {
                "key": "FFmpegEmbedSubtitle",
            }
        )

    options.update(
        {
            "format": build_format_selector(format_id),
            "outtmpl": str(destination / f"%(title).180B-{unique_prefix}.%(ext)s"),
            "merge_output_format": "mp4",
            "postprocessors": postprocessors,
            # --- Captions / Subtitles ---
            "writesubtitles": True,           # download manual subtitles
            "writeautomaticsub": True,        # fallback to auto-generated captions
            "subtitleslangs": ["en.*", "en", "hi"],  # English + Hindi (add more as needed)
            "subtitlesformat": "srt/best",    # prefer SRT format
        }
    )

    before = set(destination.glob(f"*-{unique_prefix}.*"))
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([clean_url])
    except (DownloadError, ExtractorError, ValueError) as exc:
        if not _is_format_unavailable_error(exc) or format_id == "best":
            raise _map_download_error(exc) from exc

        options["format"] = build_format_selector("best")
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([clean_url])
        except (DownloadError, ExtractorError, ValueError) as retry_exc:
            raise _map_download_error(retry_exc) from retry_exc

    after = set(destination.glob(f"*-{unique_prefix}.*"))
    completed = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
    if not completed:
        completed = sorted(destination.glob(f"*-{unique_prefix}.*"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not completed:
        raise VideoUnavailableError("The download finished, but the output file could not be found.")

    output_file = completed[0]

    # Clean up standalone subtitle files (already embedded inside the MP4)
    _SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".lrc", ".ttml", ".srv1", ".srv2", ".srv3", ".json3"}
    for path in destination.glob(f"*-{unique_prefix}.*"):
        if path.suffix.lower() in _SUBTITLE_EXTENSIONS:
            try:
                path.unlink()
            except OSError:
                pass

    return output_file


def threaded_download(
    url: str,
    format_id: str,
    progress_hook: ProgressCallback | None = None,
    output_dir: Path | None = None,
) -> tuple[threading.Thread, dict]:
    state: dict = {"status": "starting", "path": None, "error": None}

    def worker() -> None:
        try:
            state["path"] = download_video(url, format_id, progress_hook, output_dir)
            state["status"] = "finished"
        except DownloaderError as exc:
            state["error"] = str(exc)
            state["status"] = "error"

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread, state
