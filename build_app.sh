#!/usr/bin/env bash
set -euo pipefail

# ── Build MUTABAR.app ────────────────────────────────────
# Creates a standalone macOS .app bundle via PyInstaller.
# Output: dist/MUTABAR.zip (send this to anyone)
# ─────────────────────────────────────────────────────────

cd "$(dirname "$0")"

echo "==> Activating venv..."
source venv/bin/activate

echo "==> Installing build deps..."
pip install pyinstaller Pillow -q

echo "==> Cleaning previous build..."
rm -rf build dist

echo "==> Building MUTABAR.app..."
pyinstaller mutabar.spec --noconfirm 2>&1 | tail -5

if [[ -d "dist/MUTABAR.app" ]]; then
    # Remove the intermediate collect folder — only keep the .app
    rm -rf dist/mutabar

    echo "==> Zipping..."
    cd dist
    rm -f MUTABAR.zip
    zip -r -q MUTABAR.zip MUTABAR.app
    SIZE=$(du -sh MUTABAR.zip | cut -f1)
    echo ""
    echo "=============================="
    echo "  MUTABAR.app built!"
    echo "  dist/MUTABAR.zip ($SIZE)"
    echo "=============================="
    echo ""
    echo "Send MUTABAR.zip to anyone with a Mac."
    echo "They just unzip and double-click."
else
    echo "Build failed. Check output above."
    exit 1
fi
