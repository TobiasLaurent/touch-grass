#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/release_touch_grass.sh 0.2.2
#
# What it does:
# 1) Ensures working tree is clean and on main
# 2) Pulls latest main
# 3) Computes tarball sha256 for current HEAD
# 4) Updates Formula/touch-grass.rb version/url/sha256
# 5) Commits changes

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version>"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit/stash first."
  exit 1
fi

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "main" ]]; then
  echo "Please run from main branch (current: $current_branch)."
  exit 1
fi

git pull --ff-only

SHA="$(git rev-parse HEAD)"
TARBALL="/tmp/touch-grass-${SHA}.tar.gz"
URL="https://github.com/TobiasLaurent/touch-grass/archive/${SHA}.tar.gz"

curl -L -s "$URL" -o "$TARBALL"
SHA256="$(sha256sum "$TARBALL" | awk '{print $1}')"

SHA="$SHA" VERSION="$VERSION" SHA256="$SHA256" python3 - <<'PY'
from pathlib import Path
import os
import re

sha = os.environ['SHA']
version = os.environ['VERSION']
sha256 = os.environ['SHA256']

p = Path('Formula/touch-grass.rb')
s = p.read_text()

s = re.sub(r'url\s+"https://github.com/TobiasLaurent/touch-grass/archive/[a-f0-9]+\.tar\.gz"',
           f'url "https://github.com/TobiasLaurent/touch-grass/archive/{sha}.tar.gz"', s)
s = re.sub(r'version\s+"[0-9]+\.[0-9]+\.[0-9]+"',
           f'version "{version}"', s)
s = re.sub(r'sha256\s+"[a-f0-9]{64}"',
           f'sha256 "{sha256}"', s)

p.write_text(s)
PY

git add Formula/touch-grass.rb
git commit -m "Release ${VERSION}: update Homebrew formula"

echo "Done."
echo "- Version: ${VERSION}"
echo "- Commit SHA: ${SHA}"
echo "- Tarball SHA256: ${SHA256}"
echo
echo "Next: git push && open PR (or merge directly per your workflow)."
