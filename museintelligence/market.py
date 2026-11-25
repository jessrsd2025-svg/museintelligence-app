"""Market-sentiment envelopes (TOOL-MKT-01, PREDICTION_MARKET_READER).

An envelope is a read-only crowd-sentiment snapshot. The invariant
is: market_probability = crowd sentiment snapshot; NEVER event
evidence. The guard is enforced twice: the hardcoded constants
below (stdlib, always applied) and, when the ``jsonschema`` package
is installed, validation against the schema in
templates/06_market_sentiment_envelope.json.

A valid envelope always has epistemic_tag SENTIMENT_ONLY,
graph_mutation_authorized false, human_review_required true, and
confidence_weight 0.0 when present.
"""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_FIELDS = (
    "market_id",
    "provider_locator",
    "snapshot_timestamp_utc",
    "implied_probability_float",
    "liquidity_depth_usd",
    "epistemic_tag",
    "graph_mutation_authorized",
    "human_review_required",
    "source_id",
    "source_locator",
    "retrieval_timestamp",
)

ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {"confidence_weight", "tool_id"}

HARDCODED = {
    "epistemic_tag": "SENTIMENT_ONLY",
    "graph_mutation_authorized": False,
    "human_review_required": True,
}


def _default_schema_path() -> Path:
    here = Path(__file__).resolve()
    for base in (here.parent.parent, Path.home() / "workspace" / "notes"):
        candidate = base / "templates" / "06_market_sentiment_envelope.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "market-sentiment envelope schema not found (looked in the app "
        "templates/ directory and ~/workspace/notes/templates/)")


def load_schema(path: str | Path | None = None) -> dict:
    """Load the TOOL-MKT-01 output contract (JSON Schema)."""
    target = Path(path) if path is not None else _default_schema_path()
    return json.loads(target.read_text(encoding="utf-8"))


def _stdlib_checks(envelope: dict) -> list[str]:
    """The hardcoded SENTIMENT_ONLY guard, stdlib only."""
    errors: list[str] = []
    if not isinstance(envelope, dict):
        return ["envelope must be a JSON object"]
    for field in REQUIRED_FIELDS:
        if field not in envelope:
            errors.append(f"missing required field: {field}")
    for field in envelope:
        if field not in ALLOWED_FIELDS:
            errors.append(f"additional property not allowed: {field}")
    for field, want in HARDCODED.items():
        if field in envelope and envelope[field] != want:
            errors.append(
                f"{field} must be {want!r}, got {envelope[field]!r} "
                "(SENTIMENT_ONLY guard)")
    prob = envelope.get("implied_probability_float")
    if prob is not None and not (
            isinstance(prob, (int, float)) and not isinstance(prob, bool)
            and 0 <= prob <= 1):
        errors.append(
            f"implied_probability_float {prob!r} outside 0-1")
    depth = envelope.get("liquidity_depth_usd")
    if depth is not None and not (
            isinstance(depth, (int, float)) and not isinstance(depth, bool)
            and depth >= 0):
        errors.append(
            f"liquidity_depth_usd {depth!r} must be a number >= 0")
    weight = envelope.get("confidence_weight")
    if weight is not None and weight != 0.0:
        errors.append(
            f"confidence_weight must be 0.0, got {weight!r}")
    tool = envelope.get("tool_id")
    if tool is not None and tool != "TOOL-MKT-01":
        errors.append(f"tool_id must be 'TOOL-MKT-01', got {tool!r}")
    for field in ("market_id", "provider_locator", "source_id",
                  "source_locator"):
        value = envelope.get(field)
        if value is not None and (
                not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be a non-empty string")
    return errors


def validate_envelope(envelope: dict,
                      schema: dict | None = None
                      ) -> tuple[bool, list[str], str]:
    """Validate an envelope. Returns (ok, errors, note).

    The stdlib guard always runs. When a schema is given (or found)
    and ``jsonschema`` is installed, the envelope is also validated
    against the JSON Schema; if ``jsonschema`` is absent the stdlib
    guard is the whole check and the note says so.
    """
    errors = _stdlib_checks(envelope)
    note = "jsonschema not installed; stdlib guard only"
    if schema is None:
        try:
            schema = load_schema()
        except FileNotFoundError:
            schema = None
            note = "schema file not found; stdlib guard only"
    if schema is not None:
        try:
            import jsonschema  # type: ignore
        except ImportError:
            note = "jsonschema not installed; stdlib guard only"
        else:
            validator = jsonschema.Draft202012Validator(schema)
            for error in validator.iter_errors(envelope):
                message = f"schema: {error.message}"
                if message not in errors:
                    errors.append(message)
            note = "validated against the JSON Schema"
    return (not errors, errors, note)


def load_envelope_file(path: str | Path) -> dict:
    """Load one envelope from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return data


def example_envelope() -> dict:
    """A valid example envelope (illustrative values only; the
    example.invalid domain is reserved and not a real market)."""
    return {
        "market_id": "EXAMPLE-MARKET-002",
        "provider_locator": "https://example.invalid/markets/EXAMPLE-MARKET-002",
        "snapshot_timestamp_utc": "2026-11-25T12:00:00Z",
        "implied_probability_float": 0.62,
        "liquidity_depth_usd": 125000.0,
        "epistemic_tag": "SENTIMENT_ONLY",
        "graph_mutation_authorized": False,
        "human_review_required": True,
        "confidence_weight": 0.0,
        "source_id": "SRC-EXAMPLE-MKT-002",
        "source_locator": "https://example.invalid/markets/EXAMPLE-MARKET-002",
        "retrieval_timestamp": "2026-11-25T12:00:00Z",
        "tool_id": "TOOL-MKT-01",
    }
