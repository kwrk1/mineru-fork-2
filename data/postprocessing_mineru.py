import re
import json

from typing import Optional
from pathlib import Path

def extract_page_footnote_number(footnote: str, last_footnote_number: Optional[int] = None) -> int:
    footnote = footnote.strip()
    
    # Fall 1: HTML <sup>-Tag
    html_match = re.match(r'^<sup>(\d+)</sup>', footnote)
    if html_match:
        return int(html_match.group(1))
    
    # Fall 2: LaTeX $^{...}$-Format
    latex_match = re.match(r'^\$\^{(\d+)}\$', footnote)
    if latex_match:
        return int(latex_match.group(1))
    
    # Fall 3: Einfache Zahl am Anfang (gefolgt von Leerzeichen oder Nicht-Ziffer)
    simple_match = re.match(r'^(\d+)(?:\s|\D)', footnote)
    if simple_match:
        return int(simple_match.group(1))
    
    # Fallback (Man kann das noch besser machen, aber wesentlich mehr aufwand erstmal so und beobachten, wie gut das funktioniert.)
    if last_footnote_number is not None:
        print(f"Musste auf Fallback bei footnote zugreifen: {footnote}")
        return last_footnote_number + 1

    raise ValueError(f"Konnte keine Fußnotennummer in '{footnote[:50]}...' finden")

def insert_page_footnote_number(text: str, page_footnote_number: int) -> str:
    return ""

def create_final_text(input_file: Path):

    final_text = ""
    last_footnote_number = None

    with open(input_file, "r") as in_f:
        content = json.load(in_f)

        text_buffer = []
        page_nr = 0

        for idx, entry in enumerate(content):

            if entry["type"] == "text":
                text_buffer.append(entry["text"])
                
                if entry["page_idx"] > page_nr:
                    print(f"New Page: {entry['page_idx']}")
                    page_nr = entry["page_idx"]
                    final_text += "\n\n".join(text_buffer)
                    text_buffer = []

            if entry["type"] == "list":
                if entry["sub_type"] != "text":
                    print(f"Unknown Subtype of list: {entry['sub_type']}")
                    continue
            
                text_buffer.extend(entry["list_items"])

                if entry["page_idx"] > page_nr:
                    print(f"New Page: {entry['page_idx']}")
                    page_nr = entry["page_idx"]
                    final_text += "\n\n".join(text_buffer)
                    text_buffer = []

            if entry["type"] == "page_footnote":
                footnote = entry["text"]
                footnote_number = extract_page_footnote_number(footnote, last_footnote_number)
                last_footnote_number = footnote_number

                


            


                










def main():

    INPUT_DIR = Path(__file__).parent / "output"
    json_path = INPUT_DIR / "bgh_content_list.json"

    create_final_text(json_path)


if __name__ == "__main__":
    main()