#!/bin/bash
set -e

echo "🧹 Uninstalling spanish-linter..."

PACKAGE_NAME="spanish-linter"
INSTALL_DIR="$HOME/.local/$PACKAGE_NAME"
MODEL_PATH="$HOME/.cache/fasttext/lid.176.bin"

# Uninstall from pipx if installed
if command -v pipx >/dev/null; then
  if pipx list | grep -q "$PACKAGE_NAME"; then
    echo "🔧 Removing pipx package..."
    pipx uninstall "$PACKAGE_NAME"
  else
    echo "ℹ️  Package not found in pipx. Skipping pipx uninstall."
  fi
else
  echo "⚠️  pipx not found. Please uninstall manually if needed."
fi

# Remove local clone
if [ -d "$INSTALL_DIR" ]; then
  echo "🗑 Removing local directory: $INSTALL_DIR"
  rm -rf "$INSTALL_DIR"
else
  echo "ℹ️  No local directory found at $INSTALL_DIR"
fi

# Ask if user wants to delete the fasttext model
if [ -f "$MODEL_PATH" ]; then
  read -p "🧠 Delete fasttext model at $MODEL_PATH? [y/N]: " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    rm -f "$MODEL_PATH"
    echo "✅ Model deleted."
  else
    echo "ℹ️  Model kept."
  fi
fi

echo "✅ spanish-linter has been fully uninstalled."
