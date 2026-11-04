"""Parse a Markdown ticket into a title, sections, and list items."""

import re
from dataclasses import dataclass, field

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(?:\[[ xX]\]\s+)?(.+)$")
FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class Section:
    heading: str
    level: int
    line: int
    items: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Ticket:
    text: str
    title: str | None
    sections: list[Section]


def parse_ticket(text: str) -> Ticket:
    title: str | None = None
    sections: list[Section] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if heading := HEADING.match(line):
            level, name = len(heading.group(1)), heading.group(2)
            if level == 1 and title is None:
                title = name
            else:
                sections.append(Section(name, level, number))
        elif sections and (item := ITEM.match(line)):
            sections[-1].items.append(item.group(1).strip())
    return Ticket(text, title, sections)
