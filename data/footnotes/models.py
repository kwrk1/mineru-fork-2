from typing import Optional
from dataclasses import dataclass
from typing import List, Tuple, Callable

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
    inserted: bool = False


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