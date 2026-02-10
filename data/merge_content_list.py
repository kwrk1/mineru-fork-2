import json
import os
import re
from pathlib import Path

INPUT_FILE_NAME = "Arbeitsrecht_Kommentar"
BASE_DIR = Path(__file__).parent / "downloaded_arbeitsrecht"
OUTPUT_JSON = BASE_DIR / "merged_content_list.json"
OUTPUT_JSONL = BASE_DIR / "merged_content_list.jsonl"
CONTENT_LIST_FILE = f"{INPUT_FILE_NAME}_content_list.json"

merged = []

# z.B. output_bgb_pages_500_1000 -> 500
folder_re = re.compile(r".*?(\d+)_\d+$")

for folder_name in sorted(os.listdir(BASE_DIR)):
    folder_path = os.path.join(BASE_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    match = folder_re.match(folder_name)
    if not match:
        print(f"Übersprungen (kein Seitenbereich): {folder_name}")
        continue

    page_offset = int(match.group(1))

    json_path = os.path.join(folder_path, CONTENT_LIST_FILE)
    if not os.path.isfile(json_path):
        print(f"Keine JSON gefunden in: {folder_name}")
        continue

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        #Die letzte Seite einer Batch ist immer == der nullten Seite des nächsten Batches.
        if item["page_idx"] == 0:
            continue

        if "page_idx" in item:
            item["page_idx"] += page_offset
        else:
            print(f"Warnung: kein page_idx in {folder_name}")
        if item["page_idx"] == 0:
            continue
        merged.append(item)

# -------- JSON --------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

# -------- JSONL --------
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for item in merged:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")



print("Fertig!")
print(f"- JSON:  {OUTPUT_JSON}")
print(f"- JSONL: {OUTPUT_JSONL}")
print(f"- Einträge: {len(merged)}")
