"""Command line entry: python -m fci FILE.csv [--format text|md]."""

from __future__ import annotations

import argparse
import sys

from .index import analyze, format_markdown, format_text, read_systems


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns 0 on success, 1 on bad input."""
    parser = argparse.ArgumentParser(prog="fci", description="Facility Condition Index report")
    parser.add_argument("file")
    parser.add_argument("--format", choices=["text", "md"], default="text")
    args = parser.parse_args(argv)
    try:
        results = analyze(read_systems(args.file))
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if not results:
        print("Error: no rows in input", file=sys.stderr)
        return 1
    print(format_markdown(results) if args.format == "md" else format_text(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
