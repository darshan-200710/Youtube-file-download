# YouTube Video Downloader

FastAPI + Streamlit + yt-dlp downloader with metadata lookup, resolution selection, graceful error messages, and local file output.

## Setup (Local)

```powershell
cd "D:\projects\yt do"
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

The app uses `imageio-ffmpeg` from `requirements.txt`, so you do not need to manually add `ffmpeg` to Windows `PATH`. YouTube often serves high-resolution video and audio as separate streams, and ffmpeg is needed to merge them.

## Run Streamlit UI (Local)

```powershell
py -m streamlit run app.py
```

## Deploy to Streamlit Cloud

### Step 1: Push to GitHub

1. Create a **public** GitHub repository (e.g., `Youtube-file-download`).
2. Push all project files to the `main` branch:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/Youtube-file-download.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository (`YOUR_USERNAME/Youtube-file-download`).
4. Branch: `main`.
5. Main file path: `app.py`.
6. Click **"Deploy"**.

**Important:** Make sure your repository is **public** (Streamlit Cloud can deploy from private repos too, but it requires additional OAuth permissions).

## ⚠️ Streamlit Cloud & YouTube Blocking

YouTube often blocks requests from data-center IP addresses (like those used by Streamlit Cloud). If you see the error:
> *"YouTube is blocking requests from this hosted server"*

Here are your options:

### Option 1: Upload browser cookies (easiest)
1. Install a browser extension like **"Get cookies.txt LOCALLY"** (Chrome/Firefox).
2. While logged into YouTube, export your cookies as `cookies.txt` (Netscape format).
3. In the Streamlit app sidebar, upload the `cookies.txt` file.
4. Try fetching the video info again.

### Option 2: Switch YouTube client
In the sidebar, change the **YouTube client** from `web` to `android` and try again.

### Option 3: Run locally
For reliable downloads, run the app on your local machine.

### Option 4: Use a residential proxy
Deploy the app on a server with residential IPs (not data-center IPs).

## Run FastAPI API (Local)

```powershell
py -m uvicorn api:app --reload
```

Endpoints:

- `GET /health`
- `POST /info` with `{ "url": "https://www.youtube.com/watch?v=..." }`
- `POST /download` with `{ "url": "...", "format_id": "..." }`

Downloaded files are saved in the local `downloads` folder.
