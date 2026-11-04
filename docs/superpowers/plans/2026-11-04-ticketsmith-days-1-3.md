# TicketSmith Days 1–3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the hackathon catch-up: Day 1 (`ticketsmith check` + rule AC001, PR #1), Day 2 (AGENTS.md, PR #2), Day 3 (rule VAG001 built by an agent from a ticket, PR #3).

**Architecture:** Plain-Python CLI. `ticket.py` parses Markdown into title/sections/items; `rules.py` holds rule functions `(Ticket) -> list[Finding]` in a registry; `check.py` runs rules, scores, formats text; `cli.py` wires argparse and exit codes.

**Tech Stack:** Python ≥ 3.12, uv, pytest (dev only), stdlib `argparse`/`re`/`dataclasses`.

**Spec:** `docs/superpowers/specs/2026-11-04-ticketsmith-design.md`

## Global Constraints

- Python ≥ 3.12 (`requires-python = ">=3.12"`), managed with `uv`; tests via `uv run pytest`.
- No runtime dependencies; `pytest` is a dev dependency only.
- Deterministic and offline: no network, clock, or randomness in rules.
- Score: start 100; −25 per `error`, −10 per `warning`, 0 per `info`; floor 0.
- Exit codes: `0` no error findings, `1` ≥ 1 error finding, `2` usage/file error.
- Every rule ships with a passing-ticket test and a failing-ticket test.
- All sample tickets are invented; no secrets or personal data (public, judged repo).
- Must run on Windows and Linux.
- One focused PR per day's capability; each PR reviewed by Qodo.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## Review Focus

1. **Windows CRLF line endings** — a ticket saved on Windows (`\r\n`) must parse identically to `\n`. Test in Task 1.
2. **`#` lines inside fenced code blocks** (e.g. a bash comment `# install deps` in a ```` ``` ```` block) must not become title/headings/items. Test in Task 1.
3. **Criteria nested under sub-headings** (`## Acceptance criteria` → `### API` → items) must satisfy AC001, not false-fire. Test in Task 2.
4. **Missing file or non-UTF-8 file** → exit 2 with a one-line stderr message, no traceback. Test in Task 4.
5. **Empty ticket / stdin input** (`-`) — empty text yields AC001 error and score 75; stdin works like a file. Test in Tasks 3 and 4.

---

### Task 1: Base commit, scaffold, and ticket parser

**Files:**
- Create: `pyproject.toml`, `src/ticketsmith/__init__.py` (via `uv init`), `src/ticketsmith/ticket.py`
- Test: `tests/test_ticket.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Section:
      heading: str        # heading text, no leading #'s, stripped
      level: int          # 1–6
      line: int           # 1-based line number of the heading
      items: list[str]    # list-item texts directly under this heading (marker and "[ ]"/"[x]" removed)

  @dataclass(frozen=True)
  class Ticket:
      text: str
      title: str | None   # first level-1 heading, if any
      sections: list[Section]  # every heading except the title line, in order

  def parse_ticket(text: str) -> Ticket
  ```
- List item = line matching `^\s*(?:[-*]|\d+\.)\s+(?:\[[ xX]\]\s+)?(.+)$`. Lines inside ```` ``` ```` or `~~~` fences are ignored entirely.

- [ ] **Step 1: Base commit on `main`** — commit `.gitignore`, the spec, and this plan; `git push -u origin main`. Expected: `gh repo view JASHWANTHS07/ticketsmith` shows non-empty.
- [ ] **Step 2: Branch** — `git switch -c day1-ac001`.
- [ ] **Step 3: Scaffold** — `uv init --package --name ticketsmith --python 3.12 .` then set `requires-python = ">=3.12"`, add `[project.scripts] ticketsmith = "ticketsmith.cli:main"`, `uv add --dev pytest`. Delete the generated `main()` stub from `__init__.py`. Expected: `uv run pytest` runs (0 tests collected, exit 5 is fine).
- [ ] **Step 4: Write failing tests** in `tests/test_ticket.py`:
  ```python
  def test_title_and_sections():
      t = parse_ticket("# Speed up search\n\n## Context\ntext\n\n### Acceptance criteria\n- p95 < 200ms\n- [ ] cached\n1. logged\n")
      assert t.title == "Speed up search"
      assert [(s.heading, s.level, s.line) for s in t.sections] == [("Context", 2, 3), ("Acceptance criteria", 3, 6)]
      assert t.sections[1].items == ["p95 < 200ms", "cached", "logged"]

  def test_crlf_parses_same_as_lf():
      lf = "# T\n## Done when\n- a\n"
      assert parse_ticket(lf.replace("\n", "\r\n")).sections == parse_ticket(lf).sections

  def test_fenced_code_ignored():
      t = parse_ticket("# T\n```bash\n# install deps\n- not an item\n```\n## Notes\n")
      assert [s.heading for s in t.sections] == ["Notes"]

  def test_empty_text():
      t = parse_ticket("")
      assert t.title is None and t.sections == []
  ```
- [ ] **Step 5: Run** `uv run pytest tests/test_ticket.py -v` — Expected: FAIL (ImportError).
- [ ] **Step 6: Implement** `parse_ticket` in `src/ticketsmith/ticket.py` — `text.splitlines()` (handles CRLF), single pass with a fence flag.
- [ ] **Step 7: Run** `uv run pytest -v` — Expected: 4 passed.
- [ ] **Step 8: Commit** — `feat: scaffold project and add ticket parser`.

### Task 2: Finding model and rule AC001

**Files:**
- Create: `src/ticketsmith/rules.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `Ticket`, `Section`, `parse_ticket` (Task 1).
- Produces:
  ```python
  Severity = Literal["error", "warning", "info"]

  @dataclass(frozen=True)
  class Finding:
      rule_id: str
      severity: Severity
      message: str
      fix: str
      line: int | None = None

  Rule = Callable[[Ticket], list[Finding]]
  def ac001_has_acceptance_criteria(ticket: Ticket) -> list[Finding]
  RULES: list[Rule] = [ac001_has_acceptance_criteria]
  ```
- AC001 passes when a section heading contains (case-insensitive) `acceptance criteria`, `definition of done`, or `done when`, and that section **or any following section with a deeper level, up to the next section of same-or-shallower level**, has ≥ 1 item. Else one `error` finding: message `No acceptance criteria section found.` (or `Acceptance criteria section has no list items.` with `line` = heading line, when the heading exists), fix `Add "## Acceptance criteria" with a checklist of observable outcomes.`

- [ ] **Step 1: Write failing tests** in `tests/test_rules.py`:
  ```python
  def test_ac001_passes_good_ticket():                       # "## Acceptance criteria\n- x"
      assert ac001_has_acceptance_criteria(parse_ticket(GOOD)) == []
  def test_ac001_heading_variants_pass():                     # "### Definition of Done", "## Done when", "## Acceptance Criteria (draft)" each with one item
  def test_ac001_nested_subheading_items_pass():              # "## Acceptance criteria\n### API\n- 200 OK\n## Notes\n"
  def test_ac001_missing_section_fails():
      [f] = ac001_has_acceptance_criteria(parse_ticket("# T\n## Context\n- a\n"))
      assert (f.rule_id, f.severity, f.line) == ("AC001", "error", None)
  def test_ac001_empty_section_fails():
      [f] = ac001_has_acceptance_criteria(parse_ticket("# T\n## Acceptance criteria\nsome prose\n## Notes\n- a\n"))
      assert f.line == 2 and "no list items" in f.message
  def test_ac001_registered():
      assert ac001_has_acceptance_criteria in RULES
  ```
- [ ] **Step 2: Run** `uv run pytest tests/test_rules.py -v` — Expected: FAIL (ImportError).
- [ ] **Step 3: Implement** `Finding`, `ac001_has_acceptance_criteria`, `RULES` in `rules.py`.
- [ ] **Step 4: Run** `uv run pytest -v` — Expected: all passed.
- [ ] **Step 5: Commit** — `feat: add AC001 acceptance-criteria rule`.

### Task 3: Scoring, check, and text report

**Files:**
- Create: `src/ticketsmith/check.py`
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: `parse_ticket` (Task 1); `Finding`, `RULES` (Task 2).
- Produces:
  ```python
  @dataclass(frozen=True)
  class Report:
      findings: list[Finding]
      score: int

  def score(findings: list[Finding]) -> int
  def check(text: str) -> Report
  def format_text(name: str, report: Report) -> str
  ```
- `format_text` output, exactly (two-space indent, severity uppercased, fix line aligned under message; `line N` appended after rule id when present):
  ```
  search-speed.md — score 75/100
    ERROR AC001  No acceptance criteria section found.
                 Fix: Add "## Acceptance criteria" with a checklist of observable outcomes.
  ```
  With no findings: `<name> — score 100/100` then `  No findings.`

- [ ] **Step 1: Write failing tests** in `tests/test_check.py`:
  ```python
  def test_score_values():
      e = Finding("X", "error", "m", "f"); w = Finding("X", "warning", "m", "f"); i = Finding("X", "info", "m", "f")
      assert score([]) == 100 and score([e]) == 75 and score([w]) == 90 and score([i]) == 100
      assert score([e] * 5) == 0                              # floor
  def test_check_empty_text():
      r = check("")
      assert r.score == 75 and [f.rule_id for f in r.findings] == ["AC001"]
  def test_format_text_with_finding():
      assert format_text("search-speed.md", check("# T\n")) == EXPECTED   # the block above
  def test_format_text_clean():
      assert format_text("ok.md", check("# T\n## Done when\n- a\n")) == "ok.md — score 100/100\n  No findings."
  ```
- [ ] **Step 2: Run** `uv run pytest tests/test_check.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** in `check.py`.
- [ ] **Step 4: Run** `uv run pytest -v` — Expected: all passed.
- [ ] **Step 5: Commit** — `feat: add scoring and text report`.

### Task 4: CLI, README, and Day 1 ship

**Files:**
- Create: `src/ticketsmith/cli.py`, `tests/test_cli.py`, `tests/fixtures/good.md`, `tests/fixtures/no_ac.md`, `README.md`, `docs/evidence/day-1.md`
- Modify: `CLAUDE.md` (Project section: stack + commands — local only, git-ignored)

**Interfaces:**
- Consumes: `check`, `format_text` (Task 3).
- Produces: `def main(argv: list[str] | None = None) -> int` — subcommand `check <path|->`; prints `format_text` to stdout; returns 0/1 per error findings; on missing file / `UnicodeDecodeError` prints `ticketsmith: error: <reason>` to stderr and returns 2. Name shown for stdin is `<stdin>`. Read files as UTF-8 (`utf-8-sig` to tolerate BOM). Entry point calls `sys.exit(main())`.

- [ ] **Step 1: Write fixtures** — `good.md` (invented ticket with AC section, ≥2 items) and `no_ac.md` (invented ticket, no AC).
- [ ] **Step 2: Write failing tests** in `tests/test_cli.py` (use `capsys`, `monkeypatch` for stdin):
  ```python
  def test_good_ticket_exit_0(capsys):   assert main(["check", GOOD]) == 0 and "score 100/100" in capsys.readouterr().out
  def test_bad_ticket_exit_1(capsys):    assert main(["check", NO_AC]) == 1 and "AC001" in capsys.readouterr().out
  def test_missing_file_exit_2(capsys):
      assert main(["check", "nope.md"]) == 2
      err = capsys.readouterr().err
      assert err.startswith("ticketsmith: error:") and "Traceback" not in err
  def test_non_utf8_exit_2(tmp_path):    p = tmp_path / "x.md"; p.write_bytes(b"\xff\xfe\x00bad"); assert main(["check", str(p)]) == 2
  def test_stdin(monkeypatch, capsys):   monkeypatch.setattr("sys.stdin", io.StringIO("# T\n")); assert main(["check", "-"]) == 1 and "<stdin>" in capsys.readouterr().out
  ```
- [ ] **Step 3: Run** `uv run pytest tests/test_cli.py -v` — Expected: FAIL.
- [ ] **Step 4: Implement** `main` in `cli.py`.
- [ ] **Step 5: Run** `uv run pytest -v` — Expected: all passed. Then `uv run ticketsmith check tests/fixtures/no_ac.md; echo $?` — Expected: report with AC001, exit `1`.
- [ ] **Step 6: README.md** — what it is (2 sentences), install/run (`uv sync`, `uv run ticketsmith check <file>`), test (`uv run pytest`), rules table (AC001), "Built for the Qodo Hackathon" line disclosing AI assistance (Claude Code, Qodo).
- [ ] **Step 7: Update CLAUDE.md Project section** with stack, commands (`uv run pytest`, `uv run pytest tests/test_rules.py::test_name -v`, `uv run ticketsmith check <file>`), and the module map (ticket → rules → check → cli).
- [ ] **Step 8: Commit** — `feat: add check CLI and README`.
- [ ] **Step 9: Push and open PR** — `git push -u origin day1-ac001`; `gh pr create` titled `Day 1: ticketsmith check + AC001`. Body: what, how to run, test output.
- [ ] **Step 10: Qodo review** — user confirms Qodo is installed on the repo; trigger review (Qodo comments on PR; if not automatic, comment `/review` on the PR). Wait for findings.
- [ ] **Step 11: Evidence** — `docs/evidence/day-1.md`: capability, PR link, terminal demo output (good + bad ticket), Qodo findings classified useful / questioned / missed, one lesson. Commit to the PR branch, address any confirmed Qodo findings, merge after user approval.
- [ ] **Step 12: Draft Day 1 Discussion post** for the user (purpose, repo/PR link, demo output, one lesson). User posts it.

### Task 5: AGENTS.md (Day 2)

**Files:**
- Create: `AGENTS.md`, `docs/evidence/day-2.md`

**Interfaces:**
- Consumes: commands from Task 4.

- [ ] **Step 1: Branch** `day2-agents-md` from updated `main`.
- [ ] **Step 2: Draft AGENTS.md with the user** — project description; setup (`uv sync`) and verify (`uv run pytest`, `uv run ticketsmith check tests/fixtures/good.md`) commands; 3–5 rules, each with *where it applies* and *why*. Candidates (user picks/edits): (a) every rule ships a passing-ticket and a failing-ticket test — `tests/test_rules.py` — prevents nagging noise; (b) rules are deterministic: no network, clock, randomness — `src/ticketsmith/rules.py` — same ticket must give same score in CI; (c) every score deduction maps to a `Finding` with a `fix` — `rules.py`/`check.py` — opaque scores are useless; (d) no runtime dependencies without a written reason in the PR — `pyproject.toml` — keeps install trivial; (e) sample tickets are invented — `tests/fixtures/` — public, judged repo.
- [ ] **Step 3: Self-check** — `uv run pytest` still passes; AGENTS.md contains no persona workflow (that stays in CLAUDE.md).
- [ ] **Step 4: Commit, push, PR** `Day 2: AGENTS.md house rules`.
- [ ] **Step 5: Qodo standards** — user checks Qodo → Review Standards shows the rules; if missing, use "Import rules and skills". Screenshot for evidence.
- [ ] **Step 6: Evidence** `docs/evidence/day-2.md` (rules, import screenshot note, Qodo review notes); merge after user approval.
- [ ] **Step 7: Draft Day 2 Discussion post** — AGENTS.md link, quoted most-opinionated rule (user's choice) with its name and story.

### Task 6: VAG001 from a ticket (Day 3)

**Files:**
- Create: `docs/tickets/VAG001-vague-wording.md`, `docs/evidence/day-3.md`
- Modified by the implementing agent: `src/ticketsmith/rules.py`, `tests/test_rules.py`, `README.md`

**Interfaces:**
- Consumes: `Ticket`, `Finding`, `RULES` (Tasks 1–2).
- Produces (decided in the ticket, not here): `vag001_*` rule registered in `RULES`.

- [ ] **Step 1: Branch** `day3-vag001`.
- [ ] **Step 2: Write the ticket with the user** — rule VAG001 flags vague words in acceptance-criteria items (severity `warning`), with a concrete definition of done: exact word list, where it looks (AC items only vs whole ticket), case/whole-word matching, one finding per item vs per word, message/fix copy, required passing and failing tests.
- [ ] **Step 3: Dogfood** — `uv run ticketsmith check docs/tickets/VAG001-vague-wording.md` must exit 0 (score 100). If not, fix the ticket. Save the output for evidence.
- [ ] **Step 4: Hand off** — dispatch a fresh agent given only the ticket path and AGENTS.md; it implements on the branch and commits.
- [ ] **Step 5: Compare** — check the result against **every** acceptance criterion one by one (met / partially / missed), run `uv run pytest -v`. Record misses before fixing anything.
- [ ] **Step 6: Push, PR** `Day 3: VAG001 vague-wording rule (agent-built from ticket)`; Qodo review.
- [ ] **Step 7: Evidence** `docs/evidence/day-3.md` — ticket link, dogfood output, criterion-by-criterion table, what the agent missed, what Qodo caught/missed; then fix misses in follow-up commits; merge after user approval.
- [ ] **Step 8: Draft Day 3 Discussion post** — ticket + PR + what the agent missed.
