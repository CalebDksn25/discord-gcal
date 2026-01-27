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
    kind: ItemType
    title: str
    when: Optional[str] = None # ISO String for now - can be improved later
    location: Optional[str] = None
    raw: str = "" # Original raw text

# Keywords to help identify tasks
TASK_HINTS = [
    "homework", "assignment", "submit", "turn in", "due", "finish",
    "complete", "study", "read", "quiz", "exam", "project"
]

# Function to parse text input and extract relevant information
def parse_text(text: str, timezone: str = "America/Los_Angeles") -> ParsedItem:
    """
    Parse the input text to extract item type, title, time, and location.
    Uses simple heuristics and dateparser for time extraction.
    """

    # Get cleaned text
    t = text.strip()

    # 1) Extract time if present
    dt = dateparser.parse(
        t,
        settings={
            "TIMEZONE": timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future"
        },
    )

    # Convert to ISO format if date found
    when_iso = dt.isoformat() if dt else None

    # 2) Decide if task or event
    lower = t.lower()
    kind: ItemType = "task"
    if dt: # If we found a date or time, assume its an event
        kind = "event"
    if any(h in lower for h in TASK_HINTS):
        kind="task"

    # 3) Extract location if present (SIMPLE, for now just checks for 'in <something>')
    location = None
    # Look for " in <location>" at the end of the string
    m = re.search(r"\bin\s+(.+)$", t, re.IGNORECASE)
    if m:
        # Extract location and remove from title
        location = m.group(1).strip()

    # 4) Title heuristic - remove time and location phrases
    title = t
    if location:
        title = re.sub(r"\bin\s+.+$", "", title, flags=re.IGNORECASE).strip()

    return ParsedItem(
        kind = kind,
        title = title,
        when = when_iso,
        location = location,
        raw = t
    )