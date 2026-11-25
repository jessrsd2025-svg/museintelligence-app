#!/usr/bin/env python3
"""TOOL-GH-01 (COMMIT_ANCHOR_VERIFIER) — pinned GitHub reads.

Permitted operations: pin_commit_sha, verify_ref, fetch_bytes_at_sha,
hash. Prohibited: fetch_from_unpinned_ref, trust_branch_HEAD.
Invariant: "commit_sha is the anchor; branch names are not."

Every fetch is made at a 40-hex commit SHA resolved first by
pin_commit_sha. fetch_bytes_at_sha refuses anything that is not
exactly 40 hex characters (branch names, HEAD, short SHAs) before
any network call is made. The CLI additionally refuses branch refs
(main, master, HEAD) outright — use a tag or a 40-hex SHA instead.

Reads are unauthenticated against the public GitHub API
(api.github.com). If GITHUB_TOKEN is set in the environment it is
sent as a Bearer token to raise the rate limit; it is never
required and never printed.

Usage:
    python3 github_call.py --repo owner/name --ref <ref> --path <file>
        [--out <file>] [--show-sha] [--self-test]

    Normal run: pin the ref, fetch the file at the pinned SHA, print
    the pinned SHA, byte length, and SHA-256. --out writes the bytes.
    --show-sha with no --path pins the ref and prints only the SHA.
    --self-test runs offline checks only and exits 0 only if all pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.github.com"
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
BRANCH_REFS = {"main", "master", "head"}

USER_AGENT = "museintelligence-gh-01/1.0 (TOOL-GH-01)"


def is_pinned_sha(value) -> bool:
    """True only for a 40-hex commit SHA. Branch names, HEAD, and
    short SHAs are not pinned SHAs."""
    return isinstance(value, str) and _SHA_RE.match(value) is not None


def _headers(accept: str) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _read_url(url: str, accept: str) -> bytes:
    request = urllib.request.Request(url, headers=_headers(accept))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # aequitas: allow-network
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            detail = ""
        raise RuntimeError(
            f"GitHub API request failed: HTTP {exc.code} for {url}"
            + (f" — {detail}" if detail else "")) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc.reason} "
                           f"for {url}") from exc


def _check_repo(repo: str) -> None:
    if not isinstance(repo, str) or not _REPO_RE.match(repo):
        raise ValueError(
            f"invalid repo {repo!r}: expected 'owner/name'")


def pin_commit_sha(repo: str, ref: str) -> str:
    """Resolve a ref (tag or commit SHA) to its 40-hex commit SHA via
    the public GitHub API. Returns the pinned SHA."""
    _check_repo(repo)
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("ref must be a non-empty string")
    url = (f"{API_BASE}/repos/{repo}/commits/"
           f"{urllib.parse.quote(ref, safe='')}")
    try:
        payload = json.loads(_read_url(
            url, "application/vnd.github+json").decode("utf-8"))
    except RuntimeError:
        raise
    sha = payload.get("sha") if isinstance(payload, dict) else None
    if not is_pinned_sha(sha):
        raise RuntimeError(
            f"GitHub API returned an unexpected sha for {repo}@{ref}: "
            f"{sha!r}")
    return sha.lower()


def verify_ref(repo: str, ref: str, expected_sha: str | None = None) -> str:
    """Resolve a ref to its commit SHA; if expected_sha is given,
    raise ValueError when the resolved SHA differs. Returns the
    resolved SHA."""
    sha = pin_commit_sha(repo, ref)
    if expected_sha is not None:
        if not is_pinned_sha(expected_sha):
            raise ValueError(
                f"expected_sha {expected_sha!r} is not a 40-hex commit SHA")
        if sha.lower() != expected_sha.lower():
            raise ValueError(
                f"ref {ref!r} resolves to {sha}, expected {expected_sha}")
    return sha


def fetch_bytes_at_sha(repo: str, sha: str, path: str) -> bytes:
    """Fetch the raw bytes of a file at a pinned commit SHA. Refuses
    anything that is not exactly 40 hex characters — branch names,
    HEAD, and short SHAs are rejected before any network call."""
    _check_repo(repo)
    if not is_pinned_sha(sha):
        raise ValueError(
            f"refusing unpinned ref {sha!r}: fetch_bytes_at_sha requires "
            "a 40-hex commit SHA; branch names are not anchors")
    if (not isinstance(path, str) or not path.strip()
            or path.startswith("/") or ".." in path.split("/")):
        raise ValueError(f"invalid path {path!r}")
    url = (f"{API_BASE}/repos/{repo}/contents/"
           f"{urllib.parse.quote(path, safe='/')}"
           f"?ref={sha.lower()}")
    return _read_url(url, "application/vnd.github.raw")


def hash_bytes(data: bytes) -> str:
    """SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def self_test() -> int:
    """Offline checks only — no network calls are made."""
    failures: list[str] = []

    def check(name: str, fn) -> None:
        try:
            fn()
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
        except Exception as exc:  # noqa: BLE001 — report, don't crash
            failures.append(f"{name}: unexpected {type(exc).__name__}: {exc}")

    def expect_refusal(value: str) -> None:
        def run() -> None:
            try:
                fetch_bytes_at_sha("psf/requests", value, "LICENSE")
            except ValueError:
                return
            raise AssertionError(
                f"fetch_bytes_at_sha accepted {value!r} instead of "
                "refusing it")
        check(f"refuse {value!r}", run)

    for bad in ("main", "HEAD", "abc123",
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"):
        expect_refusal(bad)

    def hash_check() -> None:
        got = hash_bytes(b"abc")
        want = ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f"
                "20015ad")
        assert got == want, f"hash_bytes(b'abc') = {got}, expected {want}"
    check("hash_bytes(b'abc')", hash_check)

    def pinned_shape() -> None:
        assert is_pinned_sha("a" * 40)
        assert is_pinned_sha("A" * 40)
        assert not is_pinned_sha("main")
        assert not is_pinned_sha("a" * 39)
        assert not is_pinned_sha("a" * 41)
        assert not is_pinned_sha("")
        assert not is_pinned_sha(None)
    check("is_pinned_sha shapes", pinned_shape)

    def repo_shape() -> None:
        try:
            pin_commit_sha("not-a-repo", "v1")
        except ValueError:
            return
        raise AssertionError("pin_commit_sha accepted a malformed repo")
    check("pin_commit_sha rejects malformed repo", repo_shape)

    if failures:
        print("self-test FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("self-test passed (offline checks only, no network used)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TOOL-GH-01 (COMMIT_ANCHOR_VERIFIER): pin a ref to a "
                    "commit SHA and fetch a file at that SHA from the "
                    "public GitHub API. Branch names are refused; the "
                    "commit SHA is the anchor.")
    parser.add_argument("--repo", help="repository as owner/name")
    parser.add_argument("--ref",
                        help="tag or 40-hex commit SHA to pin "
                             "(branch names main/master/HEAD are refused)")
    parser.add_argument("--path", help="file path inside the repository")
    parser.add_argument("--out", help="write the fetched bytes to this file")
    parser.add_argument("--show-sha", action="store_true",
                        help="pin the ref and print only the SHA "
                             "(no fetch; --path not required)")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks only")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.repo or not args.ref:
        print("error: --repo and --ref are required (or use --self-test)",
              file=sys.stderr)
        return 2
    if args.ref.lower() in BRANCH_REFS:
        print(f"error: refusing branch ref {args.ref!r}: branch names are "
              "not anchors (TOOL-GH-01) — use a tag or a 40-hex commit SHA",
              file=sys.stderr)
        return 1
    if not args.show_sha and not args.path:
        print("error: --path is required unless --show-sha is given",
              file=sys.stderr)
        return 2

    try:
        sha = pin_commit_sha(args.repo, args.ref)
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.show_sha and not args.path:
        print(sha)
        return 0

    try:
        data = fetch_bytes_at_sha(args.repo, sha, args.path)
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    digest = hash_bytes(data)
    print(f"repo: {args.repo}")
    print(f"ref: {args.ref}")
    print(f"pinned_sha: {sha}")
    print(f"path: {args.path}")
    print(f"bytes: {len(data)}")
    print(f"sha256: {digest}")
    if args.out:
        try:
            Path(args.out).write_bytes(data)
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
            return 1
        print(f"wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
