#!/bin/bash
set -e

echo "🛠 Installing spanish-linter..."

INSTALL_DIR="$HOME/.local/spanish-linter"
VENV_DIR="$INSTALL_DIR/venv"
BIN_NAME="spanish-linter"

if ! command -v python3 >/dev/null; then
  echo "🔧 Installing Python via Homebrew..."
  brew install python
fi

if ! command -v pipx >/dev/null; then
  echo "🔧 Installing pipx via Homebrew..."
  brew install pipx
  pipx ensurepath
fi

if [ ! -d "$INSTALL_DIR" ]; then
  echo "📦 Cloning repository into $INSTALL_DIR..."
  git clone . "$INSTALL_DIR"
else
  echo "📁 Updating existing $INSTALL_DIR..."
  cd "$INSTALL_DIR" && git pull
fi

echo "🐍 Installing isolated environment with pipx..."
pipx install --force --editable "$INSTALL_DIR" --pip-args "--requirement=$INSTALL_DIR/requirements.txt"

echo "✅ spanish-linter installed. Run:"
echo ""
echo "   spanish-linter --help"
echo ""
