#!/usr/bin/env bash

set -e

REMOTE_USER="kai"
REMOTE_HOST="34.6.17.211"
REMOTE_BASE="/home/k_werk/mineru-fork-2/data/output"

LOCAL_BASE="./downloaded_outputs"

mkdir -p "$LOCAL_BASE"

echo "📥 Lade alle Outputs aus $REMOTE_BASE"
echo "   → nur .md, *_content_list.json, *_content_list_v2.json"

rsync -avz \
  --prune-empty-dirs \
  --include="*/" \
  --include="*.md" \
  --include="*_content_list.json" \
  --include="*_content_list_v2.json" \
  --exclude="*" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE/" \
  "$LOCAL_BASE/"

echo "✅ Fertig."