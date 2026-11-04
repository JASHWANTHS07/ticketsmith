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


def test_inner_backtick_fence_does_not_close_tilde_fence():
    t = parse_ticket("# T\n~~~\n```\n## Acceptance criteria\n- a\n~~~\n")
    assert t.sections == []


def test_longer_fence_shows_markdown_example():
    t = parse_ticket("# T\n````md\n```\n## fake\n```\n````\n## Real\n")
    assert [s.heading for s in t.sections] == ["Real"]


def test_empty_and_bare_checkbox_items_skipped():
    t = parse_ticket("# T\n## Done when\n- [ ]\n-   \n- [x] real\n")
    assert t.sections[0].items == ["real"]
