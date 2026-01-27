import os
import re

BASE_DIR = "/home/kai/dev/mineru-fork-2/data/downloaded_bgb"
OUTPUT_MD = "BGB-Erman_merged.md"

# z.B. output_bgb_pages_500_1000 -> 500
folder_re = re.compile(r".*?(\d+)_\d+$")

# Ordner mit Seitenstart sammeln
folders = []

for folder_name in os.listdir(BASE_DIR):
    folder_path = os.path.join(BASE_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    match = folder_re.match(folder_name)
    if not match:
        continue

    page_start = int(match.group(1))
    md_path = os.path.join(folder_path, "BGB-Erman.md")

    if os.path.isfile(md_path):
        folders.append((page_start, folder_name, md_path))

# Nach Seitenstart sortieren
folders.sort(key=lambda x: x[0])

with open(OUTPUT_MD, "w", encoding="utf-8") as out:
    for page_start, folder_name, md_path in folders:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Optionaler Trenner
        out.write(f"\n\n<!-- BEGIN {folder_name} (ab Seite {page_start}) -->\n\n")
        out.write(content)
        out.write(f"\n\n<!-- END {folder_name} -->\n")

print(f"Fertig! Markdown gemerged in: {OUTPUT_MD}")