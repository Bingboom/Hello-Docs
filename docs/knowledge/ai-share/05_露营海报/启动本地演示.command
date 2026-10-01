#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PATH="/Library/TeX/texbin:/opt/homebrew/bin:$PATH"
python3 demo.py serve --port 8765
