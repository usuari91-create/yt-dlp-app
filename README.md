# YT-DLP Web App (v2)

Self-hosted web UI around [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) with built-in
PO Token generation (via [`bgutil-ytdlp-pot-provider`](https://github.com/Brainicism/bgutil-ytdlp-pot-provider))
and cookie upload for YouTube.

## Features

- 🎬 Download video as **mp4** (up to 1080p)
- 🎵 Download audio as **mp3** (96 / 128 / 192 / 320 kbps)
- 🔍 Preview metadata (title, channel, duration, views, thumbnail) before downloading
- 🔐 **Cookie upload** — bring your own `cookies.txt` for YouTube
- 🪪 **PO Token server** — auto-started in the background (Node.js + bgutil POT)
- 🌐 Works with YouTube, Vimeo, Twitter/X, TikTok, SoundCloud, Reddit, Twitch, Bandcamp, etc.
  (any site yt-dlp supports)
- 📦 Single-process install: clones + builds bgutil on first run

## Requirements

- **Python 3.9+**
- **FFmpeg** (on `PATH` — needed for audio conversion and video merging)
- **Node.js 20+** (for yt-dlp's JS challenge solver + bgutil POT provider)
- **git** (only on first install — to fetch bgutil)
- Internet access to the target site

## Install & run

```bash
# 1. System deps
sudo apt-get install -y ffmpeg nodejs git     # Debian / Ubuntu
brew install ffmpeg node git                  # macOS

# 2. Start
chmod +x start.sh
./start.sh
# -> open http://localhost:8000
```

The first run installs Python deps, clones bgutil, builds it, then starts the
FastAPI app. The POT server is launched as a child process automatically.

Or run the backend directly:

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## YouTube & anti-bot: the honest version

YouTube applies strong anti-bot protections, especially against datacenter IPs.
The app handles them in three layers:

1. **PO Token server** — bgutil-ytdlp-pot-provider runs locally and generates
   proof-of-origin tokens that yt-dlp sends to YouTube. The server is
   auto-started by the backend.
2. **JS runtime** — yt-dlp's challenge solver is wired to `node` automatically.
3. **Cookies** — if YouTube still blocks you, the UI has a panel to upload a
   `cookies.txt` exported from a logged-in browser. Cookies are stored on disk
   and reused for subsequent requests.

If all three fail (which is expected from a datacenter IP without a real
YouTube session), the API returns a clear, actionable error and the UI tells
the user exactly what to do.

The other ~1500 sites supported by yt-dlp (Vimeo, SoundCloud, Bandcamp,
Twitter/X, etc.) work **without any of this**.

## API

| Method | Path                    | Description                                                |
|--------|-------------------------|------------------------------------------------------------|
| GET    | `/api/health`           | `{ok, yt_dlp_version, ffmpeg, node, pot_server, cookies}`  |
| GET    | `/api/info?url=&cookies=` | Returns metadata for the URL (no download).              |
| GET    | `/api/cookies/status`   | Whether a cookies file is configured.                      |
| POST   | `/api/cookies/upload`   | multipart `file` field — Netscape `cookies.txt`.           |
| POST   | `/api/cookies/clear`    | Drop the configured cookies.                               |
| POST   | `/api/download`         | Body: `{url, format_type, quality, cookies}`. Streams file. |

`cookies` can be `"auto"` (use uploaded file if present), `"none"`, `"browser"`,
or `"upload"`.

## Project layout

```
yt-dlp-app/
├── backend/
│   ├── main.py             # FastAPI app (info / download / cookies / POT lifecycle)
│   ├── requirements.txt
│   ├── data/               # created at runtime: cookies.txt, pot-server.log
│   └── downloads/          # created at runtime: per-job tempdirs (auto-cleaned)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── start.sh                # one-shot installer + runner
└── README.md
```

## Notes

- File size is capped at 2 GB per download. Adjust `MAX_FILE_SIZE` in `backend/main.py`.
- Cookies file lives at `backend/data/cookies.txt`. Delete it to wipe.
- The bgutil POT server logs to `backend/data/pot-server.log`.
- Respect content creators and site ToS.
