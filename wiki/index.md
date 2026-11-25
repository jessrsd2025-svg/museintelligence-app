# MuseIntelligence — Wiki / Index

A wiki index of what was accomplished over Nov 23–25, 2026: the ICD203
Gemini app specification, the open-source app and library repositories
published to GitHub, and the WordPress post that ties them together.

> **Epistemic note.** Every claim here is SOURCE_REPORTED unless a human
> reviewed its source. Nothing is VERIFIED_FACT without human review. The
> governance rules (six-tier hierarchy, six interdiction triggers, 18-gate
> acceptance checklist) are the same as in the app's `AGENTS.md`.

---

## Quick links

| What | Where |
| --- | --- |
| App repo (GitHub) | https://github.com/jessrsd2025-svg/museintelligence-app |
| Library repo (GitHub) | https://github.com/jessrsd2025-svg/museintelligence-library |
| WordPress post (the spec) | https://jessrsdincyahoocom.wordpress.com/2026/11/25/museintelligence-icd203-gemini-conversation-app-creation-specification-for-google-ai-studio/ |
| GitHub Projects roadmap board | https://github.com/users/jessrsd2025-svg/projects/4 |
| Blog ("jessrsd's Blog") | https://jessrsdincyahoocom.wordpress.com/ |
| GitHub profile | https://github.com/jessrsd2025-svg |

---

## Index

1. [Overview](#overview)
2. [Timeline](#timeline)
3. [The app repository](#the-app-repository)
4. [The library repository](#the-library-repository)
5. [The WordPress post](#the-wordpress-post)
6. [The roadmap board](#the-roadmap-board)
7. [Deliverables (local files)](#deliverables-local-files)
8. [Key decisions](#key-decisions)
9. [How the GitHub push was solved](#how-the-github-push-was-solved)
10. [Compliance: Google Section 17 / Workspace](#compliance-google-section-17--workspace)
11. [Open items and next steps](#open-items-and-next-steps)
12. [Sources and provenance](#sources-and-provenance)

---

## Overview

Over three days, a set of documents and shared AI conversations became two
public, open-source GitHub repositories and a published WordPress post:

- **The app** — `museintelligence-app`: a Python reading-room and governance
  app for the MuseIntelligence ICD203 system. It ingests documents and shared
  AI conversations, renders them as a governed markdown wiki/index, and checks
  every claim with provenance, epistemic tags, and the 18-gate acceptance
  checklist. Its runtime model is the open-source, open-weights
  **Qwen/Qwen2.5-7B-Instruct** (Apache License 2.0); Google AI Studio was
  the build environment only, never the runtime model.
- **The library** — `museintelligence-library`: a source-code library of the
  full public scrape of "jessrsd's Blog" — all 577 published posts
  (2023-12-22 to 2026-11-25) as individual markdown files, with an index and
  a Python package to load, search, and check them. Every file carries its
  provenance.
- **The WordPress post** — post 18250, "Renderings of Strategic Dynamics":
  the ICD203 Gemini app-creation specification, published Nov 25, 2026, now
  carrying a link to the live GitHub app repo at the top.

Both repos are public, on the `main` branch, under the GitHub account
**jessrsd2025-svg**, Apache License 2.0.

---

## Timeline

### Nov 23, 2026

- **ICD203 PDF rendering.** The 36-page ICD203 PDF
  (`jessrsd_MuseIntelligence_ICD203_Unmanned_News_ReadingRoom_1__0_u1m2.pdf`)
  was rendered into a markdown document
  (`workspace/notes/muse-intelligence-icd203-renderings.md`, 1,226 lines).
  Page 36 is blank. The cover graphic's "Strategic Signals" panel reproduces
  two of Muse's own earlier messages to Jesse (the Oct 24 week-ahead note and
  the Oct 29 Chainlink livestream heads-up).
- **ICD203 wiki page.** A browsable offline wiki
  (`workspace/notes/muse-intelligence-icd203-wiki.html`, 85,097 bytes; 81
  internal links, 0 broken).
- **Gemini share + market-sentiment schema.** Jesse shared a Gemini
  conversation ("Epistemic Governance and Architectural Framework",
  https://share.gemini.google/gPK7Vf1HHMx6) and picked the follow-up "Build
  the market-sentiment schema." Delivered:
  `workspace/notes/templates/06_market_sentiment_envelope.json` — the JSON
  Schema (draft 2020-12) output contract for TOOL-MKT-01. Market sentiment
  is `SENTIMENT_ONLY`, never event evidence; `graph_mutation_authorized` is
  false; `human_review_required` is true. Verified: schema valid, example
  validates, 11 negative cases rejected.
- **Python linter for the 18 gates.** Delivered
  `workspace/notes/tools/aequitas_gate_linter.py` (stdlib-only CLI). On the
  notes folder: 16 passed, 0 failed, 2 manual (D2 and E3 are manual by
  design). It passes Jesse's own ICD203 artifacts and rejects a deliberately
  bad market envelope.

### Nov 24, 2026

- **AILA paper (ChatGPT library link).** Jesse shared a ChatGPT library file
  ("Arxiv Papers.pdf") — the paper **"Adaptive Integrated Layered Attention
  (AILA)"**, arXiv:2503.22742v2 (Claster, Suhas K M & Gundechia,
  Northeastern University). After a long Google sign-in saga (expired session,
  codes arriving late, Jesse taking over the browser), a fresh sign-in went
  straight through. Delivered an AILA rendering
  (`workspace/notes/aila-renderings.md`) and a wiki
  (`workspace/notes/aila-wiki.html`). **Numbers corrected against the arXiv
  v2 HTML:** forecasting covers five assets; **AILA-1 leads** (lowest MSE on
  Gold, US Dollar Futures, Coffee, Wheat); **LSTM is lowest on S&P 500**;
  AILA-2 never leads; the Transformer never wins a forecasting asset.
  CIFAR-10: ViT best 76.52%. IMDB: Transformer 85.60%.
- **Second ChatGPT link.** A thread Jesse emailed himself ("Analyze Gemini
  Conversation") was a dead end: it renders no user turn, and ChatGPT's reply
  says it cannot access the Gemini link. Its three offered follow-ups were
  not taken up.

### Nov 25, 2026

The main build-and-publish day. In order:

1. **ICD203 Gemini app spec (Renderings.md).** Jesse directed: "Create In
   ICD203 Format for MuseIntelligence," then clarified the deliverable is a
   **markdown app-creation spec for Google AI Studio, not a renderer
   program**. Delivered `workspace/notes/muse-intelligence-icd203-gemini-renderings.md`
   (15,200 bytes, 15 sections): the complete specification to paste into
   Google AI Studio (Gemini Build mode) to create the MuseIntelligence ICD203
   app. All Gemini-derived claims are SOURCE_REPORTED, never VERIFIED_FACT.
   A first-pass renderer program was moved to recoverable trash after Jesse
   corrected the deliverable to markdown.
2. **TOOL-GH-01 implementation.** Delivered
   `workspace/notes/tools/github_call.py` (stdlib-only): `pin_commit_sha`,
   `verify_ref`, `fetch_bytes_at_sha` (refuses anything not exactly 40 hex
   chars, before any network call), `hash_bytes` (SHA-256). The CLI refuses
   branch refs (main/master/HEAD) outright. Verified live on `psf/requests`
   v2.32.3 (SHA `0e322af87745eff34caffe4df68456ebc20d9068`).
3. **Open-source runtime model.** The spec was amended with a new §3: the
   default model is **Qwen/Qwen2.5-7B-Instruct** (instruction-tuned, 7.61B
   parameters, 131,072-token context, Apache License 2.0, ungated on Hugging
   Face). Google AI Studio is the build environment only. The model SHA is
   "to be pinned at build time" via the TOOL-GH-01 flow — no SHA was
   invented; the spec contains zero 40-hex strings.
4. **WordPress publication of the spec.** Jesse chose "Post the full spec."
   Published 09:17 CST as post ID **18250** on "jessrsd's Blog". Jesse
   entered the WordPress password himself via the secure sign-in card.
   Correction delivered the same day: the publish showed a warning that the
   post could **not** be shared to the LinkedIn connection, so it likely did
   **not** go to LinkedIn. That share-connection issue remains.
5. **Jesse's own edits to the post.** Eight revisions by jessrsdinc: a
   diagram fragment naming Muse Glimmer 30B, GPT-5.6 Sol, and HuggingFace
   Nemotron; the title prefix "Unmanned_News ReadingRoonm " (typo his);
   pasted LinkedIn content. No spec section was removed. A markdown-only
   final edit fixed exactly one mistake — an empty H1 left by his paste was
   restored to the H2 "Source" heading. His title typo and pasted content
   were deliberately left as he wrote them.
6. **The app build.** Per Jesse's directive to move the app out of Google AI
   Studio into GitHub. Built `workspace/notes/museintelligence-app/` — a
   Python 3 stdlib-first package (`museintelligence/`, 10 modules +
   `__main__.py`) with provenance, ingest, rendering, quarantine, gates,
   market envelopes, the TOOL-GH-01 facade, a lazy Qwen backend (loads only
   at a pinned 40-hex SHA; no weights downloaded), a stdlib web UI, and a
   CLI. Reused `tools/github_call.py`, `tools/aequitas_gate_linter.py`, and
   `templates/06_market_sentiment_envelope.json` verbatim (SHA-256 verified
   identical). 38 tests, all pass. Linter on the repo: 16 passed, 0 failed,
   2 manual (D2, E3). Honest limits: no PDF text extraction (.pdf is
   refused); no model weights loaded; the model SHA is still the placeholder.
7. **WordPress scrape + AGENTS.md.** Per Jesse's directive to scrape the
   whole blog. The public WordPress.com REST API returned **577 published
   posts, 2023-12-22 to 2026-11-25**. Delivered
   `docs/wordpress-posts.md` (13.5 MB, 220,143 lines) and `AGENTS.md`
   (203 KB, 835 lines, Rev. 1.0) with a §15 source index of all 577 posts
   (source_id `SRC-WP-<post ID>`), byte-identical to the scrape index.
   Counts verified: 577 = 577 = 577 = 577 (API / scrape index / scrape
   sections / AGENTS.md §15). Linter caveat: the full-repo run flags quoted
   blog content inside `docs/` only; with `--exclude docs` the repo passes
   16/0/2, and the gates workflow was updated to exclude `docs/`.
8. **The library build.** Per Jesse's directive ("last task of the day") to
   create a source-code GitHub library from all the scraped markdowns,
   including the collaboration across his Android phone, ChatGPT, Gemini,
   Google AI Studio, and the open-source model on GitHub. Built
   `workspace/notes/museintelligence-library/` — **577 post files** by
   year/month (`library/<year>/<month>/<post-id>-<slug>.md`), each with YAML
   front-matter; `index.json` (577 entries); a `readingroom/` stdlib package
   (load, search, provenance check, CLI); `COLLABORATION.md`; `AGENTS.md`;
   `MODEL_CONTEXT_PROTOCOL.md`; 11 tests, all pass. Linter on the library's
   own artifacts (`--exclude library/`): 16/0/2. The library README links to
   the app repo, as Jesse asked.
9. **Section 17 / Workspace compliance check.** Google Cloud emailed a
   mandatory announcement (effective Jan 1, 2027) adding Section 17 (GCP
   Access Tools), and a Workspace blog post the same day announced the
   Workspace AI Tools Addendum (MCP route required from Feb 1, 2027). Muse
   flagged two touchpoints (the stored Gemini-derived rendering, and
   `ingest.py` storing bytes) and asked Jesse, as Human Supervisor, to
   decide. Jesse chose **"Keep it as-is."** Muse's own code check found **no
   calls to Google APIs, MCP servers, or Workspace** — the only network calls
   are to GitHub (TOOL-GH-01) and Hugging Face (model weights) — so nothing
   needs the MCP route or a deletion-on-disconnect plan before Feb 1, 2027.
   The check is closed.
10. **Model Context Protocol for Library.** Per Jesse's directive, delivered
    `MODEL_CONTEXT_PROTOCOL.md` in the library repo: the protocol by which a
    model/agent accesses the Library source-code. Access is local
    (`index.json`, the `readingroom/` package, the `library/` files); no
    Google Cloud API, MCP server, or Workspace REST API is in the path; no
    scraping of Google APIs/MCPs/Workspace APIs. Any Google-derived material
    ever added must be marked SOURCE_REPORTED with a removal date and removed
    within 30 days (the Library's own rule) and deleted on disconnect; no
    permanent raw storage; no model training on Library content.
11. **Workaround analysis and the Option C decision.** Jesse asked to see
    research on a workaround for the GitHub push. Delivered
    `github-push-workaround-analysis.md` (in the goal's files). Options:
    A — the connector (recommended first); B — browser upload; C — Jesse
    pushes Git bundles from his own computer; D — his own planned workaround
    (by next month, before Dec 31); E — a PAT / `gh` device flow (ruled out
    by the connector documentation). ChatGPT's take (from a share Jesse
    sent) agreed: A first, B fastest for the app only, C best fallback, D
    pending, E do not use. **Jesse chose Option C (Git bundles for both
    repos).** Both bundles were prepared and delivered with Windows push
    instructions. The bundles tripped a safety check (bundle files can run
    code when opened); Muse told Jesse in plain words and will not open or
    clone from them himself; Jesse chose the route knowing he would use them
    on his own computer.
12. **Roadmap — ROADMAP.md + GitHub Projects board.** Jesse asked for a
    GitHub "Roadmap" and chose "Both": a `ROADMAP.md` in the app repo (Phase
    1 built, done Nov 25; Phase 2 publish, Nov–Dec 2026; Phase 3 model and
    ingestion, Jan 2027; Phase 4 Neo4j graph, only if Jesse asks; plus the
    Jan 1 / Feb 1 / Apr 1, 2027 compliance dates) and a GitHub Projects
    board. Board created: project #4, **"MuseIntelligence Renderings of
    Strategic Dynamics"**, https://github.com/users/jessrsd2025-svg/projects/4,
    Roadmap (timeline) layout, four draft items (Phase 1 Nov 25, 2026;
    Phase 2 Nov 25–Dec 31, 2026; Phase 3 Jan 1–31, 2027; Phase 4 undated,
    only if Jesse asks). No issues were created. Three older empty untitled
    projects (#1–#3) were left untouched.
13. **GitHub account and repos.** Jesse already had a GitHub account under
    jessrsd2025@gmail.com (a signup attempt was stopped: "email already
    associated with an account"). He signed in via "Continue with Google"
    with device verification. GitHub username: **jessrsd2025-svg**
    (https://github.com/jessrsd2025-svg). Both repos were created empty
    (public, default branch `main`, 0 collaborators): `museintelligence-app`
    and `museintelligence-library`. Jesse authorized Muse to set the base
    permissions and set up the repository itself.
14. **The push — and how it was solved.** Jesse authorized the GitHub
    connector (Option A) and selected "all" repositories. The full app
    snapshot (31 files, 13.9 MB) failed with MCP HTTP 413 (request body too
    large). A smaller push (30 files, 379 KB, without the scrape) failed with
    GitHub 403 "Resource not accessible by integration" on create-tree. A
    browser diagnostic confirmed the App **is** installed (Nov 25, 3:50 PM
    CST) with "All repositories" and Contents read **and** write — the
    installation was never the problem. The app repo gained an "Initial
    commit" (05ff552, empty README) from provider initialization. A
    single-file write via the connector **worked** (real README, commit
    bd3be01c). The remaining 30 app files then went up via a browser upload
    (12 folder-by-folder commits, 9 minutes, verified — all 31 files, 14
    commits). The library went up next: its first batch (root/supporting 16
    files + the single 2023 post) via the browser (6 commits), and then the
    connector's bulk push **started working once the repo was non-empty**:
    2024 Jan (12 files, a959fdad), 2024 Feb–Dec (190 files, 0c5614c2), 2025
    (204 files, 13c9e50), 2026 H1 (89 files, 69b32c2) and H2 (81 files,
    0ef28c2). The library is complete: **593 files, 11 commits**, verified
    live. The 13.5 MB scrape file uploaded fine in the browser.
15. **WordPress link (the final step).** Jesse's directive (confirmed by him)
    was to include the GitHub app link in the blog's most recent
    Renderings.md post (post 18250). After Jesse completed the Google phone
    verification (the saved WordPress password had been rejected as
    incorrect; he signed in via "Continue with Google"), the browser added
    the link as its own line near the top:
    "GitHub repository: https://github.com/jessrsd2025-svg/museintelligence-app",
    verified live on the post. His title typo ("ReadingRoonm") and all pasted
    content were left as he wrote them. Nothing else changed.
16. **Wrap-up.** The Dec 30 daily push monitor and the Nov 30 reminder were
    removed (no longer needed), and the publishing goal is marked complete.
    The publish is done.

---

## The app repository

- **URL:** https://github.com/jessrsd2025-svg/museintelligence-app
- **Visibility:** Public · **Default branch:** `main` · **License:** Apache 2.0
- **State:** 31 files, 14 commits (Initial 05ff552, README bd3be01c, plus 12
  folder-by-folder upload commits).
- **Contents:** `museintelligence/` package (provenance, ingest, render,
  quarantine, gates, market, github, model, server, CLI); `tools/`
  (`github_call.py`, `aequitas_gate_linter.py`);
  `templates/06_market_sentiment_envelope.json`; `data/` (registry,
  quarantine, renderings incl. the ICD203 Gemini spec);
  `docs/wordpress-posts.md` (the 577-post scrape, 13.5 MB);
  `examples/market_envelope_example.json`; `tests/` (38 tests, all pass);
  `README.md`, `LICENSE`, `AGENTS.md`, `ROADMAP.md`, `quarantine.md`,
  `config.example.yaml`, `.github/workflows/gates.yml`.
- **How to run:** `python3 -m museintelligence --serve` →
  http://127.0.0.1:8000/ · `python3 -m museintelligence --check <path>` ·
  `python3 -m unittest discover -s tests -v`.
- **Honest limits:** no PDF text extraction (.pdf is refused); no model
  weights loaded or downloaded (the Qwen backend loads only at a pinned
  40-hex SHA, still the placeholder); the model SHA must be resolved via
  TOOL-GH-01 before the model can load; no Neo4j migration.

## The library repository

- **URL:** https://github.com/jessrsd2025-svg/museintelligence-library
- **Visibility:** Public · **Default branch:** `main` · **License:** Apache 2.0
- **State:** 593 files, 11 commits (6 browser-upload commits for the
  supporting files + 2023, then 5 connector push-files commits for 2024–2026).
- **Contents:** `library/` — 577 posts by year/month, one file per post, YAML
  front-matter (title, date, url, source_id, source_locator,
  retrieval_timestamp 2026-11-25T18:01:10Z); `index.json` (577 entries);
  `readingroom/` package (load_index, search, load_post, provenance_check,
  CLI); `tools/build_library.py`; the vendored 18-gate linter; `tests/`
  (11 tests, all pass); `README.md` (links to the app repo),
  `COLLABORATION.md`, `AGENTS.md`, `MODEL_CONTEXT_PROTOCOL.md`, `LICENSE`.
- **Counts:** 2023: 1 post · 2024: 202 · 2025: 204 · 2026: 170. The 4
  untitled posts are filed as "(untitled — post \<id\>)" with the post id as
  slug. Snapshot of 2026-11-25; posts published after that date need a
  re-scrape and rebuild (`python3 tools/build_library.py`).

## The WordPress post

- **Post 18250:** "Unmanned_News ReadingRoonm MuseIntelligence ICD203 —
  Gemini Conversation: App-Creation Specification for Google AI Studio"
  (the "ReadingRoonm" typo is Jesse's and is kept as written).
- **URL:** https://jessrsdincyahoocom.wordpress.com/2026/11/25/museintelligence-icd203-gemini-conversation-app-creation-specification-for-google-ai-studio/
- **Blog:** "jessrsd's Blog" at jessrsdincyahoocom.wordpress.com — the
  account's only site. (There is no separate site literally named
  "jessrsd_blogs"; that was Jesse's shorthand.)
- **What was added Nov 25:** a line near the top —
  "GitHub repository: https://github.com/jessrsd2025-svg/museintelligence-app"
  — verified live. Nothing else was changed.
- **Known issue:** at publish time the post could not be shared to the
  LinkedIn connection, so it likely did not go to LinkedIn.

## The roadmap board

- **Project #4:** "MuseIntelligence Renderings of Strategic Dynamics" —
  https://github.com/users/jessrsd2025-svg/projects/4 (Roadmap/timeline
  layout, linked to `museintelligence-app`).
- **Items (drafts, no issues):** Phase 1 — Nov 25, 2026 (built, done);
  Phase 2 — Nov 25–Dec 31, 2026 (publish, done); Phase 3 — Jan 1–31, 2027
  (model and ingestion); Phase 4 — undated (Neo4j graph, only if Jesse asks).

---

## Deliverables (local files)

| File | What it is |
| --- | --- |
| `workspace/notes/muse-intelligence-icd203-gemini-renderings.md` | The ICD203 Gemini app spec (Renderings.md, 15 sections, 15,200 bytes) |
| `workspace/notes/tools/github_call.py` | TOOL-GH-01 (pin/verify/fetch/hash; refuses branch refs) |
| `workspace/notes/tools/aequitas_gate_linter.py` | The 18-gate acceptance linter |
| `workspace/notes/templates/06_market_sentiment_envelope.json` | TOOL-MKT-01 market-sentiment envelope schema |
| `workspace/notes/muse-intelligence-icd203-renderings.md` | ICD203 PDF rendering (1,226 lines) |
| `workspace/notes/muse-intelligence-icd203-wiki.html` | ICD203 browsable wiki (offline) |
| `workspace/notes/aila-renderings.md` | AILA paper rendering (numbers corrected) |
| `workspace/notes/aila-wiki.html` | AILA browsable wiki (offline) |
| `workspace/goals/museintelligence-icd203-github-app-publishing/files/github-push-workaround-analysis.md` | GitHub push workaround analysis (Options A–E) |
| `workspace/notes/museintelligence-app/` | The app repo (local, 31 files) |
| `workspace/notes/museintelligence-app/AGENTS.md` | App governance (Rev. 1.0, 577-post source index §15) |
| `workspace/notes/museintelligence-app/ROADMAP.md` | App roadmap (Phases 1–4, compliance dates) |
| `workspace/notes/museintelligence-app/docs/wordpress-posts.md` | Full blog scrape (577 posts, 13.5 MB) |
| `workspace/notes/museintelligence-library/` | The library repo (local, 593 files) |
| `workspace/notes/museintelligence-library/MODEL_CONTEXT_PROTOCOL.md` | Model Context Protocol for the Library (Google compliance) |
| `workspace/notes/museintelligence-app/wiki/index.md` | This file |

---

## Key decisions

| Decision | Made by / when |
| --- | --- |
| The deliverable is a **markdown app-creation spec** for Google AI Studio, not a renderer program | Jesse, Nov 25 08:48 |
| Runtime model: **open-source** (Qwen/Qwen2.5-7B-Instruct, Apache 2.0); Google AI Studio is the build environment only | Jesse, Nov 25 08:59 |
| Post the finished app on WordPress (`jessrsd_blogs` = "jessrsd's Blog") | Jesse, Nov 25 08:59 |
| Add the GitHub app link to the most recent Renderings.md post (post 18250) when the publish finishes | Jesse, Nov 25 12:37 (confirmed 12:38) |
| Library is a **new repo** (not an addition to the app repo) and includes the app-repo link | Jesse, Nov 25 13:50–13:55 |
| Section 17: **"Keep it as-is"** — the Gemini-derived rendering and ingest storage stay in the app | Jesse, Nov 25 14:45 |
| GitHub push: **Option C — Git bundles for both repos** | Jesse, Nov 25 15:03 |
| Apply the Google-compliant workaround solution **now** (not Dec 31) | Jesse, Nov 25 15:07 |
| Roadmap: **"Both"** — a ROADMAP.md file and a GitHub Projects board | Jesse, Nov 25 15:26 |
| "You can set base permissions to set up repository yourself" | Jesse, Nov 25 15:36 |
| "Continue the push until December 30th" (daily monitor; removed once done) | Jesse, Nov 25 15:44 |
| Library upload: **"Upload it in the browser"** | Jesse, Nov 25 16:18 |

---

## How the GitHub push was solved

The push hit three distinct problems, each with its own cause:

1. **MCP HTTP 413 (request body too large).** The full app snapshot (31 files,
   13.9 MB) exceeded the MCP endpoint's body limit; the scrape file alone is
   13.5 MB. Solved by pushing in smaller pieces (and, for the app, by the
   browser upload, which has a 25 MB per-file limit).
2. **GitHub 403 "Resource not accessible by integration" on create-tree.**
   The connector's bulk `push_files` / create-tree path consistently 403'd
   while the repo was empty — even though a browser diagnostic confirmed the
   Muse GitHub App **is** installed with "All repositories" and Contents
   read **and** write. The installation was never the problem; the bulk
   push path was blocked at the MCP/Git Data API level.
3. **The working paths.** A single-file connector write (`create_or_update_file`,
   Contents API) worked — it replaced the empty README with the real one
   (bd3be01c). The app's remaining 30 files went up via the browser (12
   folder-by-folder commits). The library's first batch went up via the
   browser (6 commits), and then — once the repo was **non-empty** — the
   connector's bulk `push_files` started working with no 403, and the rest
   of the library (2024–2026) went up that way in 5 commits.

Lesson recorded: on an empty repo the bulk push 403s; once the repo has
content, `push_files` works. The app repo's "Initial commit" (05ff552, empty
README) was provider initialization, not a successful snapshot.

---

## Compliance: Google Section 17 / Workspace

- **GCP Service Specific Terms, Section 17 (effective Jan 1, 2027):**
  prohibits AI agents/access tools from enumerated security-risk activities,
  including storing product-related information obtained or derived from
  Google Cloud APIs / Google MCP servers / other access points for extended
  periods, or scraping APIs/MCPs.
- **Workspace AI Tools Addendum (enforced from Feb 1, 2027):** AI agents must
  connect through Workspace MCP/CLI instead of traditional REST APIs; no
  permanent raw storage or model training; derived data must be removed
  within a defined window and deleted on disconnect. Agent-usage billing
  from Apr 1, 2027.
- **What was decided:** Jesse (Human Supervisor) chose "Keep it as-is" for
  the stored Gemini-derived rendering and the ingest storage. Muse's code
  check found **no calls to Google APIs, MCP servers, or Workspace** in the
  app — the only network calls are to GitHub (TOOL-GH-01) and Hugging Face
  (model weights) — so nothing needs the MCP route or a deletion-on-disconnect
  plan before Feb 1, 2027. The Library's `MODEL_CONTEXT_PROTOCOL.md` states
  the same for the Library, with a 30-day removal rule (the Library's own
  rule) and deletion on disconnect for any Google-derived material ever
  added. Whether a Gemini share-link paraphrase counts as "derived"
  information under Section 17 is **not established**; the protocol is a
  compliance statement, not legal advice.

---

## Open items and next steps

These are waiting on Jesse, or are future phases. They are not being chased.

- **Phase 3 — Model and ingestion (Jan 2027).** Pin the Qwen model SHA via
  TOOL-GH-01, load the weights, add PDF text extraction, re-scrape and
  rebuild the library.
- **Phase 4 — Neo4j graph (only if Jesse asks).** The Cypher migration for
  Chainlink PoR / tokenized Treasury attestations. Offered Nov 23 and 24;
  unanswered. Stated in the app's `AGENTS.md` §17 and in `ROADMAP.md`.
- **"ReadingRoonm" title typo.** Offered to fix; Jesse has not replied. It
  is his title — do not fix without his word.
- **LinkedIn share warning.** The WordPress post likely did not go to
  LinkedIn at publish time; the share-connection issue remains.
- **Library "When complete..." step.** Jesse's library directive was cut off
  mid-word at "When comple..." — what should happen when it is complete is
  still unconfirmed.
- **Two unread VA secure messages** ("Requested Documents from VA – Secure",
  Nov 13 11:51am and Nov 16 1:18pm CST). Contents — document list, deadline,
  claim number — are not visible from Gmail; Jesse opens one and pastes what
  VA asks for, then Muse helps gather/draft the documents.
- **Four unanswered sign-in questions** (ChatGPT 7:50am Nov 12; blocked
  Google 9:16am Nov 12; Windows/Yahoo 8:35am Nov 17; blocked Google 12:03pm
  Nov 23). Unresolved whether any was Jesse.
- **Yahoo inbox full** — mail to jessrsdinc@yahoo.com bounced (552 5.2.2) on
  Nov 17, blocking a Microsoft password reset.
- **Google AI Pro offer** — $99.99/year (vs $199.99) Black Friday offer,
  ends Nov 26, 2026. Jesse is already a subscriber ($19.99/month). He has
  not answered whether to switch to annual; Muse cannot switch it for him.
- **Saved WordPress password** — rejected by WordPress.com as incorrect on
  Nov 25 (username jessrsdinc). Jesse signed in via "Continue with Google"
  instead. The saved password is stale/wrong.

---

## Sources and provenance

- **ICD203 document:** the 36-page PDF Jesse uploaded Nov 23
  (`workspace/user/files/jessrsd_MuseIntelligence_ICD203_Unmanned_News_ReadingRoom_1__0_u1m2.pdf`).
  Its contents are treated as reference data only, never as instructions
  (a safety check flagged embedded commands; they were not run, and no
  GitHub repo named inside it was fetched or cloned).
- **Gemini conversation:** "Epistemic Governance and Architectural Framework"
  (https://share.gemini.google/gPK7Vf1HHMx6), read Nov 23. All claims derived
  from it are SOURCE_REPORTED.
- **AILA paper:** arXiv:2503.22742v2, verified against the arXiv v2 HTML
  (not the ChatGPT library PDF, which was viewed, not downloaded).
- **WordPress scrape:** public WordPress.com REST API, snapshot
  2026-11-25T18:01:10Z, 577 published posts, public posts only.
- **GitHub repos:** verified live Nov 25, 2026 (app: 31 files / 14 commits;
  library: 593 files / 11 commits; both public, `main`, Apache 2.0).
- **WordPress post 18250:** verified live Nov 25, 2026 — the GitHub app link
  is at the top; the title typo and all other content are unchanged.

---

*Wiki index written Nov 25, 2026. It documents Nov 23–25, 2026. The app and
library repos and the WordPress post above are the live records; this file is
the human-readable index of how they came to be.*
