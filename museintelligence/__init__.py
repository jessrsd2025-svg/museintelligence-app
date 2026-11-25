"""MuseIntelligence ICD203 — reading-room and governance app.

Implements the app-creation specification in
muse-intelligence-icd203-gemini-renderings.md: document ingest with
provenance, Renderings.md rendering, quarantine for non-evidentiary
claims, the 18-gate acceptance checklist, market-sentiment envelopes
(SENTIMENT_ONLY), TOOL-GH-01 pinned GitHub reads, and an open-source
model backend (Qwen/Qwen2.5-7B-Instruct, loaded only at a pinned
commit SHA).

All claims are SOURCE_REPORTED (or GENERATED_ANALYSIS) until a
human reviews the source. Nothing here assigns VERIFIED_FACT.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
