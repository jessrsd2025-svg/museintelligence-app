"""Command-line entry point.

Usage:
    python3 -m museintelligence --serve [--host 127.0.0.1] [--port 8000]
    python3 -m museintelligence --check <path>
    python3 -m museintelligence --version
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, gates as gates_mod
from . import server as server_mod


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="museintelligence",
        description="MuseIntelligence ICD203 — reading-room and "
                    "governance app.")
    parser.add_argument("--serve", action="store_true",
                        help="start the web UI")
    parser.add_argument("--host", default="127.0.0.1",
                        help="host for --serve (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000,
                        help="port for --serve (default 8000)")
    parser.add_argument("--check", metavar="PATH",
                        help="run the 18-gate checklist over PATH and "
                             "print the results")
    parser.add_argument("--strict", action="store_true",
                        help="with --check, treat MANUAL gates as "
                             "failures")
    parser.add_argument("--version", action="store_true",
                        help="print the app version")
    args = parser.parse_args(argv)

    if args.version:
        print(f"museintelligence {__version__}")
        return 0

    if args.check:
        try:
            run = gates_mod.run_linter(args.check, strict=args.strict)
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for result in run.results:
            mark = {"PASS": "✓", "FAIL": "✗", "MANUAL": "?"}.get(
                result.status, "?")
            print(f"[{mark}] {result.gate} {result.name}: {result.status}")
            if result.note:
                print(f"      {result.note}")
            for finding in result.findings:
                print(f"      {finding}")
        print(f"\n{run.summary_line()}")
        return run.exit_code

    if args.serve:
        server_mod.serve(_repo_root(), host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
