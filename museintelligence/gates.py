"""18-gate acceptance checklist runner (AGENTS.md, ICD203 pp. 33-35).

Runs the vendored linter (tools/aequitas_gate_linter.py) over a
path and reports PASS / FAIL / MANUAL per gate. Gates D2 (context
vs. authorization separation) and E3 (human sign-off) are MANUAL by
design and are confirmed by a human, not by the scan.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

GATE_IDS = tuple(
    [f"A{i}" for i in range(1, 5)]
    + [f"B{i}" for i in range(1, 5)]
    + [f"C{i}" for i in range(1, 5)]
    + [f"D{i}" for i in range(1, 4)]
    + [f"E{i}" for i in range(1, 4)]
)


@dataclass
class GateResult:
    gate: str
    name: str
    status: str  # PASS, FAIL, or MANUAL
    note: str = ""
    findings: list[str] = field(default_factory=list)


@dataclass
class GateRun:
    results: list[GateResult]
    passed: int
    failed: int
    manual: int
    exit_code: int
    root: str = ""

    @property
    def total(self) -> int:
        return len(self.results)

    def summary_line(self) -> str:
        return (f"{self.passed} passed, {self.failed} failed, "
                f"{self.manual} manual — {self.total} gates total")


def find_linter() -> Path:
    """Locate tools/aequitas_gate_linter.py (app copy first, then
    the notes copy)."""
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "tools" / "aequitas_gate_linter.py",
        Path.home() / "workspace" / "notes" / "tools"
        / "aequitas_gate_linter.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "aequitas_gate_linter.py not found (looked in the app tools/ "
        "directory and ~/workspace/notes/tools/)")


def run_linter(path: str | Path, strict: bool = False,
               timeout: int = 300) -> GateRun:
    """Run the 18-gate linter over ``path`` and parse its --json
    output. ``strict`` treats MANUAL gates as failures."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    linter = find_linter()
    command = [sys.executable, str(linter), str(root), "--json"]
    if strict:
        command.append("--strict")
    proc = subprocess.run(command, capture_output=True, text=True,
                          timeout=timeout)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "linter produced unparseable --json output: "
            f"{exc}\nstdout: {proc.stdout[:500]}"
            f"\nstderr: {proc.stderr[:500]}") from exc
    results = [
        GateResult(gate=item.get("gate", "?"),
                   name=item.get("name", ""),
                   status=item.get("status", "?"),
                   note=item.get("note", ""),
                   findings=list(item.get("findings", [])))
        for item in payload.get("gates", [])
    ]
    summary = payload.get("summary", {})
    return GateRun(
        results=results,
        passed=int(summary.get("pass", 0)),
        failed=int(summary.get("fail", 0)),
        manual=int(summary.get("manual", 0)),
        exit_code=proc.returncode,
        root=str(payload.get("root", root)),
    )
