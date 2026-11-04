"""Command-line entry point: ticketsmith check <ticket.md | ->."""

import argparse
import sys

from ticketsmith.check import check, format_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ticketsmith", description="Check how ready a ticket is for an AI coding agent."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check_cmd = commands.add_parser("check", help="check one ticket")
    check_cmd.add_argument("ticket", help="path to a Markdown ticket, or - for stdin")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit:  # argparse exits on usage errors and --help
        return int(exit.code or 0)

    try:
        if args.ticket == "-":
            name, text = "<stdin>", sys.stdin.read()
        else:
            name = args.ticket
            with open(args.ticket, encoding="utf-8-sig") as file:
                text = file.read()
    except (OSError, UnicodeDecodeError) as error:
        print(f"ticketsmith: error: cannot read {args.ticket}: {error}", file=sys.stderr)
        return 2

    report = check(text)
    print(format_text(name, report))
    return 1 if any(f.severity == "error" for f in report.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
