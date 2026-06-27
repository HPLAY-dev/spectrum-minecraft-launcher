#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:?usage: cargo_build.sh <output.pyd>}"
cd "$ROOT/spectrum-core"
export PYO3_PYTHON="${PYO3_PYTHON:-$(command -v python3 || command -v python)}"
cargo build --release --features python
for name in spectrum_core.so _spectrum_core.so _spectrum_core.dylib libspectrum_core.so; do
  if [[ -f "target/release/$name" ]]; then
    cp "target/release/$name" "$OUT"
    exit 0
  fi
done
echo "Build output not found in target/release" >&2
exit 1
