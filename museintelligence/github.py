"""TOOL-GH-01 (COMMIT_ANCHOR_VERIFIER) facade.

All GitHub reads in the app go through the vendored implementation
in tools/github_call.py. This module only re-exports its operations
so the rest of the app has one import point; it adds no network call
of its own. Invariant: commit_sha is the anchor; branch names are
not. Branch names (main, master, HEAD) and short SHAs are refused
before any network call.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_tool():
    """Load tools/github_call.py as a module (it lives outside the
    package so it can also run standalone)."""
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "tools" / "github_call.py",
        Path.home() / "workspace" / "notes" / "tools" / "github_call.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location(
                "museintelligence_github_call", candidate)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules["museintelligence_github_call"] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError(
        "tools/github_call.py not found (looked in the app tools/ "
        "directory and ~/workspace/notes/tools/)")


_tool = _load_tool()

# Re-exported TOOL-GH-01 operations (same names, same behaviour).
is_pinned_sha = _tool.is_pinned_sha
pin_commit_sha = _tool.pin_commit_sha
verify_ref = _tool.verify_ref
fetch_bytes_at_sha = _tool.fetch_bytes_at_sha
hash_bytes = _tool.hash_bytes
self_test = _tool.self_test


class GitHubAnchor:
    """A TOOL-GH-01 client bound to one repository (owner/name).

    Every read is pinned: pin() resolves a tag (or an already-pinned
    SHA) to its 40-hex commit SHA first; fetch() only ever runs at
    that pinned SHA.
    """

    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.pinned_sha: str | None = None

    def pin(self, ref: str) -> str:
        """Resolve ``ref`` to its commit SHA and remember it."""
        self.pinned_sha = pin_commit_sha(self.repo, ref)
        return self.pinned_sha

    def verify(self, ref: str, expected_sha: str | None = None) -> str:
        """Resolve ``ref``; if ``expected_sha`` is given, raise
        ValueError when the resolved SHA differs."""
        return verify_ref(self.repo, ref, expected_sha)

    def fetch(self, path: str, sha: str | None = None) -> bytes:
        """Fetch a file at a pinned SHA (defaults to the SHA pinned
        by pin()). Branch names are refused."""
        target = sha if sha is not None else self.pinned_sha
        if target is None:
            raise ValueError(
                "no pinned SHA: call pin() first, or pass a 40-hex "
                "commit SHA")
        return fetch_bytes_at_sha(self.repo, target, path)

    def digest(self, data: bytes) -> str:
        """SHA-256 hex digest of bytes."""
        return hash_bytes(data)
