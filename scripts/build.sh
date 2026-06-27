#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_TYPE="${1:-Release}"

"$ROOT/scripts/gen_version.sh"

echo "==> Building C++ core"
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
cmake --build "$ROOT/build" -j"$(nproc)"

echo "==> Building Rust core"
"$ROOT/scripts/cargo_build.sh"

echo "Done."
