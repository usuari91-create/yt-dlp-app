#!/usr/bin/env bash
# Start the YT-DLP web app (v2).
#
# - Installs Python deps if missing
# - Clones + builds the bgutil POT server if missing
# - Starts the POT server in the background (auto-started by the backend too)
# - Starts the FastAPI backend in the foreground
set -e

cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

# ----- ffmpeg -----
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[!] ffmpeg is required for audio/video conversion."
  echo "    Install it with: sudo apt-get install ffmpeg   (Debian/Ubuntu)"
  echo "                     brew install ffmpeg           (macOS)"
  exit 1
fi

# ----- Python deps -----
if ! "$PY" -c "import yt_dlp, fastapi, uvicorn, httpx" 2>/dev/null; then
  echo "[*] Installing Python dependencies..."
  "$PY" -m pip install --break-system-packages -r backend/requirements.txt
fi

# ----- bgutil POT server (cloned + built once) -----
BGUTIL_DIR="${BGUTIL_DIR:-/opt/bgutil-provider/server}"
BGUTIL_REPO="https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git"
BGUTIL_BRANCH="${BGUTIL_BRANCH:-1.3.1}"

if [ ! -d "$BGUTIL_DIR" ]; then
  if command -v git >/dev/null 2>&1; then
    echo "[*] Cloning bgutil POT provider into $BGUTIL_DIR"
    sudo mkdir -p "$(dirname "$BGUTIL_DIR")"
    sudo git clone --single-branch --branch "$BGUTIL_BRANCH" --depth 1 \
      "$BGUTIL_REPO" "$(dirname "$BGUTIL_DIR")/bgutil-provider"
  else
    echo "[!] git is required to fetch the bgutil POT provider. Install git or pre-populate $BGUTIL_DIR"
    exit 1
  fi
fi

if [ -d "$BGUTIL_DIR" ] && [ ! -f "$BGUTIL_DIR/build/main.js" ]; then
  echo "[*] Building bgutil POT server..."
  (cd "$BGUTIL_DIR" && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund) && npx tsc)
fi

# Export the path so the backend picks it up
export BGUTIL_DIR

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "[*] Starting YT-DLP web app on http://$HOST:$PORT"
cd backend
exec "$PY" -m uvicorn main:app --host "$HOST" --port "$PORT"
