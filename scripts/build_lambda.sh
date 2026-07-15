#!/usr/bin/env bash
# SPDX-License-Identifier: MIT-0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build"
STAGE="$BUILD/lambda"
ZIP="$BUILD/finding-processor.zip"

rm -rf "$STAGE" "$ZIP"
mkdir -p "$STAGE"
python3.13 -m pip install \
  --requirement "$ROOT/requirements.txt" \
  --target "$STAGE" \
  --platform manylinux2014_aarch64 \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all: \
  --no-compile \
  --disable-pip-version-check
cp -R "$ROOT/src/finding_processor" "$STAGE/finding_processor"
mkdir -p "$STAGE/config"
cp "$ROOT/config/triage-policy.json" "$STAGE/config/triage-policy.json"
find "$STAGE" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$STAGE" -type f -name '*.pyc' -delete
find "$STAGE" -exec touch -t 202601010000 {} +
(
  cd "$STAGE"
  find . -type f -print | LC_ALL=C sort | zip -X -q "$ZIP" -@
)
shasum -a 256 "$ZIP" | tee "$ZIP.sha256"

