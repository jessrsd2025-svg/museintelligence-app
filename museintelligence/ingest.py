"""Document ingest (TOOL-OSINT-DOC-01 surface).

Accepts .md / .txt / .json sources. Every ingested source is
registered with its source_id, source_locator and UTC
retrieval_timestamp; anything missing one of the three is refused
with INCOMPLETE_PROVENANCE and is the caller's responsibility to
route to quarantine. Ingested bytes are stored under the documents
directory and their SHA-256 is recorded on the source record.

PDF text extraction is NOT implemented: this module refuses .pdf
with a clear message instead of silently producing partial text.
"""

from __future__ import annotations

import json
from pathlib import Path

from .provenance import (
    IncompleteProvenanceError,
    SourceRecord,
    SourceRegistry,
    sha256_hex,
)

SUPPORTED_SUFFIXES = {".md", ".txt", ".json"}


class UnsupportedSourceError(ValueError):
    """The source file type cannot be ingested by this module."""


def _check_provenance(source_id: str, source_locator: str,
                      retrieval_timestamp: str) -> None:
    record = SourceRecord(source_id=source_id,
                          source_locator=source_locator,
                          retrieval_timestamp=retrieval_timestamp)
    missing = record.validate()
    if missing:
        raise IncompleteProvenanceError(
            "INCOMPLETE_PROVENANCE: cannot ingest source "
            f"{source_id or '<no id>'} — missing "
            + ", ".join(missing))


def ingest_file(path: str | Path, *, source_id: str, source_locator: str,
                retrieval_timestamp: str, kind: str = "document",
                registry: SourceRegistry | None = None,
                documents_dir: str | Path | None = None) -> SourceRecord:
    """Ingest a file and register its provenance.

    Returns the registered SourceRecord (with the content SHA-256).
    Raises IncompleteProvenanceError for missing provenance fields,
    UnsupportedSourceError for .pdf and other unsupported types, and
    ValueError for invalid JSON or a duplicate source_id.
    """
    _check_provenance(source_id, source_locator, retrieval_timestamp)
    src = Path(path)
    if not src.is_file():
        raise ValueError(f"no such file: {src}")
    suffix = src.suffix.lower()
    if suffix == ".pdf":
        raise UnsupportedSourceError(
            "PDF text extraction is not implemented in this version; "
            "convert the PDF to .md or .txt first, then ingest it")
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedSourceError(
            f"unsupported source type {suffix!r}; supported types are "
            + ", ".join(sorted(SUPPORTED_SUFFIXES)))
    data = src.read_bytes()
    if suffix == ".json":
        try:
            json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"{src} is not valid JSON: {exc}") from exc
    digest = sha256_hex(data)
    record = SourceRecord(source_id=source_id,
                          source_locator=source_locator,
                          retrieval_timestamp=retrieval_timestamp,
                          kind=kind)
    if registry is not None:
        record = registry.register(record, content_sha256=digest)
    else:
        record = SourceRecord(
            source_id=record.source_id,
            source_locator=record.source_locator,
            retrieval_timestamp=record.retrieval_timestamp,
            kind=record.kind,
            human_reviewed=record.human_reviewed,
            sha256=digest)
    if documents_dir is not None:
        target_dir = Path(documents_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{source_id}{suffix}"
        target.write_bytes(data)
    return record


def ingest_text(text: str, *, source_id: str, source_locator: str,
                retrieval_timestamp: str, kind: str = "document",
                registry: SourceRegistry | None = None,
                documents_dir: str | Path | None = None) -> SourceRecord:
    """Ingest in-memory text as a .md source (same provenance rules
    as ingest_file)."""
    _check_provenance(source_id, source_locator, retrieval_timestamp)
    data = text.encode("utf-8")
    digest = sha256_hex(data)
    record = SourceRecord(source_id=source_id,
                          source_locator=source_locator,
                          retrieval_timestamp=retrieval_timestamp,
                          kind=kind)
    if registry is not None:
        record = registry.register(record, content_sha256=digest)
    else:
        record = SourceRecord(
            source_id=record.source_id,
            source_locator=record.source_locator,
            retrieval_timestamp=record.retrieval_timestamp,
            kind=record.kind,
            human_reviewed=record.human_reviewed,
            sha256=digest)
    if documents_dir is not None:
        target_dir = Path(documents_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"{source_id}.md").write_bytes(data)
    return record
