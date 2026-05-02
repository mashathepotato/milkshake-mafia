#!/usr/bin/env bash
# Start the full Milkshake Mafia stack: FastAPI taste bridge + Barista (Vite).
#
# First run bootstraps anything missing (Python venv, deps, Playwright Chromium,
# Node modules, baseline embeddings). Subsequent runs skip straight to launch.
#
# Usage: ./scripts/dev.sh [--rebuild-baseline]
#
# Stops both servers cleanly on Ctrl+C.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv"
BARISTA="$ROOT/barista"
EMB_META="$ROOT/baselines/embeddings/baseline_meta.json"
SERVICE_PORT="${SERVICE_PORT:-8000}"
REBUILD_BASELINE=0

for arg in "$@"; do
  case "$arg" in
    --rebuild-baseline) REBUILD_BASELINE=1 ;;
    -h|--help)
      sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

note() { printf '\033[1;36m[dev]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[dev]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[dev]\033[0m %s\n' "$*" >&2; exit 1; }

# ---- prerequisites ---------------------------------------------------------

command -v python3 >/dev/null || die "python3 not found. Install Python 3.11+."
command -v node >/dev/null || die "node not found. Install Node 18+ (https://nodejs.org)."
command -v npm >/dev/null || die "npm not found (ships with Node)."

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_OK="$(python3 -c 'import sys; print(int(sys.version_info >= (3,11)))')"
[ "$PY_OK" = "1" ] || die "Python $PY_VERSION found, need >= 3.11."

# ---- python venv + deps ---------------------------------------------------

if [ ! -d "$VENV" ]; then
  note "Creating virtualenv at .venv (one-time)…"
  if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.11
  else
    python3 -m venv "$VENV"
  fi
fi

PY="$VENV/bin/python"
PIP_INSTALL="$PY -m pip install"
if command -v uv >/dev/null 2>&1; then
  PIP_INSTALL="uv pip install"
fi

# Probe for the heavy/optional bits (torch, fastapi, playwright). If any are
# missing, do a single editable install with both extras and python-multipart.
if ! "$PY" -c "import fastapi, playwright, torch, transformers" 2>/dev/null; then
  note "Installing Python deps (one-time, ~700 MB incl. torch + transformers)…"
  $PIP_INSTALL -e ".[service,dinov2]" python-multipart
fi

# Playwright browser binary (separate from the pip package).
if ! "$PY" -c "import playwright; from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.executable_path" 2>/dev/null | grep -q "/"; then
  note "Installing Playwright Chromium (one-time, ~92 MB)…"
  "$PY" -m playwright install chromium
fi

# ---- baseline embeddings --------------------------------------------------

if [ ! -f "$EMB_META" ] || [ "$REBUILD_BASELINE" = "1" ]; then
  note "Building cellar baseline embeddings (this can take a few minutes — captures 12 URLs with Playwright + DINOv2)…"
  "$PY" -m photographer baseline build --embedder dinov2
fi

# ---- node deps ------------------------------------------------------------

if [ ! -d "$BARISTA/node_modules" ]; then
  note "Installing Barista node_modules (one-time)…"
  npm --prefix "$BARISTA" install
fi

# ---- launch ---------------------------------------------------------------

UVICORN_LOG="$ROOT/.dev-uvicorn.log"
note "Starting taste bridge on http://localhost:$SERVICE_PORT (logs → .dev-uvicorn.log)…"
"$PY" -m uvicorn service.main:app --port "$SERVICE_PORT" --log-level warning > "$UVICORN_LOG" 2>&1 &
SERVICE_PID=$!

cleanup() {
  echo
  note "Stopping taste bridge (pid $SERVICE_PID)…"
  kill "$SERVICE_PID" 2>/dev/null || true
  wait "$SERVICE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for /health before starting Vite, so the first taste isn't a race.
note "Waiting for taste bridge to warm up (DINOv2 takes a few seconds)…"
for _ in $(seq 1 60); do
  if curl -sSf "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1; then
    note "Taste bridge ready."
    break
  fi
  sleep 1
done

note "Starting Barista on Vite (default http://localhost:5173, will hop ports if taken)…"
note "Ctrl+C to stop both."
npm --prefix "$BARISTA" run dev
