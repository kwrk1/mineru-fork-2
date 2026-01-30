from pathlib import Path
from collections import Counter
from typing import List, Tuple, Callable
import pdfplumber
from collections import defaultdict
from dataclasses import dataclass, asdict
import json
import re
from typing import Optional
from pprint import pprint
import logging
import gc
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),              # stdout (live)
        logging.FileHandler("log.log")        # Datei
    ]
)

logging.info("Starte PDF-Extraktion")

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


@dataclass
class BaseBlock:
    page_idx: int
    bbox: list[int]
    type: str
    
@dataclass
class TextBlock(BaseBlock):
    text: str
    text_level: Optional[int] = None

@dataclass
class ListBlock(BaseBlock):
    sub_type: str
    list_items: list[str]

FootnoteParser = Callable[[dict], List[Tuple[str, str]]]


def extract_pdf_text(input_pdf_file: Path, input_content_list_file_1: Path, input_content_list_file_2: Path, output_jsonl_file: Path):

    #Main Data
    with open(input_content_list_file_1) as inp:
        mineru_blocks = json.load(inp)

    pages = defaultdict(list)
    for block in mineru_blocks:
        pages[block["page_idx"]].append(block)

    del mineru_blocks

    #Backup Data from another run
    with open(input_content_list_file_2) as inp:
        backup_mineru_blocks = json.load(inp)

    backup_pages = defaultdict(list)
    for block in backup_mineru_blocks:
        backup_pages[block["page_idx"]].append(block)

    del backup_mineru_blocks

    with open(output_jsonl_file, "w", encoding="utf-8") as out, \
         pdfplumber.open(input_pdf_file) as pdf:
        for idx, page in enumerate(pdf.pages):

            #print(idx)
            chars = page.chars

            page_blocks = pages.get(idx, [])

            mineru_page_text_blocks = [TextBlock(**block) for block in page_blocks if block["page_idx"] == idx and block["type"] == "text"]
            mineru_page_list_blocks = [ListBlock(**block) for block in page_blocks if block["page_idx"] == idx and block["type"] == "list"]
            mineru_page_footnote_blocks = [block for block in page_blocks if block["page_idx"] == idx and block["type"] == "page_footnote"]

            all_page_mineru_blocks = mineru_page_text_blocks + mineru_page_list_blocks



            small_digits = finding_smaller_digits(chars)

            #merged_numbers = merging_single_numbers(small_digits)

            #top_footnotes, bottom_footnotes = splitting_footnotes(small_digits)

            for fn in small_digits:
                fn.left_context = extract_left_context(chars, fn)
                fn.right_context = extract_right_context(chars, fn)

                #print(f"[{fn.number}]")
                #print("LEFT :", fn.left_context)
                #logging.info("RIGHT:", fn.right_context)

            #TODO: das muss wahrscheinlich immer anders gemacht werden.
            top_footnotes = [f for f in small_digits if int(f.number) < 100]
            top_footnotes = filtering_footnotes_arbeitsrecht(top_footnotes)

            footnote_map = build_footnote_dict(
                mineru_page_footnote_blocks,
                parse_trailing_footnotes,
                page_idx=idx
            )

            if len(footnote_map) != len(top_footnotes):
                logging.info("Trying backup data.")

                backup_page_blocks = backup_pages.get(idx, [])
                backup_mineru_page_footnote_blocks = [
                    block for block in backup_page_blocks
                    if block["type"] == "page_footnote"
                ]

                footnote_map = build_footnote_dict(
                    backup_mineru_page_footnote_blocks,
                    parse_trailing_footnotes,
                    page_idx=idx
                )

                logging.info(f"Footnote Error on Page: Content List: {idx} PDF: {idx+1}")
                if not footnote_map:
                    logging.info(f"MinerU Error on Page: Content List: {idx} PDF: {idx+1}")
                    continue
                
                if len(footnote_map) < len(top_footnotes):
                    logging.info(f"MinerU Error on Page: Content List: {idx} PDF: {idx+1}")
                
                if len(footnote_map) > len(top_footnotes):
                    logging.info(f"My misstake on page: Content List: {idx} PDF: {idx+1}")
                    logging.info(footnote_map)
                    logging.info("-----")
                    logging.info(top_footnotes)
                
                logging.info("Sucessfully used backup data.")

            for block in all_page_mineru_blocks:
                if isinstance(block, TextBlock):
                    insertions = collect_insertions(block.text, top_footnotes)

                    if insertions:
                        block.text = apply_insertions(block.text, insertions)
                elif isinstance(block, ListBlock):
                    new_list_items = []
                    for text in block.list_items:
                        insertions = collect_insertions(text, top_footnotes)

                        if insertions:
                            new_text = apply_insertions(text, insertions)
                            new_list_items.append(new_text)
                        else:
                            new_list_items.append(text)
                    
                    block.list_items = new_list_items
                else:
                    logging.info(f"Unknown Block Instance: {block}")
            
            #for idx, block in enumerate(all_page_mineru_blocks):
            #    if isinstance(block, TextBlock):
            #        logging.info(f"{idx}: {block.text}\n\n")
            #    if isinstance(block, ListBlock):
            #        for idx_2, text in enumerate(block.list_items):
            #            logging.info(f"{idx} {idx_2}: {text}\n\n")



            
                    
            #for k, v in footnote_map.items():
            #    logging.info(k, "→", v)

            for block in all_page_mineru_blocks:
                if isinstance(block, TextBlock):
                    text = block.text
                    new_text = insert_inline_footnotes(text, footnote_map, idx + 1)
                    block.text = new_text
                if isinstance(block, ListBlock):
                    new_list_items = []
                    for text in block.list_items:
                        new_text = insert_inline_footnotes(text, footnote_map, idx + 1)
                        new_list_items.append(new_text)
                    block.list_items = new_list_items

            #for idx, block in enumerate(all_page_mineru_blocks):
            #    if isinstance(block, TextBlock):
            #        logging.info(f"{idx}: {block.text}\n\n")
            #    if isinstance(block, ListBlock):
            #        for idx_2, text in enumerate(block.list_items):
            #            logging.info(f"{idx} {idx_2}: {text}\n\n")
            for block in all_page_mineru_blocks:
                record = asdict(block)

                out.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

            del all_page_mineru_blocks
            del mineru_page_text_blocks
            del mineru_page_list_blocks
            del mineru_page_footnote_blocks
            del small_digits
            del top_footnotes
            del footnote_map
            del chars
            
            page.flush_cache()
            gc.collect()
    


def filtering_footnotes_arbeitsrecht(footnotes: List[Footnote]) -> List[Footnote]:
    #sorted_footnotes = sorted(footnotes, key=lambda x : int(x.number))
    last = 0
    final = []

    #Somehow startet die footnotes auf seite 449 auf einmal mit 4 lovely
    #auschließen das die erste footnote ein bruch ist.
    if footnotes:
        if not (footnotes[0].left_context.endswith("/") or footnotes[0].right_context.startswith("/")):
            last = int(footnotes[0].number) - 1 

    for f in footnotes:
        if f.left_context.endswith("/") or f.right_context.startswith("/"):
            continue
        #TODO: immer noch nciht perfekt kann auch beides eintreten!
        if int(f.number) > last + 1:
            continue

        if "||" in f.left_context or "||" in f.right_context:
            break

        last += 1
        final.append(f)

    return final

def insert_inline_footnotes(text: str, footnote_map: dict[str, str], page_idx: int):
    def insert_footnote_with_error_log(x : re.Match) -> str:
        footnote = footnote_map.get(x.group())
        if not footnote:
            logging.info(f"Missing: {x.group()} on page_idx: {page_idx}")
            return f"[REF]{x.group()}[/REF]"
        return f"[REF]{footnote}[/REF]"
    
    ref_pattern = r"\[REF\]\d+\[/REF\]"
    new_text = re.sub(ref_pattern, insert_footnote_with_error_log, text)

    return new_text

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

#TODO: das muss für jede pdf angepasst werden die tol and threshold
def same_line(a, b, tolerance=2.5):
    return abs(a["top"] - b["top"]) < tolerance

#TODO: das muss für jede pdf angepasst werden die tol and threshold
def needs_space(prev, curr, threshold=1.5):
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
        
        return None

    # LEFT only
    if left:
        lpos = block.find(left)
        if lpos != -1:
            start = lpos + len(left)
            return (start, num_len, ref)

        return None

    # RIGHT only
    if right:
        rpos = block.find(right)
        if rpos != -1:
            return (rpos, num_len, ref)
        
        return None
    
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

    #logging.info("Häufigste Fontgröße:", common_size)
    return common_size

def finding_smaller_digits(chars) -> List[Footnote]:
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
        
    #logging.info("Footnotes in the Text:")
    #for footnote in footnotes_in_text:
    #   logging.info(footnote)
    
    #logging.info("Footnotes in at Bottom:")
    #for footnote in footnotes_at_bottom:
    #    logging.info(footnote)

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


if __name__ == "__main__":
    #Input PDF File
    input_path = Path(__file__).parent / "input"
    input_pdf_file = input_path / "Arbeitsrecht_Kommentar.pdf"
    
    #Merge the content list before with merge_content_list.py
    PROJECT_NAME = "downloaded_arbeitsrecht"
    input_content_list_file_1 = Path(__file__).parent / PROJECT_NAME / "merged_content_list.json"

    #Backup Rrun
    PROJECT_NAME = "downloaded_arbeitsrecht_2"
    input_content_list_file_2 = Path(__file__).parent / PROJECT_NAME / "merged_content_list.json"
    #output file for the new content list
    output_file = Path(__file__).parent / PROJECT_NAME / "new_content_list.jsonl"

    #Main Step
    all_mineru_blocks = extract_pdf_text(
        input_pdf_file=input_pdf_file, 
        input_content_list_file_1=input_content_list_file_1,
        input_content_list_file_2=input_content_list_file_2,
        output_jsonl_file=output_file
        )




