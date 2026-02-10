from typing import List

from models import Footnote

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