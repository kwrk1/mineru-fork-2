"""
JSON/JSONL to Markdown Converter
Converts JSON or JSONL data with text and list elements into Markdown.
Sorts by page_idx and vertical position (bbox[1]).
"""

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


def sort_elements(elements):
    """
    Sorts elements by page (page_idx) and vertical position (bbox[1]).
    """
    return sorted(elements, key=lambda x: (
        x.get('page_idx', 0),
        x.get('bbox', [0, 0, 0, 0])[1]
    ))


def convert_to_markdown(data):
    """
    Converts JSON data into Markdown.
    """

    relevant_elements = [
        elem for elem in data
        if elem.get('type') in ['text', 'list']
    ]

    sorted_elements = sort_elements(relevant_elements)

    markdown_lines = []
    current_page = None

    for elem in sorted_elements:
        page_idx = elem.get('page_idx', 0)
        elem_type = elem.get('type')

        if page_idx != current_page:
            if current_page is not None:
                markdown_lines.append('\n---\n')

            markdown_lines.append(f'## Page {page_idx + 1}\n\n')
            current_page = page_idx

        if elem_type == 'text':
            text = elem.get('text', '').strip()
            text_level = elem.get('text_level', 0)

            if not text_level:
                text_level = 0

            if text:
                if text_level > 0:
                    heading_level = min(text_level + 2, 6)  # Markdown max ######
                    markdown_lines.append(f'{"#" * heading_level} {text}\n\n')
                else:
                    markdown_lines.append(f'{text}\n\n')

        elif elem_type == 'list':
            list_items = elem.get('list_items', [])

            for item in list_items:
                item = item.strip()
                if item:
                    markdown_lines.append(f'- {item}\n')

            markdown_lines.append('\n')

    return ''.join(markdown_lines)


def main():
    PROJECT_NAME = "downloaded_arbeitsrecht"
    INPUT_PATH = Path(__file__).parent / PROJECT_NAME / "new_content_list.jsonl"
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
