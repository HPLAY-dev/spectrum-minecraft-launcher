#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="$ROOT/config/version.json"
HEADER_FILE="$ROOT/src/common/include/mc/common/version.generated.hpp"
BUILD_ID="${SERENA_BUILD_ID:-0}"

if commit="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)"; then
  :
else
  commit="dev"
fi

cat >"$VERSION_FILE" <<EOF
{
  "name": "SerenaLauncher",
  "codename": "Okra",
  "major": 26,
  "quarter": "Q2",
  "build_id": "$BUILD_ID",
  "commit": "$commit"
}
EOF

full="26Q2.${BUILD_ID}.${commit}"
cat >"$HEADER_FILE" <<EOF
#pragma once

#define SERENA_APP_NAME "SerenaLauncher"
#define SERENA_CODENAME "Okra"
#define SERENA_MAJOR_VERSION 26
#define SERENA_QUARTER "Q2"
#define SERENA_BUILD_ID "$BUILD_ID"
#define SERENA_COMMIT "$commit"
#define SERENA_VERSION_STRING "$full"
EOF

echo "SerenaLauncher $full (Okra)"
