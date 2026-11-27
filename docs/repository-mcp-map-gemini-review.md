# MuseIntelligence — Repository MCP Map and Gemini Architecture Review

**Author:** Jesse Marshall (jessrsd / Unmanned_News)

**Series:** Renderings of Strategic Dynamics

**Source:** Gemini conversation "Muse Architecture Roadmap Review" (created with Gemini 4 Hydrogen, November 27, 2026 at 11:22 AM, published 11:23 AM), reviewing the repository MCP map for museintelligence-app (commit 9a70e91, generated 2026-11-26).

**Repository map (SVG):** [docs/repository-mcp-map.svg](https://github.com/jessrsd2025-svg/museintelligence-app/blob/e85f9f61922c18014e79a5ab1a8e3f22e51df493/docs/repository-mcp-map.svg)

**Gemini conversation:** https://gemini.google.com/share/956d726883085447fbe71cbc7b19dc60

**Rendered:** November 27, 2026

> **Status — rendering, not verification.** This post reproduces Gemini's response to the uploaded repository MCP map image, as Gemini stated it. Claims in it are as stated by Gemini; they are not independently verified by this rendering. Human review is required before any claim is used as evidence.

---

## The repository MCP map

The map is the Neo4j graph context for the museintelligence-app repository, rendered as a Scalable Vector Graphic (SVG) for the Model Context Protocol (MCP) access path: how a model/agent reaches the repository, what the repository holds, and what governs it.

- **File:** `docs/repository-mcp-map.svg` (24,166 bytes, 1900x844)
- **Repository:** museintelligence-app, main, 33 files, commit 9a70e91
- **Generated:** 2026-11-26 by `tools/build_repository_mcp_map.py` (deterministic — the same tree always produces the same SVG bytes)
- **View it:** https://github.com/jessrsd2025-svg/museintelligence-app/blob/e85f9f61922c18014e79a5ab1a8e3f22e51df493/docs/repository-mcp-map.svg

Jesse uploaded the map image to Gemini, and Gemini responded with the architecture review reproduced below.

---

## Gemini's response — "Muse Architecture Roadmap Review"

The repository MCP map for museintelligence-app (commit 9a70e91, generated 2026-11-26) details the structural layout, gating dependencies, and tool bindings across:

### 1. Structural Inventory & Access Paths

- Root Governance: AGENTS.md, LICENSE, README.md, ROADMAP.md, config.example.yaml, .gitignore, and quarantine.md.
- Execution & Ingestion (museintelligence/): Houses core processing (__init__.py, __main__.py, gates.py, github.py, ingest.py, market.py, model.py, provenance.py, quarantine.py, runtime.py, serve.py).
- Tools (tools/): Contains aequitas_gate_filter.py and github_call.py.
- Data & Registries (data/): Tracks documents/.gitkeep, checkpoints/.gitkeep, quarantine.json, registry.json, and rendered corpora (renderings/museintelligence-icd203-gemini.md).
- Documentation (docs/): Contains langchain_deep_agents_subagents.md (ADR-SUBAGENTS-001) and wordpress-eval.md.
- Templates & Examples (templates/, examples/): Stores 06_market_sentiment_envelope.json and market_envelope_example.json.
- CI/CD & Tests: Workflows in .github/workflows/gates.yml, test suites in tests/__init__.py and tests/test_museintelligence.py, and documentation in wiki/index.md.

### 2. Gating and Boundary Enforcement

- AEQUITAS Gates (14-gate checklist): Imposes deterministic verification directly on gates.py and feeds interdictions into quarantine.md.
- TOOL-GH-01 (commit-anchor-verifier): Validates GitHub commits and SHA integrity on tools/github_call.py, gated by AEQUITAS.
- TOOL-MKT-01 (market-signal-SENTIMENT_ONLY): Enforces epistemic boundary labeling on museintelligence/market.py, strictly downgrading market feeds from event proof to SENTIMENT_ONLY.
- Interdiction Triggers (6 triggers): Deterministically routes schema violations, prohibited predicates, or provenance gaps to data/quarantine.json and quarantine.md.
- Provenance Registry: Connects museintelligence/provenance.py directly to data/registry.json, enforcing immutable source_id, locator, and timestamp tracking before graph insertion or downstream handoff.

### 3. Synthesis with ADR-SUBAGENTS-001 & Increment Alignment

Connecting this physical topology to the architectural decision record (langchain_deep_agents_subagents.md):

1. Increment A & B Mapping: museintelligence/runtime.py and model.py serve as the foundation for the proposed create_deep_agent / LangGraph harness, while data/registry.json forms the base for the proposed subagents/registry.yaml allowlist.
2. Deterministic Interdiction (Increment C): tools/aequitas_gate_filter.py and museintelligence/gates.py enforce the 6 interdiction triggers against templates/06_market_sentiment_envelope.json and child subagent results before any state reaches supervisor synthesis.
3. Execution Separation: Write tools remain completely absent from tools/, matching the invariant that read-only subagents cannot mutate Neo4j or trigger state changes without an external, cryptographically signed human authorization pipeline.

Would you like to draft the exact unit tests (SUB-UNIT-001 through SUB-UNIT-012), implement the subagents/registry.yaml schema against registry.json, or align this topology directly with the milestones in ROADMAP.md?

---

## Source and accuracy note

This post reproduces Gemini's response verbatim, as displayed on the shared conversation page. The conversation is a single turn: Jesse uploaded the MCP map image (shown as "image_0.jpg", titled "MuseIntelligence — Repository MCP Map") with no text prompt, and Gemini responded with the review above. The visible response ends with the unit-tests question.

Accuracy note — Gemini's response contains errors when checked against the actual repository at commit 9a70e91 (these are flagged here, not silently corrected in the verbatim copy above):

- It says "AEQUITAS Gates (14-gate checklist)" — the repository's acceptance checklist has **18 gates** (16 pass, 2 manual by design), not 14.
- It names files that do not exist in the repository: `museintelligence/runtime.py`, `museintelligence/serve.py` (the server module is `server.py`), `tools/aequitas_gate_filter.py` (the linter is `tools/aequitas_gate_linter.py`), `data/checkpoints/.gitkeep` (the data folders are `documents/` and `envelopes/`), and `docs/wordpress-eval.md` (no such file in `docs/`).
- A closing "In short..." paragraph found only in a prose extraction of the shared page is NOT included above, because it does not appear in the rendered shared page.

All Gemini-derived claims in this post are SOURCE_REPORTED, never VERIFIED_FACT.

Rendered November 27, 2026, from the shared Gemini conversation listed above. LIBERTAS // VERITAS // AEQUITAS.
