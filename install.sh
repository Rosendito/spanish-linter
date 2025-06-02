#!/bin/bash
set -e

echo "🛠 Installing spanish-linter..."

INSTALL_DIR="$HOME/spanish_linter"

if ! command -v python3 >/dev/null; then
  echo "🔧 Installing Python via Homebrew..."
  brew install python
fi

if ! command -v pipx >/dev/null; then
  echo "🔧 Installing pipx via Homebrew..."
  brew install pipx
  pipx ensurepath
fi

# Remove existing installation to ensure clean install
if [ -d "$INSTALL_DIR" ]; then
  echo "🗑 Removing existing installation..."
  rm -rf "$INSTALL_DIR"
fi

echo "📦 Cloning repository into $INSTALL_DIR..."
git clone . "$INSTALL_DIR"

# Fix directory structure if needed
if [ -d "$INSTALL_DIR/spanish-linter" ] && [ ! -d "$INSTALL_DIR/spanish_linter" ]; then
  echo "🔧 Fixing directory structure..."
  mv "$INSTALL_DIR/spanish-linter" "$INSTALL_DIR/spanish_linter"
fi

echo "🐍 Installing with pipx from $INSTALL_DIR..."
pipx install --force "$INSTALL_DIR"

echo "🧠 Downloading fastText model..."
MODEL_DIR="$HOME/.models/fasttext"
MODEL_PATH="$MODEL_DIR/lid.176.bin"
MODEL_URL="https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"

mkdir -p "$MODEL_DIR"
if [ ! -f "$MODEL_PATH" ]; then
  echo "⬇️  Downloading model to $MODEL_PATH..."
  curl -L "$MODEL_URL" -o "$MODEL_PATH"
  echo "✅ Model downloaded successfully"
else
  echo "ℹ️  Model already exists at $MODEL_PATH"
fi

echo "✅ spanish-linter installed. Run:"
echo ""
echo "   spanish-linter --help"
echo ""
