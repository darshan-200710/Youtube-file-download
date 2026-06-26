# YouTube Video Downloader

A simple Streamlit app to download YouTube videos with resolution selection and progress tracking.

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/Youtube-file-download.git
cd Youtube-file-download

# Create virtual environment
python -m venv .venv

# Activate it
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**. Paste a YouTube URL, pick a resolution, and download.

## Notes

- ffmpeg is bundled via `imageio-ffmpeg` — no manual install needed.
- Works best on a residential IP (your home computer). YouTube blocks most data-center IPs.
- Downloaded files are saved to the `downloads/` folder.

## License

MIT
