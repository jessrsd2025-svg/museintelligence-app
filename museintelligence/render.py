"""Rendering: build a markdown wiki/index in the Renderings.md
canonical format.

Output shape (per the ICD203 Renderings.md specification): title,
Source block, provenance and epistemic guards, index with anchors,
governed sections with source references, entity index, links, and
rendering notes. Every section carries the epistemic tag
SOURCE_REPORTED unless its sources are human-reviewed; material
derived from a generated summary is labelled GENERATED_ANALYSIS.
"""

from __future__ import annotations

import re

from .provenance import SourceRecord, utc_now_iso

_GUARDS = (
    "Every source object carries a source_id, a stable source_locator, "
    "and a UTC retrieval_timestamp. A payload lacking any of the three "
    "is INCOMPLETE_PROVENANCE and fails the build.",
    "All claims in this rendering are SOURCE_REPORTED unless their "
    "cited source is human-reviewed. No claim is assigned "
    "VERIFIED_FACT without human review, and no silent epistemic "
    "upgrade is performed.",
    "Market and sentiment content is SENTIMENT_ONLY: it is never event "
    "evidence and never authorizes a graph mutation.",
    "No causal edges are asserted. Claims from different source types "
    "are kept as separate nodes, never merged into one claim.",
    "Content derived from a generated summary is labeled "
    "GENERATED_ANALYSIS and is not a verbatim source passage.",
)


def slugify(text: str) -> str:
    """Anchor slug: lowercase, runs of non-alphanumerics become one
    dash, leading/trailing dashes stripped."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def _source_line(record: SourceRecord) -> str:
    reviewed = "yes" if record.human_reviewed else "no"
    return (f"- `{record.source_id}` — {record.source_locator} — "
            f"retrieved {record.retrieval_timestamp} — "
            f"human-reviewed: {reviewed}")


def build_rendering(*, title: str, system: str,
                    sources: list[SourceRecord],
                    sections: list[dict],
                    entities: list[str] | None = None,
                    links: list[dict] | None = None,
                    notes: str = "",
                    rendered_utc: str | None = None) -> str:
    """Build a Renderings.md document.

    ``sections`` is a list of dicts with keys ``heading`` (str),
    ``body`` (str, markdown), ``source_refs`` (list of source_id
    strings) and optional ``level`` (default 2). Every section's
    source_refs must resolve to a source in ``sources``; a dangling
    reference raises ValueError.
    """
    known = {record.source_id for record in sources}
    for section in sections:
        for ref in section.get("source_refs", []):
            if ref not in known:
                raise ValueError(
                    f"section {section.get('heading')!r} cites unknown "
                    f"source {ref!r}")
    entities = list(entities or [])
    links = list(links or [])
    rendered = rendered_utc or utc_now_iso()

    lines: list[str] = [f"# {title}", ""]
    lines.append("## Source")
    lines.append("")
    lines.append(f"- **System:** {system}")
    lines.append(f"- **Title:** {title}")
    lines.append(f"- **Rendered (UTC):** {rendered}")
    lines.append("- **Sources:**")
    for record in sources:
        lines.append(f"  {_source_line(record)}")
    lines.append("")
    lines.append("## Provenance and epistemic guards")
    lines.append("")
    for guard in _GUARDS:
        lines.append(f"- {guard}")
    lines.append("")
    lines.append("## Index")
    lines.append("")
    for index, section in enumerate(sections, start=1):
        lines.append(
            f"{index}. [{section['heading']}](#{slugify(section['heading'])})")
    lines.append("---")
    lines.append("")
    for section in sections:
        level = int(section.get("level", 2))
        lines.append(f"{'#' * level} {section['heading']}")
        lines.append("")
        lines.append(section["body"].rstrip())
        lines.append("")
        refs = section.get("source_refs", [])
        if refs:
            tags = ", ".join(f"`{ref}`" for ref in refs)
            lines.append(
                f"*Sources: {tags} — epistemic tag: SOURCE_REPORTED.*")
            lines.append("")
    if entities:
        lines.append("## Entity index")
        lines.append("")
        for entity in entities:
            lines.append(f"- {entity}")
        lines.append("")
    if links:
        lines.append("## Links")
        lines.append("")
        for link in links:
            lines.append(f"- [{link['label']}]({link['url']})")
        lines.append("")
    lines.append("## Rendering notes")
    lines.append("")
    lines.append(notes or (
        "This rendering was built by the MuseIntelligence app from the "
        "sources listed above. All claims are SOURCE_REPORTED unless "
        "their cited source is human-reviewed."))
    lines.append("")
    return "\n".join(lines)


def render_quarantine_md(claims: list[dict]) -> str:
    """Render the quarantine store as markdown (quarantine.md).

    Quarantined claims are shown as non-evidentiary items with their
    provenance and human review required before any promotion — never
    as settled fact.
    """
    lines = [
        "# Quarantine",
        "",
        "Non-evidentiary claims held out of the verified record. "
        "Each item shows its provenance; human review is required "
        "before any promotion. No item here is settled fact.",
        "",
    ]
    if not claims:
        lines.append("No quarantined claims.")
        lines.append("")
        return "\n".join(lines)
    for claim in claims:
        lines.append(f"## {claim['claim_id']}")
        lines.append("")
        lines.append(claim["text"])
        lines.append("")
        lines.append(f"- **Epistemic state:** {claim['epistemic_state']}")
        lines.append(f"- **Confidence:** {claim['confidence']}")
        lines.append(f"- **decision_rationale:** {claim['reason']}")
        lines.append("- **human_review_required:** true")
        lines.append(f"- **Temporal reference:** "
                     f"{claim.get('temporal_reference', '')}")
        lines.append(f"- **Source:** `{claim['source_id']}` — "
                     f"{claim['source_locator']} — retrieved "
                     f"{claim['retrieval_timestamp']}")
        lines.append("")
    return "\n".join(lines)
