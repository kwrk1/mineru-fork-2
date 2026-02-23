import json
import re
import pdfplumber
import logging

from pathlib import Path
from collections import defaultdict
from dataclasses import asdict

from filtering_footnotes import filtering_footnotes_arbeitsrecht
from finding_footnotes_in_text import finding_footnotes_in_text, extract_left_context, extract_right_context
from models import ListBlock, TextBlock
from building_footnote_dict import build_footnote_dict, parse_trailing_footnotes
from finding_footnotes_in_mineru_block import apply_insertions, collect_insertions


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),              # stdout (live)
        logging.FileHandler("log.log")        # Datei
    ]
)


def insert_inline_footnotes_pdf(input_pdf_file: Path, input_content_list_file_1: Path, input_content_list_file_2: Path, output_folder: Path):

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

    all_mineru_blocks = []

    #logging
    insertion_errors = 0
    map_smaller_pdf = 0
    map_bigger_pdf = 0
    no_footnotes_extracted = 0

    with open(output_folder / "new_content_list.jsonl", "w", encoding="utf-8") as out, \
        pdfplumber.open(input_pdf_file) as pdf:

        for idx, page in enumerate(pdf.pages):

            chars = page.chars

            page_blocks = pages.get(idx, [])

            mineru_page_text_blocks = [TextBlock(**block) for block in page_blocks if block["page_idx"] == idx and block["type"] == "text"]
            mineru_page_list_blocks = [ListBlock(**block) for block in page_blocks if block["page_idx"] == idx and block["type"] == "list"]
            mineru_page_footnote_blocks = [block for block in page_blocks if block["page_idx"] == idx and block["type"] == "page_footnote"]

            all_page_mineru_blocks = mineru_page_text_blocks + mineru_page_list_blocks

            #Finding and building footnotes from the text
            footnotes_in_text = finding_footnotes_in_text(chars)

            for fn in footnotes_in_text:
                fn.left_context = extract_left_context(chars, fn)
                fn.right_context = extract_right_context(chars, fn)


            #TODO: das muss wahrscheinlich immer anders gemacht werden.
            #Most of the time there are multiple smaller digits we need to find the correct ones which are indeed a footnote
            top_footnotes = [f for f in footnotes_in_text if int(f.number) < 100]
            top_footnotes = filtering_footnotes_arbeitsrecht(top_footnotes)

            #Now we need a mapping from the footnote number to the actual reference mineru extracted
            footnote_map = build_footnote_dict(
                mineru_page_footnote_blocks,
                parse_trailing_footnotes,
                page_idx=idx
            )

            if len(footnote_map) != len(top_footnotes):
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

                if not footnote_map:
                    logging.info("ANFANG KEINE FOOTNOTE MAP")
                    logging.info(f"MinerU Error on Page: Content List: {idx} PDF: {idx+1}")
                    logging.info("ENDE KEINE FOOTNOTE MAP")
                    no_footnotes_extracted += 1
                elif len(footnote_map) < len(top_footnotes):
                    logging.info("ANFANG FOOTNOTE MAP < FOOTNOTES FROM PDF")
                    logging.info(f"MinerU Error on Page: Content List: {idx} PDF: {idx+1}")
                    logging.info("ENDE FOOTNOTE MAP < FOOTNOTES FROM PDF")
                    map_smaller_pdf += 1
                elif len(footnote_map) > len(top_footnotes):
                    logging.info("ANFANG FOOTNOTE MAP > FOOTNOTES FROM PDF")
                    logging.info(f"My misstake on page: Content List: {idx} PDF: {idx+1}")
                    logging.info(footnote_map)
                    logging.info("-----")
                    logging.info(top_footnotes)
                    logging.info("ENDE FOOTNOTE MAP > FOOTNOTES FROM PDF")
                    map_bigger_pdf += 1


            #Preparing the MinerU Blocks for the insertion of inline footnotes
            total_insertions = 0
            for block in all_page_mineru_blocks:
                if isinstance(block, TextBlock):
                    insertions = collect_insertions(block.text, top_footnotes)

                    if insertions:
                        total_insertions += len(insertions)
                        block.text = apply_insertions(block.text, insertions)
                elif isinstance(block, ListBlock):
                    new_list_items = []
                    for text in block.list_items:
                        insertions = collect_insertions(text, top_footnotes)

                        if insertions:
                            total_insertions += len(insertions)
                            new_text = apply_insertions(text, insertions)
                            new_list_items.append(new_text)
                        else:
                            new_list_items.append(text)
                    
                    block.list_items = new_list_items
                else:
                    logging.info(f"Unknown Block Instance: {block}")
            
            not_inserted = [fn for fn in top_footnotes if not fn.inserted]

            if not_inserted:
                logging.info("ANFANG INSERTION ERROR")
                logging.info(f"Insertions Error on Page: Content List: {idx} PDF: {idx+1}")
                
                insertion_errors += len(not_inserted)

                for fn in not_inserted:
                    logging.info(f"NOT INSERTED: {fn.number} | left='{fn.left_context}' | right='{fn.right_context}'")

                logging.info("ENDE INSERTION ERROR")
                

            #Finaly inserting the footnotes in the text
            for block in all_page_mineru_blocks:
                if isinstance(block, TextBlock):
                    text = block.text
                    new_text = insert_inline_footnotes(text, footnote_map, idx)
                    block.text = new_text
                if isinstance(block, ListBlock):
                    new_list_items = []
                    for text in block.list_items:
                        new_text = insert_inline_footnotes(text, footnote_map, idx)
                        new_list_items.append(new_text)
                    block.list_items = new_list_items

            for block in all_page_mineru_blocks:
                record = asdict(block)

                all_mineru_blocks.append(record)

                out.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

            all_mineru_blocks.extend(mineru_page_footnote_blocks)
            
            page.flush_cache()
    
        with open(output_folder / "new_content_list.json", "w") as out:
            json.dump(all_mineru_blocks, out, indent=2)
        
        logging.info("ERROR COUNTS:")
        logging.info(f"NO FOOTNOTE MAP ERRORS: {no_footnotes_extracted}")
        logging.info(f"MAP SMALLER TOP FOOTNOTES (MinerU Error): {map_smaller_pdf}")
        logging.info(f"MAP BIGGER TOP FOOTNOTES (Top Footnotes Extraction Error): {map_bigger_pdf}")
        logging.info(f"INSERTION ERRORS: {insertion_errors}")

def insert_inline_footnotes(text: str, footnote_map: dict[str, str], page_idx: int):
    def insert_footnote_with_error_log(x : re.Match) -> str:
        footnote = footnote_map.get(x.group())
        if not footnote:
            logging.info(f"Missing: {x.group()} on page_idx Content List: {page_idx} PDF: {page_idx+1}")
            return f"[REF]{x.group()}[/REF]"
        return f"[REF]{footnote}[/REF]"
    
    ref_pattern = r"\[REF\]\d+\[/REF\]"
    new_text = re.sub(ref_pattern, insert_footnote_with_error_log, text)

    return new_text


if __name__ == "__main__":
    logging.info("start insert inline footnotes")

    #Input PDF File
    input_path = Path(__file__).parent.parent / "input"
    input_pdf_file = input_path / "Arbeitsrecht_Kommentar.pdf"
    
    #Merge the content list before with merge_content_list.py
    PROJECT_NAME = "downloaded_arbeitsrecht"
    input_content_list_file_1 = Path(__file__).parent.parent / PROJECT_NAME / "merged_content_list.json"

    #output file for the new content list
    output_path = Path(__file__).parent.parent / PROJECT_NAME

    #Backup Run
    #Wieso die? habe von hand viel angepasst in den footnotes deswegen werden die jetzt als backup benutzt.
    #und die original daten sind die neuen mit den zugeschnittenen pdfs
    PROJECT_NAME = "downloaded_arbeitsrecht_zuschnitt_2"
    input_content_list_file_2 = Path(__file__).parent.parent / PROJECT_NAME / "merged_content_list.json"
    
    print("Writing to:", output_path.resolve())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #Main Step
    all_mineru_blocks = insert_inline_footnotes_pdf(
        input_pdf_file=input_pdf_file, 
        input_content_list_file_1=input_content_list_file_1,
        input_content_list_file_2=input_content_list_file_2,
        output_folder=output_path
        )




