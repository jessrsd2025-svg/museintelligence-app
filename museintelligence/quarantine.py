"""Quarantine store: non-evidentiary claims are held out of the
verified record, shown with their provenance, and never promoted
without human review.

Quarantine is where the interdiction triggers send a claim:
INCOMPLETE_PROVENANCE, SIMILARITY_IS_NOT_CORROBORATION,
MARKET_SIGNAL_IS_NOT_EVENT_EVIDENCE,
GENERATED_SUMMARY_IS_NOT_SOURCE_EVIDENCE,
PROHIBITED_CAUSAL_RELATIONSHIP, SILENT_EPISTEMIC_UPGRADE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .provenance import (
    IncompleteProvenanceError,
    SourceRecord,
    canonical_sha256,
)

# Relationship types a quarantined claim may carry. Causal
# predicates (CONTROLS, OWNS, FINANCES, EXECUTES_C2) are forbidden
# by gate C2 and never appear here.
ALLOWED_RELATIONSHIPS = ("QUARANTINED_AS", "SUPPORTED_BY", "RELATED_TO",
                         "MENTIONED_WITH")

# The example item for the quarantine view, taken from the ICD203
# rendering (§4, RubyGems quarantine finding). The source printed its
# retrieval time as "2026-09-20T06:57:0005:00"; the timestamp below
# is that same instant normalized to UTC.
RUBYGEMS_CLAIM = {
    "claim_id": "CLAIM-RUBYGEMS-AI-SWARM-2026",
    "text": ("Autonomous agents uploaded 2,000 malicious packages, "
             "bypassed email verification, probed CDN caching, and "
             "achieved RCE via RubyDoc."),
    "source_id": "SRC-YOUTUBE-TRANSCRIPT",
    "source_locator": "YouTube transcript – Emma Explains AI",
    "retrieval_timestamp": "2026-09-20T11:57:00Z",
    "temporal_reference": "May 2026",
    "confidence": "SOURCE_REPORTED",
    "epistemic_state": "QUARANTINED",
    "relationship": "QUARANTINED_AS",
    "reason": ("Non-evidentiary narrative quarantined: speculative "
               "involvement claims and breach assertions are not "
               "source evidence. The verified grounding is kept "
               "separate: automated agent scripts interacted with "
               "the RubyGems platform, bypassed email verification "
               "with disposable accounts, manipulated RubyDoc "
               "pipelines, and probed CDN caching headers."),
    "notes": ("Source printed retrieval time as "
              "2026-09-20T06:57:0005:00; normalized to UTC "
              "2026-09-20T11:57:00Z."),
}


@dataclass(frozen=True)
class QuarantinedClaim:
    """One quarantined, non-evidentiary claim."""

    claim_id: str
    text: str
    source_id: str
    source_locator: str
    retrieval_timestamp: str
    reason: str
    temporal_reference: str = ""
    confidence: str = "SOURCE_REPORTED"
    epistemic_state: str = "QUARANTINED"
    relationship: str = "QUARANTINED_AS"
    notes: str = ""

    def validate(self) -> list[str]:
        """Return the names of missing or invalid fields."""
        record = SourceRecord(
            source_id=self.source_id,
            source_locator=self.source_locator,
            retrieval_timestamp=self.retrieval_timestamp)
        missing = record.validate()
        if not self.claim_id.strip():
            missing.append("claim_id")
        if not self.text.strip():
            missing.append("text")
        if not self.reason.strip():
            missing.append("reason")
        if self.relationship not in ALLOWED_RELATIONSHIPS:
            missing.append(
                f"relationship {self.relationship!r} is not allowed")
        return missing

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "source_id": self.source_id,
            "source_locator": self.source_locator,
            "retrieval_timestamp": self.retrieval_timestamp,
            "temporal_reference": self.temporal_reference,
            "confidence": self.confidence,
            "epistemic_state": self.epistemic_state,
            "relationship": self.relationship,
            "reason": self.reason,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuarantinedClaim":
        return cls(
            claim_id=data.get("claim_id", ""),
            text=data.get("text", ""),
            source_id=data.get("source_id", ""),
            source_locator=data.get("source_locator", ""),
            retrieval_timestamp=data.get("retrieval_timestamp", ""),
            temporal_reference=data.get("temporal_reference", ""),
            confidence=data.get("confidence", "SOURCE_REPORTED"),
            epistemic_state=data.get("epistemic_state", "QUARANTINED"),
            relationship=data.get("relationship", "QUARANTINED_AS"),
            reason=data.get("reason", ""),
            notes=data.get("notes", ""),
        )


class QuarantineStore:
    """The quarantine store, persisted as JSON.

    Adding a claim with incomplete provenance raises
    IncompleteProvenanceError; the claim is not stored.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._claims: dict[str, QuarantinedClaim] = {}
        if self.path is not None and self.path.exists():
            self.load()

    @classmethod
    def seeded(cls, path: Path | None = None) -> "QuarantineStore":
        """A store pre-loaded with the RubyGems example item."""
        store = cls(path)
        if not store._claims:
            store.add(QuarantinedClaim.from_dict(RUBYGEMS_CLAIM))
        return store

    def add(self, claim: QuarantinedClaim) -> QuarantinedClaim:
        missing = claim.validate()
        if missing:
            raise IncompleteProvenanceError(
                "INCOMPLETE_PROVENANCE: cannot quarantine claim "
                f"{claim.claim_id or '<no id>'} — missing "
                + ", ".join(missing))
        if claim.claim_id in self._claims:
            raise ValueError(
                f"duplicate claim_id {claim.claim_id!r} already "
                "quarantined")
        self._claims[claim.claim_id] = claim
        return claim

    def route_incomplete(self, *, claim_id: str, text: str,
                         source_id: str = "", source_locator: str = "",
                         retrieval_timestamp: str = "",
                         reason: str = "INCOMPLETE_PROVENANCE",
                         **extra) -> QuarantinedClaim:
        """Route a payload with incomplete provenance to quarantine.

        The payload's provenance fields are recorded as given (empty
        where missing); the claim is still stored because quarantine
        is the holding place for defective payloads, and its
        ``reason`` names the defect. The claim is never promoted.
        """
        claim = QuarantinedClaim(
            claim_id=claim_id,
            text=text,
            source_id=source_id or "UNKNOWN",
            source_locator=source_locator or "UNKNOWN",
            retrieval_timestamp=retrieval_timestamp or "1970-01-01T00:00:00Z",
            reason=reason,
            **extra)
        if claim.claim_id in self._claims:
            raise ValueError(
                f"duplicate claim_id {claim.claim_id!r} already "
                "quarantined")
        self._claims[claim.claim_id] = claim
        return claim

    def get(self, claim_id: str) -> QuarantinedClaim | None:
        return self._claims.get(claim_id)

    def all(self) -> list[QuarantinedClaim]:
        return [self._claims[key] for key in sorted(self._claims)]

    def __len__(self) -> int:
        return len(self._claims)

    def save(self, path: Path | None = None) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to save the quarantine store to")
        payload = {"claims": [c.to_dict() for c in self.all()]}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True,
                       ensure_ascii=False) + "\n", encoding="utf-8")
        self.path = target
        return target

    def load(self, path: Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to load the quarantine store from")
        data = json.loads(target.read_text(encoding="utf-8"))
        self._claims = {}
        for item in data.get("claims", []):
            claim = QuarantinedClaim.from_dict(item)
            if claim.claim_id in self._claims:
                raise ValueError(
                    f"duplicate claim_id {claim.claim_id!r} in stored "
                    f"quarantine {target}")
            self._claims[claim.claim_id] = claim
        self.path = target

    def canonical_hash(self) -> str:
        """SHA-256 of the canonical JSON form of the whole store."""
        return canonical_sha256(
            {"claims": [c.to_dict() for c in self.all()]})
