# YouTube Video Downloader

A Streamlit app to download YouTube videos. Works best when run locally due to YouTube's anti-bot measures blocking data-center IPs.

## Quick Start (Local - Recommended)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## The YouTube Blocking Problem

**YouTube blocks requests from data-center IPs** (AWS, GCP, Azure, Streamlit Cloud, etc.). This is why you see:

> "YouTube is blocking this server (Streamlit Cloud uses data-center IPs). Try running the app on your own computer for best results."

### Solutions for Production Deployment

#### Option 1: Run Locally (Best)
Run on your own computer - residential IPs work perfectly.

#### Option 2: VPS with Residential Proxy
Deploy to a VPS and route traffic through a residential proxy service.

#### Option 3: Provide YouTube Cookies (Streamlit Cloud)
Export cookies from your browser and add them as a secret:

1. Install "Get cookies.txt LOCALLY" browser extension
2. Export YouTube cookies to `cookies.txt`
3. On Streamlit Cloud: Settings → Secrets → Add `YOUTUBE_COOKIE_FILE` with the file content
4. Or base64 encode the file and decode at runtime

#### Option 4: PO Token + Visitor Data (Advanced)
Get Proof-of-Origin tokens from a logged-in session:

```bash
# Set these as environment variables/secrets
YOUTUBE_PO_TOKEN="your_po_token"
YOUTUBE_VISITOR_DATA="your_visitor_data"
```

## Project Structure

```
├── app.py           # Streamlit UI
├── downloader.py    # yt-dlp wrapper with anti-bot measures
├── api.py           # FastAPI backend (optional)
├── main.py          # Entry point
├── requirements.txt
└── .streamlit/config.toml
```

## Anti-Bot Measures Included

- Multiple player clients: `android`, `web`, `tv_embedded`, `ios`, `mweb`
- Full browser headers (User-Agent, Accept, Sec-Fetch-*, etc.)
- Cookie file support via `YOUTUBE_COOKIE_FILE`
- PO Token support via `YOUTUBE_PO_TOKEN`
- Visitor Data support via `YOUTUBE_VISITOR_DATA`
- Aggressive retries and timeouts
- Format fallback logic

## Deploying to Streamlit Cloud

1. Push to GitHub
2. Connect repo to Streamlit Cloud
3. Add secrets in Settings → Secrets:
   ```toml
   YOUTUBE_COOKIE_FILE = """<base64_encoded_cookies>"""
   # OR
   YOUTUBE_PO_TOKEN = "your_token"
   YOUTUBE_VISITOR_DATA = "your_data"
   ```
4. Deploy

**Note:** Even with cookies/tokens, Streamlit Cloud's shared IPs may still get rate-limited. Local usage is most reliable.

## License

MIT