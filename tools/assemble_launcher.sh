#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${1:?}"
STAMP="${2:?}"
PYD="${3:?}"
ROOT="$(pwd)"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
for item in python app assets languages themes qml web fonts; do
  if [[ -d "$ROOT/$item" ]]; then
    cp -a "$ROOT/$item" "$OUT_DIR/$item"
  fi
done
cp "$ROOT"/*.py "$OUT_DIR/" 2>/dev/null || true
mkdir -p "$OUT_DIR/python/spectrum_core"
find "$OUT_DIR/python/spectrum_core" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
cp "$PYD" "$OUT_DIR/python/spectrum_core/_spectrum_core.pyd"
date -Iseconds > "$STAMP"
echo "Assembled launcher -> $OUT_DIR"
