import pytest

from ticketsmith.rules import RULES, ac001_has_acceptance_criteria
from ticketsmith.ticket import parse_ticket


def ac001(text: str):
    return ac001_has_acceptance_criteria(parse_ticket(text))


def test_ac001_passes_good_ticket():
    assert ac001("# T\n## Acceptance criteria\n- x\n") == []


@pytest.mark.parametrize(
    "heading",
    ["### Definition of Done", "## Done when", "## Acceptance Criteria (draft)"],
)
def test_ac001_heading_variants_pass(heading):
    assert ac001(f"# T\n{heading}\n- x\n") == []


def test_ac001_nested_subheading_items_pass():
    assert ac001("# T\n## Acceptance criteria\n### API\n- 200 OK\n## Notes\n") == []


def test_ac001_items_in_later_sibling_section_do_not_count():
    [f] = ac001("# T\n## Acceptance criteria\n## Notes\n- a\n")
    assert f.line == 2


def test_ac001_missing_section_fails():
    [f] = ac001("# T\n## Context\n- a\n")
    assert (f.rule_id, f.severity, f.line) == ("AC001", "error", None)
    assert f.message == "No acceptance criteria section found."
    assert f.fix == 'Add "## Acceptance criteria" with a checklist of observable outcomes.'


def test_ac001_empty_section_fails():
    [f] = ac001("# T\n## Acceptance criteria\nsome prose\n## Notes\n- a\n")
    assert (f.rule_id, f.severity, f.line) == ("AC001", "error", 2)
    assert "no list items" in f.message


def test_ac001_registered():
    assert ac001_has_acceptance_criteria in RULES
