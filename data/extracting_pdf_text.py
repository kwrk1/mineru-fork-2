from pathlib import Path
from collections import Counter
from typing import List, Tuple, Callable
import pdfplumber
from collections import defaultdict
from dataclasses import dataclass
import json
import re


@dataclass
class Footnote():
    number: str
    start_idx: int
    end_idx: int
    top: float
    bottom: float
    x0: float
    x1: float
    size: float
    page: int
    left_context: str = ""
    right_context: str = ""

FootnoteParser = Callable[[dict], List[Tuple[str, str]]]

def extract_pdf_text(pdf_path: Path, json_path: Path):

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        chars = page.chars

    with open(json_path) as json_input:
        mineru_blocks = json.load(json_input)
    
    mineru_page_text_blocks = [block for block in mineru_blocks if block["page_idx"] == 0 and block["type"] == "text"  and block.get("text_level") != 1]

    mineru_page_footnote_blocks = [block for block in mineru_blocks if block["page_idx"] == 0 and block["type"] == "page_footnote"]

    small_digits = finding_smaller_digits(chars)

    merged_numbers = merging_single_numbers(small_digits)

    top_footnotes, bottom_footnotes = splitting_footnotes(merged_numbers)

    for fn in top_footnotes:
        fn.left_context = extract_left_context(chars, fn)
        fn.right_context = extract_right_context(chars, fn)

        print(f"[{fn.number}]")
        print("LEFT :", fn.left_context)
        print("RIGHT:", fn.right_context)

    for block in mineru_page_text_blocks:
        insertions = collect_insertions(block["text"], top_footnotes)

        if insertions:
            block["text"] = apply_insertions(block["text"], insertions)
    
    for idx, block in enumerate(mineru_page_text_blocks):
        print(f"{idx}: {block['text']}\n\n")

    footnote_map = build_footnote_dict(
        mineru_page_footnote_blocks,
        parse_numeric_leading_footnote
    )

    for k, v in footnote_map.items():
        print(k, "→", v)

    for block in mineru_page_text_blocks:
        insert_inline_footnotes(block, footnote_map)

    for idx, block in enumerate(mineru_page_text_blocks):
        print(f"{idx}: {block['text']}\n\n")
    

    
def insert_inline_footnotes(block: dict, footnote_map: dict[str, str]):
    ref_pattern = r"\[REF\]\d+\[\\Ref\]"

    text = block["text"]
    new_text = re.sub(ref_pattern, lambda x : footnote_map[x.group()], text)

    block["text"] = new_text

    return block

    
def parse_numeric_leading_footnote(block: dict) -> List[Tuple[str, str]]:
    text = block.get("text", "").strip()

    # z. B. "1 Die Entscheidung ist …"
    m = re.match(r"^(\d+)\s+(.*)$", text)
    if not m:
        return []

    number, rest = m.groups()
    key = f"[REF]{number}[/REF]"

    return [(key, rest.strip())]


def build_footnote_dict(
    footnote_blocks: List[dict],
    parser: FootnoteParser
) -> dict[str, str]:

    result = {}

    for block in footnote_blocks:
        pairs = parser(block)

        for key, value in pairs:
            if key in result:
                # optional: warnen oder mergen
                print(f"⚠ Duplicate footnote key: {key}")
            result[key] = value

    return result

def same_line(a, b, tolerance=2):
    return abs(a["top"] - b["top"]) < tolerance

def needs_space(prev, curr, threshold=2.5):
    return (curr["x0"] - prev["x1"]) > threshold

def normalize_string(s: str) -> str:
    #Checke ich noch nicht ganz wieso gebraucht
    return " ". join(s.replace("\n", " ").split())

def find_footnote_in_block(block_text: str, footnote: Footnote):
    block = normalize_string(block_text)
    left = normalize_string(footnote.left_context)
    right = normalize_string(footnote.right_context)

    num_len = len(str(footnote.number))
    ref = f"[REF]{footnote.number}[/REF]"

    # LEFT + RIGHT
    if left and right:
        lpos = block.find(left)
        if lpos != -1:
            start = lpos + len(left)
            rpos = block.find(right, start)
            if rpos != -1:
                return (start, num_len, ref)

    # LEFT only
    if left:
        lpos = block.find(left)
        if lpos != -1:
            start = lpos + len(left)
            return (start, num_len, ref)

    # RIGHT only
    if right:
        rpos = block.find(right)
        if rpos != -1:
            return (rpos, num_len, ref)

    return None

def collect_insertions(block_text: str, footnotes: List[Footnote]):
    insertions = []

    for fn in footnotes:
        hit = find_footnote_in_block(block_text, fn)
        if hit:
            insertions.append(hit)

    return insertions

def apply_insertions(block_text: str, insertions):
    text = normalize_string(block_text)

    # rückwärts nach start_pos sortieren
    for start, delete_len, repl in sorted(insertions, reverse=True):
        text = text[:start] + repl + text[start + delete_len:]

    return text

def calculating_common_font_size(chars):
    sizes = [round(c["size"], 1) for c in chars if c["text"].strip()]
    common_size = Counter(sizes).most_common(1)[0][0]

    print("Häufigste Fontgröße:", common_size)
    return common_size

def finding_smaller_digits(chars):
    common_size = calculating_common_font_size(chars)

    small_digits = []

    for i, c in enumerate(chars):
        if c["text"].isdigit():
            if c["size"] < common_size - 1:
                small_digits.append(
                    Footnote(
                        number=c["text"],
                        start_idx=i,
                        end_idx=i,
                        top=c["top"],
                        bottom=c["bottom"],
                        x0=c["x0"],
                        x1=c["x1"],
                        size=c["size"],
                        page=c["page_number"]-1 #MinerU starts at 0 and pdfplumber starts at 1 :)
                    )
                )
    
    return small_digits

def merging_single_numbers(small_digits : List[Footnote]) -> List[Footnote]:
    #TODO: kann auch sein das mehr als nur zwei digits zu einer footnote passen ... das muss nochmal angepasst werden. moment das müsste schon funktionieren
    #testfall mit 2 und mehr nummern schreiben.

    #sorting the digits according to their height position on the page
    #same line digits are next to each other, but the left most char is first (smaller x0)
    small_digits.sort(key=lambda c: (round(c.top, 1), c.x0))

    #Zusammenführen von Zahlen die nah beisammen sind 1,2 -> 12
    merged = []
    
    prev = None

    for small_digit in small_digits:
        if prev is None:
            prev = small_digit
            continue
        
        if not isinstance(prev, Footnote):
            continue

        same_line = abs(small_digit.top - prev.top) < 2
        #left of char we are looking at the moment - right from the char we looked at prev
        close_x = small_digit.x0 - prev.x1 < 5

        if same_line and close_x:
            prev.number += small_digit.number
            prev.x1 = small_digit.x1
            prev.end_idx = small_digit.end_idx
        else:
            merged.append(prev)
            prev = small_digit

    if prev:
        merged.append(prev)

    return merged

def splitting_footnotes(merged_numbers: List[Footnote]) -> Tuple[List[Footnote], List[Footnote]]:
    #Wir haben immer zwei gleiche pro seite einmal im ließtext und einmal unten als verweis
    #Nur die weiter oben stehende kleine Zahl wird genommen (da diese im Fließtext steht)
    #Wir splitten die jetzt, damit wir mit beiden arbeiten können

    by_number = defaultdict(list[Footnote])

    for f in merged_numbers:
        by_number[f.number].append(f)

    footnotes_in_text = []
    footnotes_at_bottom = []

    for number, items in by_number.items():
        topmost = min(items, key=lambda x: x.top)
        footnotes_in_text.append(topmost)

        bottommost = max(items, key=lambda x: x.top)
        footnotes_at_bottom.append(bottommost)
        
    print("Footnotes in the Text:")
    for footnote in footnotes_in_text:
        print(footnote)
    
    print("Footnotes in at Bottom:")
    for footnote in footnotes_at_bottom:
        print(footnote)

    return footnotes_in_text, footnotes_at_bottom

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

def extract_right_context(chars, footnote: Footnote, max_chars=80) -> str:
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



if __name__ == "__main__":
    #Input PDF File
    input_path = Path(__file__).parent / "input"
    pdf_file = input_path / "bgh.pdf"

    output_path = Path(__file__).parent / "output"

    #Input content_list from MinerU
    json_file = output_path / "bgh_content_list.json"

    extract_pdf_text(pdf_file, json_file)


