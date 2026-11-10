#!/usr/bin/env bash
# Install the TripoSR route (Route B). Run from anywhere:  bash scripts/setup_triposr.sh
# TripoSR is not on PyPI, so it is cloned into backend/third_party/TripoSR.
# torchmcubes compiles native code: this works on Linux / Google Colab; on Windows it needs MSVC + CUDA toolkit.
set -e
BACKEND="$(cd "$(dirname "$0")/../backend" && pwd)"
mkdir -p "$BACKEND/third_party"
[ -d "$BACKEND/third_party/TripoSR" ] || git clone https://github.com/VAST-AI-Research/TripoSR "$BACKEND/third_party/TripoSR"
pip install -r "$BACKEND/requirements-triposr.txt"
pip install git+https://github.com/tatsy/torchmcubes.git
echo "TripoSR cloned to $BACKEND/third_party/TripoSR"
