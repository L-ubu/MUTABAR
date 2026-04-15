#!/usr/bin/env bash
set -euo pipefail

# ── MUTABAR Installer ─────────────────────────────────────
# macOS menu bar monster battler with AI narration
# Usage: curl -fsSL <raw-url>/install.sh | bash
# Or:    git clone ... && cd mutabar && ./install.sh
# ──────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[*]${NC} $1"; }
ok()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
fail()  { echo -e "${RED}[x]${NC} $1"; exit 1; }

# ── Check macOS ───────────────────────────────────────────
[[ "$(uname)" == "Darwin" ]] || fail "MUTABAR only runs on macOS."

# ── Check Python 3.11+ ───────────────────────────────────
if ! command -v python3 &>/dev/null; then
    fail "Python 3 not found. Install from https://python.org or: brew install python@3.12"
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ]]; then
    fail "Python 3.11+ required (found $PY_VER). Install from https://python.org or: brew install python@3.12"
fi
ok "Python $PY_VER"

# ── Find project root ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
    PROJECT_DIR="$SCRIPT_DIR"
else
    fail "Run this script from the mutabar project directory."
fi

cd "$PROJECT_DIR"
info "Installing from $PROJECT_DIR"

# ── Create venv ───────────────────────────────────────────
if [[ ! -d "venv" ]]; then
    info "Creating virtual environment..."
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment exists"
fi

source venv/bin/activate

# ── Install package ───────────────────────────────────────
info "Installing MUTABAR..."
pip install --upgrade pip -q
pip install -e ".[ai]" -q 2>&1 | tail -1
ok "MUTABAR installed"

# ── Model download (optional) ────────────────────────────
MODEL_PATH="$PROJECT_DIR/models/Qwen3-1.7B.Q8_0.gguf"
if [[ -f "$MODEL_PATH" ]]; then
    ok "AI model already present"
else
    echo ""
    warn "AI model not found (~2 GB download)."
    warn "The model enables AI-narrated battles. Without it, battles use template text."
    echo ""
    read -rp "Download AI model now? [y/N] " dl_choice
    if [[ "$dl_choice" =~ ^[Yy]$ ]]; then
        info "Downloading model (this may take a few minutes)..."
        mkdir -p "$PROJECT_DIR/models"
        if curl -L --progress-bar \
            "https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q8_0.gguf" \
            -o "$MODEL_PATH.tmp"; then
            mv "$MODEL_PATH.tmp" "$MODEL_PATH"
            ok "AI model downloaded"
        else
            warn "Download failed. You can retry later — the game will auto-download on launch."
            rm -f "$MODEL_PATH.tmp"
        fi
    else
        info "Skipping model download. The game will auto-download on first launch."
    fi
fi

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  MUTABAR installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  To run:"
echo -e "    ${CYAN}cd $PROJECT_DIR${NC}"
echo -e "    ${CYAN}source venv/bin/activate${NC}"
echo -e "    ${CYAN}mutabar${NC}"
echo ""
echo "  Or directly:"
echo -e "    ${CYAN}$PROJECT_DIR/venv/bin/mutabar${NC}"
echo ""
