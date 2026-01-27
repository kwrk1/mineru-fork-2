#!/usr/bin/env bash

set -e

REMOTE_USER="kai"
REMOTE_HOST="35.242.233.184"
REMOTE_BASE="/home/k_werk/mineru-fork-2/data"
REMOTE_INPUT_FILE_NAME="bgh"
REMOTE_MINERU_MODE_NAME="hybrid_auto"

LOCAL_BASE="./downloaded_bgh"

FOLDERS=(
  output_bgh_pages_0_5
)

FILES=(
  "${REMOTE_INPUT_FILE_NAME}.md"
  "${REMOTE_INPUT_FILE_NAME}_content_list.json"
  "${REMOTE_INPUT_FILE_NAME}_content_list_v2.json"
)

mkdir -p "$LOCAL_BASE"

for folder in "${FOLDERS[@]}"; do
  REMOTE_PATH="$REMOTE_BASE/$folder/$REMOTE_INPUT_FILE_NAME/$REMOTE_MINERU_MODE_NAME"
  LOCAL_PATH="$LOCAL_BASE/$folder"

  echo "📥 Lade aus $REMOTE_PATH"
  mkdir -p "$LOCAL_PATH"

  for file in "${FILES[@]}"; do
    scp \
      "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file" \
      "$LOCAL_PATH/" || echo "⚠️  Datei fehlt: $REMOTE_PATH/$file"
  done
done

echo "✅ Fertig."