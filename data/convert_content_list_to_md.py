"""
JSON/JSONL to Markdown Converter
Converts JSON or JSONL data with text and list elements into Markdown.
Sorts by page_idx and vertical position (bbox[1]).
"""

import re
import json
from pathlib import Path


def load_data(filepath):
    """
    Loads data from JSON or JSONL.
    JSONL is merged into one large array.
    """
    if filepath.suffix.lower() == ".jsonl":
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Error in JSONL line {line_number}: {e}"
                    )
        return data

    elif filepath.suffix.lower() == ".json":
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    else:
        raise ValueError("Only .json or .jsonl files are supported.")

def clean_text(text: str) -> str:
    """
    Entfernt:
    - führende/trailing Spaces
    - führende/trailing Newlines
    - interne Newlines
    - doppelte Leerzeichen
    """
    if not text:
        return ""

    
    text = text.replace("\n", " ")     # interne newlines weg
    text = re.sub(r"\s+", " ", text)   # doppelte spaces normalisieren
    text = text.strip()                # trim außen

    return text

def sort_elements(elements):
    """
    Sorts elements by page (page_idx) and vertical position (bbox[1]).
    """
    return sorted(elements, key=lambda x: (
        x.get('page_idx', 0),
        x.get('bbox', [0, 0, 0, 0])[1]
    ))


ABSATZ_PATTERN = re.compile(
    r"""^(
        \(\d+\)            |   # (1)
        \d+\.\s                |   # 1.
        [IVXLCDM]+\.*\s      |   # I.  II  etc.
        [a-z]{1,2}\)\s       |   # a)  b)  aa)  bb)
        P\s                # P
    )""",
    re.VERBOSE
)


def starts_new_paragraph(text: str) -> bool:
    return bool(ABSATZ_PATTERN.match(text.strip()))


def convert_to_markdown(data):
    relevant_elements = [
        elem for elem in data
        if elem.get('type') in ['text', 'list', 'table']
    ]

    sorted_elements = sort_elements(relevant_elements)

    markdown_lines = []
    current_paragraph = ""

    for elem in sorted_elements:
        elem_type = elem.get('type')

        # =========================
        # TEXT BLOCK
        # =========================
        if elem_type == 'text':
            text = clean_text(elem.get('text', ''))
            text_level = elem.get('text_level', 0) or 0

            if not text:
                continue

            # -------- HEADING --------
            if text_level > 0:
                if current_paragraph:
                    markdown_lines.append(current_paragraph.strip() + "\n\n\n")
                    current_paragraph = ""

                heading_level = min(text_level, 6)
                markdown_lines.append(f'{"#" * heading_level} {text}\n')
                continue

            # -------- NORMAL TEXT --------
            if starts_new_paragraph(text):
                if current_paragraph:
                    markdown_lines.append(current_paragraph.strip() + "\n")
                current_paragraph = text
            else:
                current_paragraph += " " + text

        # =========================
        # LIST BLOCK
        # =========================
        elif elem_type == 'list':
            for item in elem.get('list_items', []):
                item = clean_text(item)
                if not item:
                    continue

                if starts_new_paragraph(item):
                    if current_paragraph:
                        markdown_lines.append(current_paragraph.strip() + "\n")
                    current_paragraph = item
                else:
                    current_paragraph += " " + item

        # =========================
        # TABLE BLOCK
        # =========================
        elif elem_type == 'table':
            if current_paragraph:
                markdown_lines.append(current_paragraph.strip() + "\n")
                current_paragraph = ""

            captions = elem.get('table_caption') or []
            table_body = clean_text(elem.get('table_body', ''))

            captions = elem.get('table_caption') or []
            caption_text = " ".join(clean_text(c) for c in captions if clean_text(c))

            if caption_text and table_body:
                markdown_lines.append(f"{caption_text}: {table_body}\n")
            elif table_body:
                markdown_lines.append(f"{table_body}\n")
            elif caption_text:
                markdown_lines.append(f"{caption_text}\n")

    # letzten Absatz flushen
    if current_paragraph:
        markdown_lines.append(current_paragraph.strip() + "\n\n")

    return ''.join(markdown_lines)


def main():
    PROJECT_NAME = "downloaded_arbeitsrecht_zuschnitt_3"
    INPUT_PATH = Path(__file__).parent / PROJECT_NAME / "new_content_list.json"
    OUTPUT_PATH = Path(__file__).parent / PROJECT_NAME / "output.md"


    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    print(f"Loading Data from '{INPUT_PATH}'...")
    data = load_data(INPUT_PATH)

    print("Converting to markdown ...")
    markdown_content = convert_to_markdown(data)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Markdown saved in '{OUTPUT_PATH}'")


if __name__ == '__main__':
    main()
