import json
import re
from pathlib import Path

# ---------- Konfiguration ----------
INPUT_FILE = "/home/kai/dev/mineru-fork-2/data/downloaded_arbeitsrecht/merged_content_list.json"
OUTPUT_FILE = "/home/kai/dev/mineru-fork-2/data/downloaded_arbeitsrecht/merged_content_list.json"

# Regex:
# - ein oder zwei Pipes
# - optional Leerzeichen
# - eine Zahl
FOOTNOTE_PATTERN = re.compile(r"\|{1,2}\s*\d+")


def process_entry(entry: dict) -> dict:
    """
    Prüft einen einzelnen JSON-Eintrag und passt ggf. den type an.
    """
    text = entry.get("text")
    if not isinstance(text, str):
        return entry  # kein Text → nichts tun

    matches = FOOTNOTE_PATTERN.findall(text)

    if len(matches) > 3:
        entry["type"] = "page_footnote"

    return entry


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Fall 1: Liste von Einträgen
    if isinstance(data, list):
        data = [process_entry(entry) if isinstance(entry, dict) else entry for entry in data]

    # Fall 2: einzelnes Objekt
    elif isinstance(data, dict):
        data = process_entry(data)

    else:
        raise ValueError("Unerwartete JSON-Struktur")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()