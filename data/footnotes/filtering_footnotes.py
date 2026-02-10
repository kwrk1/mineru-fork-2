from typing import List, Tuple
from models import Footnote

from collections import defaultdict

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


#Funktioniert für die BGH Urteile/Zeitschriften
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