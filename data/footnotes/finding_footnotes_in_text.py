from typing import List
from collections import Counter

from models import Footnote

#TODO: das muss für jede pdf angepasst werden die tol
def same_line(a, b, tolerance=2.5):
    return abs(a["top"] - b["top"]) < tolerance

#TODO: das muss für jede pdf angepasst der threshold
def needs_space(prev, curr, threshold=1.0):
    return (curr["x0"] - prev["x1"]) > threshold

def calculating_common_font_size(chars):
    sizes = [round(c["size"], 1) for c in chars if c["text"].strip()]
    common_size = Counter(sizes).most_common(1)[0][0]

    #logging.info("Häufigste Fontgröße:", common_size)
    return common_size

def finding_footnotes_in_text(chars) -> List[Footnote]:
    common_size = calculating_common_font_size(chars)
    #TODO: kleiner hack
    common_size = 7

    footnotes: List[Footnote] = []
    i = 0

    while i < len(chars):
        c = chars[i]

        if not (c["text"].isdigit() and c["size"] < common_size - 1):
            i += 1
            continue

        # Start einer neuen Fußnotenzahl
        number = c["text"]
        start_idx = i
        end_idx = i
        x0 = c["x0"]
        x1 = c["x1"]
        top = c["top"]
        bottom = c["bottom"]
        size = c["size"]
        page = c["page_number"] - 1

        # NUR: direkt folgende chars prüfen
        j = i + 1
        while j < len(chars):
            next_c = chars[j]

            if (
                next_c["text"].isdigit()
                and next_c["size"] < common_size - 1
            ):
                number += next_c["text"]
                end_idx = j
                x1 = next_c["x1"]
                bottom = max(bottom, next_c["bottom"])
                j += 1
            else:
                break

        footnotes.append(
            Footnote(
                number=number,
                start_idx=start_idx,
                end_idx=end_idx,
                top=top,
                bottom=bottom,
                x0=x0,
                x1=x1,
                size=size,
                page=page
            )
        )

        i = j  # Skip bereits gemergte chars
    
    footnotes.sort(key=lambda c: (round(c.top, 1), c.x0))
    
    return footnotes

def extract_left_context(chars, footnote: Footnote, max_chars=80) -> str:
    result = []
    base = chars[footnote.start_idx]

    for i in range(footnote.start_idx - 1, -1, -1):
        c = chars[i]

        if not same_line(c, base):
            break

        if result:
            if needs_space(c, result[-1]):
                result.append({"text": " "})

        result.append(c)

        if len(result) >= max_chars:
            break

    return "".join(c["text"] for c in reversed(result)).strip()

def extract_right_context(chars, footnote: Footnote, max_chars=40) -> str:
    result = []
    base = chars[footnote.end_idx]

    for i in range(footnote.end_idx + 1, len(chars)):
        c = chars[i]

        if not same_line(c, base):
            break

        if result:
            if needs_space(result[-1], c):
                result.append({"text": " "})

        result.append(c)

        if len(result) >= max_chars:
            break

    return "".join(c["text"] for c in result).strip()