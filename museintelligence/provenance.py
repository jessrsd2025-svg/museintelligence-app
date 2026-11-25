"""Provenance registry: every source object carries an immutable
identifier, a stable locator, and a UTC retrieval timestamp.

A payload lacking any of the three is INCOMPLETE_PROVENANCE and is
refused here; callers route it to the quarantine store instead of
promoting it. Nothing in this module ever assigns VERIFIED_FACT:
claims stay SOURCE_REPORTED (or GENERATED_ANALYSIS) until a human
reviews the source.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROVENANCE_FIELDS = ("source_id", "source_locator", "retrieval_timestamp")

# A source_id is a short token of letters, digits, dashes and
# underscores; it is also used as a file stem under data/documents/.
_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class IncompleteProvenanceError(ValueError):
    """A source object is missing a provenance field.

    The caller must route the payload to quarantine with the
    INCOMPLETE_PROVENANCE trigger instead of registering it.
    """


def parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and require it to be UTC.

    Raises ValueError for anything unparseable or not UTC.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("retrieval_timestamp must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            f"retrieval_timestamp {value!r} is not a valid ISO-8601 "
            "timestamp") from None
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(
            f"retrieval_timestamp {value!r} is not UTC")
    return parsed


def canonical_json(obj) -> str:
    """RFC 8785-style deterministic JSON: sorted keys, tight
    separators, no ASCII escaping. Hashing always runs over this form.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj) -> str:
    """SHA-256 of the canonical JSON form of a JSON value."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))


@dataclass(frozen=True)
class SourceRecord:
    """One registered source object.

    ``sha256`` is the digest of the ingested content bytes, filled in
    by the registry at registration time.
    """

    source_id: str
    source_locator: str
    retrieval_timestamp: str
    kind: str = "document"
    human_reviewed: bool = False
    sha256: str = ""

    def validate(self) -> list[str]:
        """Return the names of missing or invalid provenance fields
        (empty list means the record is complete)."""
        missing: list[str] = []
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            missing.append("source_id")
        elif not _SOURCE_ID_RE.match(self.source_id):
            missing.append("source_id (invalid characters)")
        if (not isinstance(self.source_locator, str)
                or not self.source_locator.strip()):
            missing.append("source_locator")
        try:
            parse_utc_timestamp(self.retrieval_timestamp)
        except ValueError:
            missing.append("retrieval_timestamp")
        return missing

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_locator": self.source_locator,
            "retrieval_timestamp": self.retrieval_timestamp,
            "kind": self.kind,
            "human_reviewed": self.human_reviewed,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourceRecord":
        return cls(
            source_id=data.get("source_id", ""),
            source_locator=data.get("source_locator", ""),
            retrieval_timestamp=data.get("retrieval_timestamp", ""),
            kind=data.get("kind", "document"),
            human_reviewed=bool(data.get("human_reviewed", False)),
            sha256=data.get("sha256", ""),
        )


class SourceRegistry:
    """The registry of source objects, persisted as JSON.

    Registration is all-or-nothing: a record with incomplete
    provenance raises IncompleteProvenanceError and is not stored,
    and a duplicate source_id raises ValueError.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: dict[str, SourceRecord] = {}
        if self.path is not None and self.path.exists():
            self.load()

    def register(self, record: SourceRecord,
                 content_sha256: str = "") -> SourceRecord:
        """Validate and store a record; returns the stored record
        (with its content digest filled in)."""
        missing = record.validate()
        if missing:
            raise IncompleteProvenanceError(
                "INCOMPLETE_PROVENANCE: source object "
                f"{record.source_id or '<no id>'} is missing "
                + ", ".join(missing))
        if record.source_id in self._records:
            raise ValueError(
                f"duplicate source_id {record.source_id!r} already "
                "registered")
        stored = SourceRecord(
            source_id=record.source_id,
            source_locator=record.source_locator,
            retrieval_timestamp=record.retrieval_timestamp,
            kind=record.kind,
            human_reviewed=record.human_reviewed,
            sha256=content_sha256,
        )
        self._records[stored.source_id] = stored
        return stored

    def get(self, source_id: str) -> SourceRecord | None:
        return self._records.get(source_id)

    def all(self) -> list[SourceRecord]:
        return [self._records[key] for key in sorted(self._records)]

    def __len__(self) -> int:
        return len(self._records)

    def save(self, path: Path | None = None) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to save the registry to")
        payload = {"sources": [r.to_dict() for r in self.all()]}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True,
                       ensure_ascii=False) + "\n", encoding="utf-8")
        self.path = target
        return target

    def load(self, path: Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to load the registry from")
        data = json.loads(target.read_text(encoding="utf-8"))
        self._records = {}
        for item in data.get("sources", []):
            record = SourceRecord.from_dict(item)
            missing = record.validate()
            if missing:
                raise IncompleteProvenanceError(
                    "INCOMPLETE_PROVENANCE in stored registry "
                    f"{target}: {record.source_id or '<no id>'} missing "
                    + ", ".join(missing))
            if record.source_id in self._records:
                raise ValueError(
                    f"duplicate source_id {record.source_id!r} in "
                    f"stored registry {target}")
            self._records[record.source_id] = record
        self.path = target


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string ending in Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
