#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$ROOT/src/core/rs/mc-core"
OUT_DIR="$ROOT/src/core/GUI/py/mc_core"

cd "$CORE_DIR"
export PYO3_PYTHON="${PYO3_PYTHON:-python3}"
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
cargo build --release --features python

LIB="$(find target/release -maxdepth 1 -name '_mc_core.dll' -o -name '_mc_core.so' | head -n1)"
DEST="$OUT_DIR/_mc_core.so"
if [[ "$LIB" == *.dll ]]; then
  DEST="$OUT_DIR/_mc_core.pyd"
fi
cp "$LIB" "$DEST"
echo "Copied $LIB -> $DEST"
