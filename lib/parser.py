from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import re
import dateparser

# Define the types of items we can parse
ItemType = Literal["event", "task"]

# Dataclass to hold parsed item information
@dataclass
class ParsedItem:
    item_type: ItemType
    title: str
    when: Optional[str] = None # ISO String for now - can be improved later
    location: Optional[str] = None
    raw: str

# Keywords to help identify tasks
TASK_HINTS = [
    "homework", "assignment", "submit", "turn in", "due", "finish",
    "complete", "study", "read", "quiz", "exam", "project"
]