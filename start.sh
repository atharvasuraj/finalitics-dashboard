#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Create .venv and install requirements.txt first; see QUICKSTART.md.' >&2
  exit 1
fi
exec .venv/bin/python app.py
