import re
import logging

from typing import List, Tuple

from models import FootnoteParser

def parse_numeric_leading_footnote(block: dict) -> List[Tuple[str, str]]:
    text = block.get("text", "").strip()

    # z. B. "1 Die Entscheidung ist …"
    m = re.match(r"^(\d+)\s+(.*)$", text)
    if not m:
        return []

    number, rest = m.groups()
    key = f"[REF]{number}[/REF]"

    return [(key, rest.strip())]

def parse_trailing_footnotes(block: dict) -> List[Tuple[str, str]]:
    final_keys = []
    text: str = block.get("text", "").strip()

    splitted_text = re.split(r"\s*\|\|\s*|\s*\|\s*", text)
    if splitted_text:
        for split in splitted_text:

            m = re.match(r"^\s*(\d+)\s+(.*)$", split)
            if not m:
                continue

            number, rest = m.groups()
            key = f"[REF]{number}[/REF]"
            final_keys.append((key, rest.strip()))

    return final_keys

def build_footnote_dict(
    footnote_blocks: List[dict],
    parser: FootnoteParser,
    page_idx: int
) -> dict[str, str]:

    result = {}

    for block in footnote_blocks:
        pairs = parser(block)

        for key, value in pairs:
            if key in result:
                # optional: warnen oder mergen
                logging.info(f"⚠ Duplicate footnote key: {key} on page_idx: {page_idx}")
                continue

            result[key] = value

    return result