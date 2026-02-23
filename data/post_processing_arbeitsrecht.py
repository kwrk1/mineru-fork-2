import json
import re
from pathlib import Path

# ---------- Konfiguration ----------
PROJECT_NAME = "downloaded_arbeitsrecht_zuschnitt_2"
INPUT_FILE = Path(__file__).parent / PROJECT_NAME / "merged_content_list.json"
OUTPUT_FILE = Path(__file__).parent / PROJECT_NAME / "merged_content_list.json"
FOOTNOTE_PATTERN = re.compile(r"\|{1,2}\s*\d+")

def process_entry(entry: dict) -> tuple[dict, bool]:
    """
    Prüft einen einzelnen JSON-Eintrag.
    Gibt (entry, True) zurück, wenn type geändert wurde.
    """
    text = entry.get("text")
    if not isinstance(text, str):
        return entry, False

    matches = FOOTNOTE_PATTERN.findall(text)

    if len(matches) > 3:
        entry["type"] = "page_footnote"
        return entry, True

    return entry, False


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    counter = 0

    if isinstance(data, list):
        new_data = []
        for entry in data:
            if isinstance(entry, dict):
                entry, changed = process_entry(entry)
                if changed:
                    counter += 1
            new_data.append(entry)
        data = new_data

    elif isinstance(data, dict):
        data, changed = process_entry(data)
        if changed:
            counter += 1

    else:
        raise ValueError("Unerwartete JSON-Struktur")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"{counter} Einträge wurden als 'page_footnote' markiert.")


if __name__ == "__main__":
    main()