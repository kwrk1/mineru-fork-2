#!/usr/bin/env bash

set -e

REMOTE_USER="kai"
REMOTE_HOST="34.34.17.77"

REMOTE_INPUT_DIR="/home/k_werk/mineru-fork-2/data/input"
LOCAL_INPUT_DIR="./input_pdfs"

echo "📤 Lade alle PDFs aus $LOCAL_INPUT_DIR"
echo "   → Ziel: $REMOTE_INPUT_DIR"

if [ ! -d "$LOCAL_INPUT_DIR" ]; then
  echo "❌ Lokaler Ordner existiert nicht: $LOCAL_INPUT_DIR"
  exit 1
fi

rsync -avz \
  --include="*/" \
  --include="*.pdf" \
  --exclude="*" \
  "$LOCAL_INPUT_DIR/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_INPUT_DIR/"

echo "✅ Upload abgeschlossen."