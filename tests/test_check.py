from ticketsmith.check import check, format_text, score
from ticketsmith.rules import Finding

ERROR = Finding("X", "error", "m", "f")
WARNING = Finding("X", "warning", "m", "f")
INFO = Finding("X", "info", "m", "f")


def test_score_values():
    assert score([]) == 100
    assert score([ERROR]) == 75
    assert score([WARNING]) == 90
    assert score([INFO]) == 100
    assert score([ERROR, WARNING]) == 65


def test_score_floors_at_zero():
    assert score([ERROR] * 5) == 0


def test_check_empty_text():
    r = check("")
    assert r.score == 75
    assert [f.rule_id for f in r.findings] == ["AC001"]


def test_format_text_with_finding():
    assert format_text("search-speed.md", check("# T\n")) == (
        "search-speed.md - score 75/100\n"
        "  ERROR AC001  No acceptance criteria section found.\n"
        '               Fix: Add "## Acceptance criteria" with a checklist of observable outcomes.'
    )


def test_format_text_includes_line_when_present():
    out = format_text("t.md", check("# T\n## Acceptance criteria\nprose\n"))
    assert "  ERROR AC001 line 2  Acceptance criteria section has no list items.\n" in out


def test_format_text_clean():
    assert format_text("ok.md", check("# T\n## Done when\n- a\n")) == "ok.md - score 100/100\n  No findings."
