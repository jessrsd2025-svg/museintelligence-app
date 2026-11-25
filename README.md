# MuseIntelligence ICD203

A reading-room and governance app for the LIBERTAS // VERITAS //
AEQUITAS system. It ingests documents and shared AI conversations,
renders them as a browsable markdown wiki/index, and governs every
claim with provenance, epistemic tags, and the 18-gate acceptance
checklist. Nothing in the app is presented as settled fact unless a
human has reviewed its source.

This repository is the working v1 of the app specified in
[the MuseIntelligence ICD203 Gemini app-creation specification](../muse-intelligence-icd203-gemini-renderings.md)
(Renderings.md, ICD203 canonical format). All claims in the app are
SOURCE_REPORTED (or GENERATED_ANALYSIS) until a human reviews the
source. The app never assigns VERIFIED_FACT on its own.

See [ROADMAP.md](ROADMAP.md) for the project roadmap — what's done, what's in progress, and what's next.

## Quickstart

Python 3.10+; the core runs on the standard library alone.

```sh
# Start the web UI (http://127.0.0.1:8000/)
python3 -m museintelligence --serve

# Run the 18-gate checklist over a directory
python3 -m museintelligence --check .

# Run the tests
python3 -m unittest discover -s tests -v
```

## What it does

- **Ingest** (`museintelligence/ingest.py`) — accepts `.md`, `.txt`
  and `.json` sources. Every source is registered with a source_id,
  a stable source_locator, and a UTC retrieval_timestamp; anything
  missing one of the three is refused as INCOMPLETE_PROVENANCE.
  PDF text extraction is not implemented yet: `.pdf` is refused
  with a clear message.
- **Render** (`museintelligence/render.py`) — builds a markdown
  wiki/index in the Renderings.md canonical format: source block,
  provenance guards, index with anchors, governed sections, entity
  index, links, rendering notes.
- **Provenance** (`museintelligence/provenance.py`) — the source
  registry plus SHA-256 digests of canonical (RFC 8785-style)
  content.
- **Quarantine** (`museintelligence/quarantine.py`) — the store and
  view for non-evidentiary claims. The seeded example is the
  RubyGems finding, claim `CLAIM-RUBYGEMS-AI-SWARM-2026`, shown
  with its provenance and human review required before any
  promotion — never as settled fact.
- **Gates** (`museintelligence/gates.py`) — runs the 18-gate
  acceptance checklist (`tools/aequitas_gate_linter.py`) and reports
  PASS / FAIL / MANUAL per gate. D2 and E3 are MANUAL by design.
- **Market** (`museintelligence/market.py`) — validates
  market-sentiment envelopes against
  `templates/06_market_sentiment_envelope.json` with the
  SENTIMENT_ONLY guard: implied probabilities are sentiment only,
  `graph_mutation_authorized` is false, `human_review_required`
  is true, `confidence_weight` is 0.0.
- **GitHub** (`museintelligence/github.py`) — TOOL-GH-01
  (`tools/github_call.py`): pin a ref to a commit SHA, verify the
  ref, fetch bytes at that SHA, hash. Branch names are refused.
  Commit SHA is the anchor; branch names are not.
- **Model** (`museintelligence/model.py`) — lazy backend for the
  open-source model (see below).

## Web UI

`python3 -m museintelligence --serve` starts a stdlib-only UI on
`http://127.0.0.1:8000/` with pages for the dashboard (OODA status),
documents, renderings, provenance, quarantine, the gates runner,
the sentiment-envelope viewer, and the GitHub panel. It works
offline except for model and GitHub calls, which the user triggers
explicitly.

## Open-source model

The app's reasoning engine is an open-source, open-weights model:

- **Default model:** `Qwen/Qwen2.5-7B-Instruct` — instruction-tuned
  7B, Apache License 2.0, ungated on Hugging Face. Model page:
  <https://huggingface.co/Qwen/Qwen2.5-7B-Instruct>
- **Pinning rule:** the model is loaded only at a commit SHA pinned
  in the configuration — never at a floating branch or tag. At build
  time the SHA is resolved and pinned via the TOOL-GH-01 flow
  (`pin_commit_sha` to resolve the ref, `verify_ref` to check it)
  and recorded in the app configuration. The shipped
  `config.example.yaml` holds the placeholder "to be pinned at
  build time"; no SHA is invented here.
- **No downloads:** the app never downloads weights. Loading uses
  `local_files_only=True`, so weights must already be in the local
  Hugging Face cache at the pinned revision. If Transformers is not
  installed, or the weights are not cached, the backend fails
  cleanly with a clear message.
- **The model is a reasoning engine only.** Its outputs are
  GENERATED_ANALYSIS; the underlying claims stay SOURCE_REPORTED
  until a human reviews them.

Copy `config.example.yaml` to `config.yaml` and pin the SHA there
when the app is built.

## Repository layout

```
museintelligence/      the app package (ingest, render, provenance,
                       quarantine, gates, market, github, model,
                       server, __main__)
tools/                 reused tools: github_call.py (TOOL-GH-01) and
                       aequitas_gate_linter.py (18-gate checklist)
templates/             06_market_sentiment_envelope.json (TOOL-MKT-01)
data/                  registry.json, quarantine.json, documents/,
                       envelopes/, renderings/
examples/              a valid market-sentiment envelope
tests/                 stdlib unittest suite
.github/workflows/     gates.yml — runs the linter on push/PR
```

## Acceptance

Every change must pass the 18-gate checklist before it leaves
`DRY_RUN` status:

```sh
python3 tools/aequitas_gate_linter.py .
```

Gates D2 (context vs. authorization separation) and E3 (human
sign-off) are MANUAL by design and are confirmed by a human, not
by the scan.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
