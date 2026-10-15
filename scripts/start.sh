#!/usr/bin/env bash
# One command on macOS, Linux, or Git Bash: ./scripts/start.sh [--check] [--no-public-data]
#   --check           install dependencies and run the test suite instead of the server
#   --no-public-data  skip the ~16 MB Kenya OCDS download (award history then reports SOURCE_UNAVAILABLE)
# A local model is optional: install Ollama yourself, pull a model, then export
# TENDER_LOCAL_MODEL_URL=http://127.0.0.1:11434 and enter the model tag in the workbench.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v uv >/dev/null || { echo "Install uv from https://docs.astral.sh/uv/getting-started/installation/ and rerun."; exit 1; }
command -v node >/dev/null || { echo "Install Node.js LTS from https://nodejs.org/ and rerun."; exit 1; }

check=0
public_data=1
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    --no-public-data) public_data=0 ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

uv sync --frozen
if [ ! -f node_modules/@modelcontextprotocol/server-filesystem/dist/index.js ]; then
  npm ci --no-audit --no-fund
fi

if [ "$check" = 1 ]; then
  exec uv run --frozen python -m pytest -q
fi

if [ "$public_data" = 1 ] && [ ! -f local_data/ocds/kenya-ppra.sqlite ]; then
  uv run --frozen python -m scripts.fetch_ocds \
    || echo "Public award data could not be downloaded; award history will show SOURCE_UNAVAILABLE."
fi

echo "Starting workbench at http://127.0.0.1:8000. Press Ctrl+C to stop."
exec uv run --frozen python -m uvicorn app.server:app --host 127.0.0.1 --port 8000
