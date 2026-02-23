#!/usr/bin/env bash

set -e

REMOTE_USER="kai"
REMOTE_HOST="34.6.17.211"
REMOTE_BASE="/home/k_werk/mineru-fork-2/data"
REMOTE_INPUT_FILE_NAME="Arbeitsrecht_Kommentar_Zuschnitt_3"
REMOTE_MINERU_MODE_NAME="hybrid_txt"

LOCAL_BASE="./downloaded_arbeitsrecht_zuschnitt_3"

FOLDERS=()

START=0
END=3455
STEP=500

for ((i=START; i<END; i+=STEP)); do
  j=$((i + STEP))
  if (( j > END )); then
    j=$END
  fi
  FOLDERS+=("output_arbeitsrecht_3_pages_${i}_${j}")
done

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