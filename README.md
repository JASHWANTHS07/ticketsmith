# TicketSmith

AI coding agents build what a ticket *says*, not what you *meant*. TicketSmith checks a Markdown ticket before an agent starts work and tells you exactly what to fix, so the agent gets a concrete definition of done.

## Run it

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12+ is installed automatically).

```bash
uv sync
uv run ticketsmith check path/to/ticket.md
cat ticket.md | uv run ticketsmith check -
```

Example:

```
$ uv run ticketsmith check tests/fixtures/no_ac.md
tests/fixtures/no_ac.md - score 75/100
  ERROR AC001  No acceptance criteria section found.
               Fix: Add "## Acceptance criteria" with a checklist of observable outcomes.
```

Exit codes: `0` no errors, `1` at least one error finding, `2` usage or file error.

**Score:** starts at 100; each error costs 25, each warning 10; never below 0. Every deducted point maps to a finding.

## Rules

| ID | Severity | Checks |
|---|---|---|
| AC001 | error | Ticket has an "Acceptance criteria" / "Definition of done" / "Done when" section (any heading level) with at least one list item. |

## Test

```bash
uv run pytest
```

## About

Built during the [Qodo Hackathon](https://hackathon.qodo.ai/) (Nov–Dec 2026) with AI assistance: code written with Claude Code, pull requests reviewed by Qodo.
