"""Ticket rules. A rule is a function (Ticket) -> list[Finding], registered in RULES."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ticketsmith.ticket import Ticket

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    fix: str
    line: int | None = None


Rule = Callable[[Ticket], list[Finding]]

AC_HEADINGS = ("acceptance criteria", "definition of done", "done when")
AC_FIX = 'Add "## Acceptance criteria" with a checklist of observable outcomes.'


def ac001_has_acceptance_criteria(ticket: Ticket) -> list[Finding]:
    sections = ticket.sections
    first_empty = None
    for i, section in enumerate(sections):
        if not any(h in section.heading.lower() for h in AC_HEADINGS):
            continue
        # Items directly under the heading or under deeper sub-headings count.
        nested = []
        for sub in sections[i + 1 :]:
            if sub.level <= section.level:
                break
            nested.append(sub)
        if section.items or any(sub.items for sub in nested):
            return []
        first_empty = first_empty or section
    if first_empty:
        return [Finding("AC001", "error", "Acceptance criteria section has no list items.", AC_FIX, first_empty.line)]
    return [Finding("AC001", "error", "No acceptance criteria section found.", AC_FIX)]


RULES: list[Rule] = [ac001_has_acceptance_criteria]
