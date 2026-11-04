# TicketSmith — Design

Date: 2026-11-04 · Status: draft for approval

## Intent

AI coding agents build what a ticket *says*, not what the author *meant*. Vague tickets ("make search faster", "improve the UI") produce wrong builds, wasted PRs, and review churn. TicketSmith checks a ticket **before** an agent starts work and tells the author exactly what to fix so the agent has a concrete definition of done.

It is also the backbone of our Qodo Hackathon entry ("Build a Software Factory in 30 Days"): the factory dogfoods it. Every daily ticket we write is checked by TicketSmith; later the coding agent calls it through MCP before implementing, and CI refuses to proceed on tickets that score too low.

## Users

- **Primary:** developers who hand tickets to AI coding agents (Claude Code, Cursor, Codex, etc.).
- **First user:** us — every hackathon ticket goes through it.

## Goals

- Given a ticket in Markdown, return a **readiness score (0–100)** and a list of **findings** (rule id, severity, message, location, how to fix).
- Grow by **one rule or one capability per PR**, each with its own tests.
- Deterministic and offline: same input → same output, no network, no API keys.
- Output usable by humans (text) and machines (`--json`) so MCP and CI can consume it later.

## Non-goals (for now)

- AI/LLM-based checks or ticket rewriting — a later capability, added behind an interface and mocked in tests.
- Reading tickets directly from GitHub/Jira APIs — later; v1 reads files (and stdin).
- Web UI.
- Non-English tickets.

## Anti-goals (failure even if it "works")

- **Flaky or untestable rules.** A rule whose result can't be pinned by a unit test doesn't ship.
- **Nagging noise.** A rule that fires on well-written tickets erodes trust. Every rule needs a "good ticket passes" test, not just a "bad ticket fails" test.
- **Opaque scores.** A score without findings explaining it is useless. Every point deducted must trace to a finding.
- **Secrets or personal data in the repo** (public, judged). Sample tickets are invented.

## Constraints

- Python ≥ 3.12, managed with `uv`. Tests with `pytest`. CLI with stdlib `argparse`.
- No runtime dependencies in v1 (pytest is dev-only).
- Public GitHub repo `JASHWANTHS07/ticketsmith` — this local repo (`H:\qodothon`, renamed on GitHub from `qodothon`). Project root = repo root: `pyproject.toml`, `AGENTS.md`, and `docs/evidence/` all live here. Every capability lands via a focused PR reviewed by Qodo.
- Windows dev machine; must also run on Linux (GitHub Actions later).

## Decided

**Command:**
```
ticketsmith check <ticket.md | ->
```
- `-` reads from stdin.
- `--json` is **not** in the Day 1 PR (my call). Added later as its own PR, when its shape can be designed for MCP/CI consumers.
- Exit code `0` = no error-severity findings, `1` = at least one error finding, `2` = usage/file error (argparse default for usage). Lets CI use it later with no extra work.

**Rule model:**
- A rule is a plain function `(ticket) -> list[Finding]` with a stable id (e.g. `AC001`), registered in one list. Adding a rule = one function + its tests + one registry line.
- `Finding` fields: `rule_id`, `severity` (`error` | `warning` | `info`), `message`, `line` (optional), `fix` (one-sentence suggestion).
- `ticket` = the raw text plus a lightweight parse: title (first `#` heading), sections (split at **any** heading level `##`–`######`, so GitHub issue forms using `###` work), and list items per section. Plain string handling, no Markdown library. (My call.)

**Score (my call):** start at 100; subtract 25 per error, 10 per warning, 0 per info; floor at 0. Simple, explainable, every deduction traceable to a finding. Tunable later.

**First rule — `AC001` "has acceptance criteria" (error):** passes when the ticket has a section whose heading **contains** (case-insensitive) `acceptance criteria`, `definition of done`, or `done when` — so "Acceptance Criteria (draft)" counts — containing at least one list item (`-`, `*`, `1.`, or `- [ ]`). Otherwise one error finding with a fix suggestion showing the expected section.

**Text output (example):**
```
search-speed.md — score 75/100
  ERROR AC001  No acceptance criteria section found.
               Fix: add "## Acceptance criteria" with a checklist of observable outcomes.
```

## Hackathon delivery map (first week)

| Day | Delivery |
|---|---|
| 1 | Project scaffold + `check` command + rule `AC001` + text output + tests. One PR, one Qodo review. Day 1 Discussion post. |
| 2 | `AGENTS.md`: description, setup/verify commands, 3–5 rules with where/why (incl. "every rule ships with a passing-ticket and a failing-ticket test"). |
| 3 | Write the ticket for rule `VAG001` (vague wording) — and run it through TicketSmith itself. Agent implements; compare against each acceptance criterion; record what it missed. |
| — | Bold-line sections (`**Acceptance criteria:**` without a heading) are not recognised in v1 — candidate follow-up rule refinement. |
| 4–5 | Per the released challenges (skill; docs). Candidate rules for later days: testable-criteria, scope/out-of-scope section, contradictions, ticket too large, `--json`. |

This table was checked against the released `docs/Day 1.txt`–`Day 3.txt`. The first implementation plan covers **Days 1–3 as one sequence of three PRs** (scaffold + AC001 → AGENTS.md → VAG001 via ticket), since we joined on Day 3 and must catch up. Days 4+ get planned when released.

## Left to the builder

- Module/file layout inside the package, naming of internals.
- Exact wording of messages and fix suggestions.
- Sample ticket fixtures (invented content).
- Whether text output uses color (must degrade cleanly when piped).
