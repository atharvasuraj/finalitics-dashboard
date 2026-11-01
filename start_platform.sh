#!/usr/bin/env bash
# Compatibility entry point: the supported demo now uses Flask only.
set -euo pipefail
cd "$(dirname "$0")"
exec ./start.sh
