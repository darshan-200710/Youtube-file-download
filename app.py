from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

from downloader import (
    DownloaderError,
    VideoFormat,
    VideoInfo,
    download_video,
    fetch_video_info,
    get_ffmpeg_location,
    has_ffmpeg,
)


st.set_page_config(
    page_title="YouTube Video Downloader",
    page_icon=":arrow_down:",
    layout="centered",
)


def _duration_label(seconds: int | None) -> str:
    if not seconds:
        return "Unknown duration"
    minutes, remaining = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{remaining:02d}"
    return f"{minutes}:{remaining:02d}"


def _format_progress(progress: dict) -> tuple[float, str]:
    status = progress.get("status")
    if status == "downloading":
        total = progress.get("total_bytes") or progress.get("total_bytes_estimate") or 0
        downloaded = progress.get("downloaded_bytes") or 0
        percent = min(downloaded / total, 1.0) if total else 0.0
        speed = progress.get("_speed_str") or ""
        eta = progress.get("_eta_str") or ""
        label = f"Downloading... {percent:.0%}"
        if speed.strip():
            label += f" at {speed.strip()}"
        if eta.strip():
            label += f" | ETA {eta.strip()}"
        return percent, label
    if status == "finished":
        return 1.0, "Finalizing file..."
    return 0.0, "Starting download..."


def _show_video_info(info: VideoInfo) -> None:
    col_thumb, col_meta = st.columns([1, 2], vertical_alignment="center")
    with col_thumb:
        if info.thumbnail:
            st.image(info.thumbnail, use_container_width=True)
    with col_meta:
        st.subheader(info.title)
        if info.uploader:
            st.caption(f"{info.uploader} | {_duration_label(info.duration)}")
        else:
            st.caption(_duration_label(info.duration))


def _select_format(formats: list[VideoFormat]) -> VideoFormat:
    labels = [fmt.label for fmt in formats]
    selected_label = st.selectbox("Resolution", labels, index=0)
    return formats[labels.index(selected_label)]


def _download_to_local(url: str, selected: VideoFormat) -> None:
    progress_slot = st.empty()
    status_slot = st.empty()
    progress_bar = progress_slot.progress(0.0)

    def progress_hook(data: dict) -> None:
        percent, label = _format_progress(data)
        progress_bar.progress(percent)
        status_slot.caption(label)

    with st.spinner("Preparing download..."):
        try:
            status_slot.caption("Starting download...")

            start = time.monotonic()
            output_path = download_video(
                url,
                selected.format_id,
                progress_hook=progress_hook,
                cookies_file=st.session_state.cookies_path,
                player_client=st.session_state.player_client,
            )

            percent, label = _format_progress({"status": "finished"})
            progress_bar.progress(percent)
            status_slot.caption(label)

            # Keep fast downloads from looking like a missed click.
            elapsed = time.monotonic() - start
            if elapsed < 0.5:
                time.sleep(0.5 - elapsed)

        except DownloaderError as exc:
            progress_slot.empty()
            status_slot.empty()
            st.error(str(exc))
            return

    st.success(f"Downloaded: {output_path.name}")
    st.caption(f"Saved to: {output_path}")

    with Path(output_path).open("rb") as file:
        st.download_button(
            "Save a copy from browser",
            data=file,
            file_name=Path(output_path).name,
            mime="video/mp4",
            use_container_width=True,
        )


def main() -> None:
    st.title("YouTube Video Downloader")
    st.caption("Fetch video details, choose a resolution, and download to this machine.")

    # --- Sidebar: advanced options ---
    with st.sidebar:
        st.subheader("⚙️ Advanced")

        # Cookies file upload
        st.markdown("**Cookies (optional)**")
        st.caption(
            "Upload a Netscape-format cookies.txt file from your browser "
            "to help bypass YouTube restrictions on data-center IPs."
        )
        uploaded_cookies = st.file_uploader(
            "Choose cookies.txt",
            type=["txt"],
            label_visibility="collapsed",
        )
        if uploaded_cookies is not None:
            cookies_dir = Path(__file__).resolve().parent / ".cookies"
            cookies_dir.mkdir(parents=True, exist_ok=True)
            cookies_path = cookies_dir / "cookies.txt"
            cookies_path.write_bytes(uploaded_cookies.getvalue())
            st.session_state.cookies_path = str(cookies_path)
            st.success("Cookies loaded ✓")
        else:
            st.session_state.cookies_path = None

        # Player client selector
        st.markdown("**YouTube client**")
        st.caption(
            "Changing the client can sometimes bypass blocking. "
            "Try 'android' if 'web' is blocked."
        )
        # Use a key so Streamlit preserves the widget state across reruns.
        st.selectbox(
            "Player client",
            options=["web", "android", "ios"],
            index=0,
            label_visibility="collapsed",
            key="player_client_selector",
        )
        st.session_state.player_client = st.session_state.player_client_selector

        st.divider()
        st.markdown(
            "### 💡 Tips\n"
            "- **Run locally** for best results; Streamlit Cloud IPs are often blocked by YouTube.\n"
            "- Upload a **cookies.txt** (exported from your browser while logged into YouTube) "
            "to bypass the block.\n"
            "- Switch the **YouTube client** to 'android' if 'web' doesn't work."
        )

    # --- Main area ---
    if "video_info" not in st.session_state:
        st.session_state.video_info = None
    if "last_url" not in st.session_state:
        st.session_state.last_url = ""
    if "cookies_path" not in st.session_state:
        st.session_state.cookies_path = None
    if "player_client" not in st.session_state:
        st.session_state.player_client = "web"

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

    fetch_clicked = st.button("Fetch Info", type="primary", use_container_width=True)
    if fetch_clicked:
        try:
            with st.spinner("Fetching video info..."):
                st.session_state.video_info = fetch_video_info(
                    url,
                    cookies_file=st.session_state.cookies_path,
                    player_client=st.session_state.player_client,
                )
                st.session_state.last_url = url
        except DownloaderError as exc:
            st.session_state.video_info = None
            st.error(str(exc))

    info: VideoInfo | None = st.session_state.video_info
    if info:
        st.divider()
        _show_video_info(info)
        ffmpeg_location = get_ffmpeg_location()
        if not has_ffmpeg():
            st.warning(
                "ffmpeg is not available. Install dependencies again to enable high-resolution video with audio."
            )
        elif ffmpeg_location:
            st.caption(f"ffmpeg ready: {ffmpeg_location}")
        selected = _select_format(info.formats)

        if st.button("Download", use_container_width=True):
            _download_to_local(st.session_state.last_url, selected)


if __name__ == "__main__":
    main()
