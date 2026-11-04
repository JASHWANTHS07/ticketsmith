"""Run all rules on a ticket, score it, and format the report."""

from dataclasses import dataclass

from ticketsmith.rules import RULES, Finding
from ticketsmith.ticket import parse_ticket

PENALTY = {"error": 25, "warning": 10, "info": 0}


@dataclass(frozen=True)
class Report:
    findings: list[Finding]
    score: int


def score(findings: list[Finding]) -> int:
    return max(0, 100 - sum(PENALTY[f.severity] for f in findings))


def check(text: str) -> Report:
    ticket = parse_ticket(text)
    findings = [finding for rule in RULES for finding in rule(ticket)]
    return Report(findings, score(findings))


def format_text(name: str, report: Report) -> str:
    lines = [f"{name} - score {report.score}/100"]
    if not report.findings:
        lines.append("  No findings.")
    for f in report.findings:
        where = f" line {f.line}" if f.line else ""
        prefix = f"  {f.severity.upper()} {f.rule_id}{where}  "
        lines.append(prefix + f.message)
        lines.append(" " * len(prefix) + "Fix: " + f.fix)
    return "\n".join(lines)
