"""
YT-DLP Web App — FastAPI backend (v2).

Adds:
  * Automatic PO Token (bgutil) HTTP server as a child process.
  * Cookie support: upload a cookies.txt OR point at a browser profile.
  * Optional JS runtime (node) auto-detection.
  * Clear, actionable error messages for YouTube anti-bot.

Endpoints
---------
  GET  /api/health                  -> {ok, yt_dlp_version, ffmpeg, pot_server, js_runtime}
  GET  /api/info?url=...            -> metadata + available formats
  GET  /api/cookies/status          -> whether a cookies file is configured
  POST /api/cookies/upload          -> multipart, field "file" = cookies.txt
  POST /api/cookies/clear           -> drop the configured cookies
  POST /api/download                -> {url, format_type, quality?, cookies? "upload"|"browser"|"none"}
"""

import os
import re
import io
import json
import time
import shutil
import signal
import logging
import tempfile
import threading
import subprocess
from pathlib import Path
from typing import Optional

import httpx
import yt_dlp
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, HttpUrl

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DATA_DIR = BASE_DIR / "data"
COOKIES_FILE = DATA_DIR / "cookies.txt"
POT_LOG = DATA_DIR / "pot-server.log"

BGUTIL_DIR = Path(os.environ.get("BGUTIL_DIR", "/opt/bgutil-provider/server"))
POT_PORT = int(os.environ.get("POT_PORT", "4416"))
POT_BASE_URL = f"http://127.0.0.1:{POT_PORT}"

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
POT_START_TIMEOUT = 45.0

for d in (DOWNLOAD_DIR, DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("yt-dlp-api")

app = FastAPI(
    title="YT-DLP Web App",
    description="Download video and audio from YouTube and 1500+ sites.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Autenticacion basica opcional (util en Render, que no tiene proxy propio)
# Se activa solo si defines APP_USER y APP_PASSWORD como variables de entorno.
# ----------------------------------------------------------------------------

import base64
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_APP_USER = os.environ.get("APP_USER")
_APP_PASSWORD = os.environ.get("APP_PASSWORD")


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not _APP_USER or not _APP_PASSWORD:
            return await call_next(request)

        # El health check de Render no manda credenciales; hay que dejarlo pasar
        # siempre o Render pensara que la app no responde.
        if request.url.path == "/api/health":
            return await call_next(request)

        auth = request.headers.get("authorization")
        if auth and auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth.split(" ", 1)[1]).decode()
                user, _, pwd = decoded.partition(":")
                if secrets.compare_digest(user, _APP_USER) and secrets.compare_digest(pwd, _APP_PASSWORD):
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            status_code=401,
            headers={"WWW-Authenticate": "Basic realm=\"yt-dlp-app\""},
            content="Autenticacion requerida",
        )


if _APP_USER and _APP_PASSWORD:
    app.add_middleware(BasicAuthMiddleware)


# ----------------------------------------------------------------------------
# PO Token (bgutil) lifecycle
# ----------------------------------------------------------------------------

_pot_proc: Optional[subprocess.Popen] = None
_pot_lock = threading.Lock()


def _has_node() -> bool:
    return shutil.which("node") is not None


def _has_bgutil_built() -> bool:
    return (BGUTIL_DIR / "build" / "main.js").exists()


def _pot_server_up() -> bool:
    try:
        r = httpx.get(f"{POT_BASE_URL}/ping", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _start_pot_server() -> Optional[subprocess.Popen]:
    """Start the bgutil POT server as a child process. Returns the Popen or None."""
    if not _has_node():
        log.warning("Node.js not found; POT server not started.")
        return None
    if not _has_bgutil_built():
        log.warning("bgutil-pot-provider not built at %s; POT server not started.", BGUTIL_DIR)
        return None
    if _pot_server_up():
        log.info("POT server already running at %s", POT_BASE_URL)
        return None

    log.info("Starting bgutil POT server (port %d) from %s", POT_PORT, BGUTIL_DIR)
    log_fh = open(POT_LOG, "ab", buffering=0)
    proc = subprocess.Popen(
        ["node", "build/main.js", "--port", str(POT_PORT)],
        cwd=str(BGUTIL_DIR),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # detach so it survives backend exit
    )

    # Wait for /ping
    deadline = time.time() + POT_START_TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            log.error("POT server exited early with code %s", proc.returncode)
            return None
        if _pot_server_up():
            log.info("POT server up (pid=%s)", proc.pid)
            return proc
        time.sleep(0.3)

    log.error("POT server did not become ready in %.1fs", POT_START_TIMEOUT)
    try:
        proc.terminate()
    except Exception:
        pass
    return None


def _ensure_pot_server() -> None:
    with _pot_lock:
        global _pot_proc
        if _pot_server_up():
            return
        _pot_proc = _start_pot_server()


@app.on_event("startup")
def _on_startup():
    # Try to start the POT server in the background. Don't block startup.
    threading.Thread(target=_ensure_pot_server, daemon=True).start()


@app.on_event("shutdown")
def _on_shutdown():
    global _pot_proc
    if _pot_proc and _pot_proc.poll() is None:
        try:
            os.killpg(os.getpgid(_pot_proc.pid), signal.SIGTERM)
        except Exception:
            pass
        _pot_proc = None


# ----------------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------------

class DownloadRequest(BaseModel):
    url: HttpUrl
    format_type: str = Field(..., pattern="^(video|audio)$")
    quality: str = "best"
    cookies: str = "auto"  # "auto" | "upload" | "browser" | "none"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _validate_url(url: str) -> str:
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    return url


def _build_format_selector(format_type: str, quality: str) -> str:
    if format_type == "audio":
        return "bestaudio/best"
    q = (quality or "best").lower()
    table = {
        "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "1080":  "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720":   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480":   "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360":   "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]",
    }
    return table.get(q, table["best"])


def _postprocessors(format_type: str, quality: str) -> list:
    if format_type == "audio":
        return [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality if quality.isdigit() else "192",
        }]
    return [{
        "key": "FFmpegVideoConvertor",
        "preferedformat": "mp4",
    }]


def _common_extractor_args(cookies_mode: str) -> dict:
    """Build the yt-dlp extractor_args dict.

    `auto`  -> use bgutil HTTP if available
    `none`  -> don't configure any plugin
    """
    if cookies_mode == "none":
        return {}

    args: dict = {}
    if _pot_server_up():
        args["youtubepot-bgutilhttp"] = {"base_url": [POT_BASE_URL]}
    # Always allow the script provider to be picked up too if it exists
    if (BGUTIL_DIR / "build" / "generate_once.js").exists():
        args.setdefault("youtubepot-bgutilscript", {})["server_home"] = [str(BGUTIL_DIR)]
    return args


def _maybe_cookiefile(cookies_mode: str) -> Optional[str]:
    if cookies_mode == "none":
        return None
    if cookies_mode == "browser":
        # default to chrome if present
        for cand in ("chrome", "firefox", "brave", "edge", "chromium", "safari"):
            try:
                # We just return the name; yt-dlp will resolve it.
                # The user must have the browser installed in the same env.
                return cand
            except Exception:
                continue
        return None
    if cookies_mode in ("auto", "upload", "default"):
        if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 0:
            return str(COOKIES_FILE)
    return None


def _yt_dlp_base_opts(url: str, format_type: str, quality: str, cookies_mode: str) -> dict:
    extractor_args = _common_extractor_args(cookies_mode)
    cookiefile = _maybe_cookiefile(cookies_mode)
    opts = {
        "quiet": True,
        "no_warnings": False,
        "skip_download": True,
        "noplaylist": True,
        "format": _build_format_selector(format_type, quality),
        "extractor_args": extractor_args,
        "max_filesize": MAX_FILE_SIZE,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    if _has_node():
        opts["js_runtimes"] = {"node": {}}
        opts["remote_components"] = {"ejs:github"}
    return opts


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "yt_dlp_version": yt_dlp.version.__version__,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "node": _has_node(),
        "pot_server": _pot_server_up(),
        "pot_server_port": POT_PORT if _pot_server_up() else None,
        "cookies_configured": COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 0,
    }


@app.get("/api/info")
def get_info(url: str = Query(..., min_length=1), cookies: str = "auto"):
    url = _validate_url(url)
    cookies_mode = cookies if cookies in ("auto", "upload", "browser", "none") else "auto"

    if "youtube.com" in url or "youtu.be" in url:
        _ensure_pot_server()

    info = None
    last_error = None

    # Estrategia "auto": las cookies de cuenta rompen el PO Token anonimo de
    # bgutil para videos publicos normales, asi que probamos SIN cookies
    # primero. Solo si eso falla por bloqueo real, reintentamos con cookies.
    attempts = [cookies_mode]
    if cookies_mode == "auto":
        attempts = ["none", "auto"]

    for attempt_mode in attempts:
        ydl_opts = _yt_dlp_base_opts(url, "video", "best", attempt_mode)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            last_error = None
            break
        except yt_dlp.utils.DownloadError as e:
            log.warning("extract_info failed (cookies=%s): %s", attempt_mode, e)
            last_error = e
            continue
        except Exception as e:
            log.exception("extract_info unexpected error")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    if last_error is not None and info is None:
        log.exception("extract_info failed on all attempts")
        raise HTTPException(
            status_code=400,
            detail=_friendly_youtube_error(str(last_error)),
        )

    if not info:
        raise HTTPException(status_code=400, detail="No info returned for that URL")

    formats = info.get("formats") or []
    summarized = []
    for f in formats:
        summarized.append({
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "vcodec": (f.get("vcodec") or "none") if f.get("vcodec") != "none" else None,
            "acodec": (f.get("acodec") or "none") if f.get("acodec") != "none" else None,
            "height": f.get("height"),
            "width": f.get("width"),
            "tbr": f.get("tbr"),
            "abr": f.get("abr"),
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "format_note": f.get("format_note"),
        })

    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "channel": info.get("channel"),
        "duration": info.get("duration"),
        "duration_string": info.get("duration_string"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "upload_date": info.get("upload_date"),
        "description": (info.get("description") or "")[:1000],
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "extractor": info.get("extractor"),
        "has_video": any(f.get("height") for f in formats),
        "has_audio": any((f.get("acodec") and f.get("acodec") != "none") for f in formats),
        "format_count": len(formats),
        "formats_sample": summarized[:30],
    }


# ---- Cookies management ----------------------------------------------------

@app.get("/api/cookies/status")
def cookies_status():
    f = COOKIES_FILE
    return {
        "configured": f.exists() and f.stat().st_size > 0,
        "size_bytes": f.stat().st_size if f.exists() else 0,
        "modified": f.stat().st_mtime if f.exists() else None,
    }


@app.post("/api/cookies/upload")
async def cookies_upload(file: UploadFile = File(...)):
    """Accept a Netscape-format cookies.txt and save it for future requests."""
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Cookie file too large (max 10 MB)")

    # Light validation: should look like a Netscape cookies file
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="Cookie file must be text")

    if not re.search(r"^# Netscape HTTP Cookie File", text, re.M) and \
       "youtube.com" not in text.lower() and "google.com" not in text.lower():
        # Not necessarily invalid — just warn
        log.warning("Uploaded cookie file does not look like a Netscape cookies.txt")

    COOKIES_FILE.write_bytes(raw)
    log.info("Saved cookies file: %d bytes", len(raw))
    return {"ok": True, "size_bytes": len(raw)}


@app.post("/api/cookies/clear")
def cookies_clear():
    if COOKIES_FILE.exists():
        COOKIES_FILE.unlink()
    return {"ok": True}


# ---- Download --------------------------------------------------------------

def _schedule_cleanup(path: Path, delay_seconds: float = 30.0) -> None:
    def _job():
        try:
            time.sleep(delay_seconds)
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
    threading.Thread(target=_job, daemon=True).start()


def _friendly_youtube_error(raw: str) -> str:
    """Turn yt-dlp's terse errors into actionable messages for the UI."""
    s = raw or ""
    if "Sign in to confirm" in s or "not a bot" in s:
        return (
            "YouTube blocked this request (anti-bot on datacenter IP / missing cookies). "
            "Fix: go to Settings → upload a cookies.txt exported from a logged-in browser, "
            "then retry. The other 1500+ sites keep working without cookies."
        )
    if "HTTP Error 403" in s:
        return "YouTube returned 403 Forbidden. Try uploading cookies or retrying later."
    if "Video unavailable" in s:
        return "This video is unavailable in your region or has been removed."
    if "Private video" in s:
        return "This video is private."
    return s[:500]


@app.post("/api/download")
def download(req: DownloadRequest):
    url = _validate_url(str(req.url))
    cookies_mode = req.cookies if req.cookies in ("auto", "upload", "browser", "none") else "auto"

    # Lazy start the POT server right before the first YouTube attempt
    if "youtube.com" in url or "youtu.be" in url:
        _ensure_pot_server()

    tmpdir = Path(tempfile.mkdtemp(prefix="ytdl_", dir=DOWNLOAD_DIR))
    try:
        outtmpl = str(tmpdir / "%(title).200B.%(ext)s")

        base_ydl_opts = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": False,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "trim_file_name": 200,
            "format": _build_format_selector(req.format_type, req.quality),
            "postprocessors": _postprocessors(req.format_type, req.quality),
            "merge_output_format": "mp4" if req.format_type == "video" else "mp3",
            "noprogress": True,
            "max_filesize": MAX_FILE_SIZE,
        }
        if _has_node():
            base_ydl_opts["js_runtimes"] = {"node": {}}
            base_ydl_opts["remote_components"] = {"ejs:github"}

        # Igual que en /api/info: las cookies de cuenta rompen el PO Token
        # anonimo para videos publicos normales, asi que en modo "auto"
        # probamos primero SIN cookies y solo caemos a cookies si hace falta.
        attempts = [cookies_mode]
        if cookies_mode == "auto":
            attempts = ["none", "auto"]

        info = None
        last_error = None
        for attempt_mode in attempts:
            ydl_opts = dict(base_ydl_opts)
            ydl_opts["extractor_args"] = _common_extractor_args(attempt_mode)
            cookiefile = _maybe_cookiefile(attempt_mode)
            if cookiefile:
                ydl_opts["cookiefile"] = cookiefile

            log.info("Starting download: url=%s type=%s quality=%s cookies=%s",
                     url, req.format_type, req.quality, attempt_mode)
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                last_error = None
                break
            except yt_dlp.utils.DownloadError as e:
                log.warning("download failed (cookies=%s): %s", attempt_mode, e)
                last_error = e
                continue
            except Exception as e:
                log.exception("download unexpected error")
                raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

        if last_error is not None and info is None:
            log.exception("download failed on all attempts")
            raise HTTPException(status_code=400, detail=_friendly_youtube_error(str(last_error)))

        if not info:
            raise HTTPException(status_code=500, detail="No info returned after download")

        produced = None
        requested = info.get("requested_downloads") or []
        if requested and requested[0].get("filepath"):
            produced = Path(requested[0]["filepath"])
        if not produced or not produced.exists():
            files = sorted(
                (p for p in tmpdir.iterdir() if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not files:
                raise HTTPException(status_code=500, detail="Download finished but no file was produced")
            produced = files[0]
        if not produced.exists():
            raise HTTPException(status_code=500, detail="Produced file not found on disk")

        ext = produced.suffix.lstrip(".").lower() or ("mp4" if req.format_type == "video" else "mp3")
        media_type = "audio/mpeg" if ext == "mp3" else f"video/{ext if ext.startswith('mp4') else 'mp4'}"

        raw_title = info.get("title") or "download"
        safe = re.sub(r"[^\w\-\. ]+", "_", raw_title).strip()[:120] or "download"
        filename = f"{safe}.{ext}"

        log.info("Serving file: %s (%s bytes)", produced, produced.stat().st_size)

        _schedule_cleanup(produced, delay_seconds=30.0)
        _schedule_cleanup(tmpdir, delay_seconds=35.0)

        return FileResponse(
            path=str(produced),
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Title": raw_title[:200],
                "X-Duration": str(info.get("duration") or 0),
                "X-Extractor": info.get("extractor", ""),
            },
        )
    except HTTPException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


# ----------------------------------------------------------------------------
# Static frontend
# ----------------------------------------------------------------------------

FRONTEND_DIR = (BASE_DIR.parent / "frontend").resolve()
if FRONTEND_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)
