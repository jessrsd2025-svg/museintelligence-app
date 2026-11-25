# Roadmap — MuseIntelligence ICD203 App

- **Document class:** Project roadmap
- **Project:** MuseIntelligence ICD203 app (`museintelligence-app`)
- **Companion repo:** MuseIntelligence Library (`museintelligence-library`)
- **Status:** Working roadmap
- **Revision:** 1.0
- **Date:** 2026-11-25
- **Human Supervisor:** Jesse marshall — sole authority for sign-off and publication
- **Epistemic status:** every claim in this file is SOURCE_REPORTED unless its cited source is human-reviewed. No claim in this file is VERIFIED_FACT. Dates are plans, not guarantees.

## Overview

The app is the open-source MuseIntelligence ICD203 reading-room and governance app (Qwen/Qwen2.5-7B-Instruct, Apache 2.0). This roadmap states what is done, what is in progress, and what is next. It is a plan, not a promise — the Human Supervisor sets the order and the dates. The companion library repo is the corpus this app governs; its own roadmap items are noted where they touch this app.

## Phase 1 — Built (done, 2026-11-25)

- App v1: Python package (provenance, ingest, rendering, quarantine, gates, market envelopes, TOOL-GH-01, lazy Qwen backend, standard-library web UI, CLI), 38 tests passing, linter 16 passed / 0 failed / 2 manual.
- WordPress scrape and AGENTS.md: the full public blog, 577 published posts (2023-12-22 to 2026-11-25), with a 577-row source index.
- ICD203 Gemini app spec published on WordPress (post 18250, "Renderings of Strategic Dynamics").
- Library repo built: 577 posts as individual markdown files, index.json, readingroom package, 11 tests passing, linter 16 passed / 0 failed / 2 manual.
- Google compliance: Section 17 / Workspace Addendum check done (Human Supervisor decided "keep it as-is" for the Gemini-derived rendering in this app); the MuseIntelligence "Model Context Protocol" for Library written in the library repo.
- GitHub repo created (public, empty): https://github.com/jessrsd2025-svg/museintelligence-app

## Phase 2 — Publish (now, November–December 2026)

- Push both repos to GitHub via Git bundles (Option C, chosen 2026-11-25). The app bundle carries this roadmap; the library bundle is at its 9f3c618 commit. Create `museintelligence-library` (public, empty) on GitHub first.
- Add the GitHub app link to the WordPress Renderings post (post 18250) once the push is live.
- Confirm the library's "when complete" step (the directive was cut off at "When comple..." on 2026-11-25) — push as `museintelligence-library`, post on WordPress, or something else. Still unconfirmed.

## Phase 3 — Model and ingestion (January 2027)

- Pin the Qwen/Qwen2.5-7B-Instruct commit SHA at build time via TOOL-GH-01. No SHA is stated anywhere yet; the spec and the code both say "to be pinned at build time." No SHA is invented.
- Load model weights (the backend is lazy; no weights are loaded or downloaded yet) and verify the backend end to end.
- PDF text extraction (ingest currently accepts `.md`, `.txt`, and `.json` and refuses `.pdf` with a clear message).
- Re-scrape the blog and rebuild the library for posts published after 2026-11-25.

## Phase 4 — Graph (only if the Human Supervisor asks)

- Neo4j Cypher migration for Chainlink Proof of Reserve and tokenized Treasury attestations. Unbuilt. AGENTS.md §17: do not build it unless the human asks.
- No date is set for this phase.

## Compliance dates (external)

- GCP Service Specific Terms, Section 17 (GCP Access Tools): effective January 1, 2027.
- Google Workspace AI Tools Addendum: technical enforcement from February 1, 2027; agent-usage billing from April 1, 2027.
- The compliance protocol (MODEL_CONTEXT_PROTOCOL.md, in the library repo) is already written; it goes live with the push.

## Open items (not yet decided)

- The library's "when complete" step (see Phase 2).
- The "ReadingRoonm" title typo in post 18250. It is Jesse's title; fix it only if he asks.
- The LinkedIn share-connection warning on post 18250 (the post likely did not go to LinkedIn).

## Governance

This roadmap is subordinate to AGENTS.md and Human-Approved Policy (precedence hierarchy, AGENTS.md §2). Changes to it need the Human Supervisor's sign-off. Nothing in it is VERIFIED_FACT, and no date in it is a guarantee.
