import io
from pathlib import Path

from ticketsmith.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = str(FIXTURES / "good.md")
NO_AC = str(FIXTURES / "no_ac.md")


def test_good_ticket_exit_0(capsys):
    assert main(["check", GOOD]) == 0
    assert "score 100/100" in capsys.readouterr().out


def test_bad_ticket_exit_1(capsys):
    assert main(["check", NO_AC]) == 1
    assert "AC001" in capsys.readouterr().out


def test_missing_file_exit_2(capsys):
    assert main(["check", "nope.md"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("ticketsmith: error:")
    assert "Traceback" not in err


def test_non_utf8_exit_2(tmp_path, capsys):
    p = tmp_path / "x.md"
    p.write_bytes(b"\xff\xfe\x00bad")
    assert main(["check", str(p)]) == 2
    assert capsys.readouterr().err.startswith("ticketsmith: error:")


def test_utf8_bom_tolerated(tmp_path, capsys):
    p = tmp_path / "bom.md"
    p.write_bytes("﻿# T\n## Done when\n- a\n".encode("utf-8"))
    assert main(["check", str(p)]) == 0


def test_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("# T\n"))
    assert main(["check", "-"]) == 1
    assert "<stdin>" in capsys.readouterr().out


def test_no_subcommand_exit_2(capsys):
    assert main([]) == 2
