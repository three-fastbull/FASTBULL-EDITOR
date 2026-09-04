#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
project_dir="$(cd -- "$script_dir/.." && pwd -P)"
cd "$project_dir"

command -v python3 >/dev/null || { echo "Python 3.10+ is required"; exit 1; }
command -v node >/dev/null || { echo "Node.js 22+ is required"; exit 1; }
command -v ffmpeg >/dev/null || { echo "FFmpeg is required"; exit 1; }

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-fastbull.txt
.venv/bin/python scripts/download_whisper_model.py --model small

npm --prefix remotion-composer ci
bash scripts/setup_hyperframes_local.sh

.venv/bin/python scripts/fastbull_editor.py doctor
echo "FASTBULL Editor is ready. API cost: 0 baht."
