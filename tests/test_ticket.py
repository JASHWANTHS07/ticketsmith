from ticketsmith.ticket import parse_ticket


def test_title_and_sections():
    t = parse_ticket(
        "# Speed up search\n\n## Context\ntext\n\n### Acceptance criteria\n"
        "- p95 < 200ms\n- [ ] cached\n1. logged\n"
    )
    assert t.title == "Speed up search"
    assert [(s.heading, s.level, s.line) for s in t.sections] == [
        ("Context", 2, 3),
        ("Acceptance criteria", 3, 6),
    ]
    assert t.sections[1].items == ["p95 < 200ms", "cached", "logged"]


def test_crlf_parses_same_as_lf():
    lf = "# T\n## Done when\n- a\n"
    assert parse_ticket(lf.replace("\n", "\r\n")).sections == parse_ticket(lf).sections


def test_fenced_code_ignored():
    t = parse_ticket("# T\n```bash\n# install deps\n- not an item\n```\n## Notes\n")
    assert t.title == "T"
    assert [s.heading for s in t.sections] == ["Notes"]
    assert t.sections[0].items == []


def test_empty_text():
    t = parse_ticket("")
    assert t.title is None and t.sections == []
