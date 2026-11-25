"""Stdlib-only web UI (http.server).

Pages: dashboard (OODA status), documents / renderings, provenance
view, quarantine view, gates runner (runs the 18-gate linter and
shows per-gate results), sentiment-envelope viewer, and the
TOOL-GH-01 GitHub panel. No external assets — the UI works offline
except for model and GitHub calls, which the user triggers
explicitly.

All dynamic content is HTML-escaped. The server binds to
127.0.0.1 by default.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import gates as gates_mod
from . import github as gh
from . import market as market_mod
from . import model as model_mod
from . import render as render_mod
from .provenance import SourceRegistry, SourceRecord
from .quarantine import QuarantineStore

CSS = """
body{font-family:system-ui,sans-serif;margin:0 auto;max-width:900px;
padding:0 16px 48px;color:#1a1a1a;background:#fdfdf8}
nav{background:#1a1a2e;color:#fff;padding:10px 16px;margin:0 -16px 20px}
nav a{color:#9ecbff;margin-right:14px;text-decoration:none}
nav a:hover{text-decoration:underline}
h1{font-size:1.6em}h2{font-size:1.25em;border-bottom:1px solid #ccc;
padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:12px 0}
th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;
vertical-align:top}
th{background:#eee}
.pass{color:#0a6e0a;font-weight:bold}.fail{color:#b00020;font-weight:bold}
.manual{color:#8a6d00;font-weight:bold}
.tag{background:#eee;border-radius:4px;padding:1px 6px;font-size:.85em}
pre{background:#f4f4f4;padding:12px;overflow:auto}
code{background:#f4f4f4;padding:0 3px}
.card{border:1px solid #ccc;border-radius:6px;padding:12px;margin:12px 0}
"""

NAV = [("/", "Dashboard"), ("/documents", "Documents"),
       ("/renderings", "Renderings"), ("/provenance", "Provenance"),
       ("/quarantine", "Quarantine"), ("/gates", "Gates"),
       ("/market", "Sentiment"), ("/github", "GitHub")]


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _md_to_html(text: str) -> str:
    """Minimal markdown-to-HTML for rendering pages: headings,
    lists, tables, bold, italics, code spans, links, rules."""
    out: list[str] = []
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            block = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            out.append("<pre>" + _esc("\n".join(block)) + "</pre>")
            continue
        match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if match:
            level = len(match.group(1))
            out.append(f"<h{level}>" + _inline(match.group(2)) + f"</h{level}>")
            index += 1
            continue
        if stripped == "---":
            out.append("<hr>")
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[index + 1].strip()):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            rows = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append([c.strip() for c in
                             lines[index].strip().strip("|").split("|")])
                index += 1
            table = ["<table><thead><tr>" + "".join(
                f"<th>{_inline(c)}</th>" for c in header) + "</tr></thead><tbody>"]
            for row in rows:
                table.append("<tr>" + "".join(
                    f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
            table.append("</tbody></table>")
            out.append("".join(table))
            continue
        if stripped.startswith(("- ", "* ")) or re.match(r"^\d+\.\s", stripped):
            items = []
            while index < len(lines):
                item = lines[index].strip()
                item = re.sub(r"^[-*]\s+|^\d+\.\s+", "", item)
                if not item:
                    break
                items.append(f"<li>{_inline(item)}</li>")
                index += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        out.append(f"<p>{_inline(stripped)}</p>")
        index += 1
    return "\n".join(out)


def _inline(text: str) -> str:
    text = _esc(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


class AppContext:
    """Shared state for the UI: repo root, data directory, stores."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.data_dir = self.repo_root / "data"
        self.registry = SourceRegistry(self.data_dir / "registry.json")
        self.quarantine = QuarantineStore(self.data_dir / "quarantine.json")
        self.config = model_mod.load_config()
        self.backend = model_mod.ModelBackend(self.config)
        self.last_gate_run: gates_mod.GateRun | None = None

    def renderings(self) -> list[Path]:
        folder = self.data_dir / "renderings"
        if not folder.is_dir():
            return []
        return sorted(folder.glob("*.md"))

    def build_example_rendering(self) -> Path:
        """Build the example rendering from the spec's own content
        (GENERATED_ANALYSIS) and save it under data/renderings/."""
        sources = self.registry.all()
        if not sources:
            sources = [SourceRecord(
                source_id="SRC-GEMINI-ICD203-2026-11-23",
                source_locator="https://share.gemini.google/gPK7Vf1HHMx6",
                retrieval_timestamp="2026-11-23T00:00:00Z",
                kind="conversation")]
        sections = [
            {"heading": "Purpose",
             "body": ("The MuseIntelligence ICD203 app is a reading-room "
                      "and governance app for the LIBERTAS // VERITAS // "
                      "AEQUITAS system. It ingests documents and shared AI "
                      "conversations, renders them as a browsable markdown "
                      "wiki/index, and governs every claim with provenance, "
                      "epistemic tags, and the 18-gate acceptance "
                      "checklist."),
             "source_refs": ["SRC-GEMINI-ICD203-2026-11-23"]},
            {"heading": "Architecture",
             "body": ("Observe → Orient → Decide → Act (OODA), with the "
                      "Capture → Analyze → Strategize → Execute pipeline. "
                      "The OBSERVE panel supplies the observation tools; "
                      "the 18-gate checklist is the decision gate for "
                      "everything the app ships."),
             "source_refs": ["SRC-GEMINI-ICD203-2026-11-23"]},
            {"heading": "Runtime model — open-source backend",
             "body": ("The app's engine is Qwen/Qwen2.5-7B-Instruct "
                      "(Apache 2.0, Hugging Face), loaded only at a "
                      "commit SHA pinned at build time. Google AI Studio "
                      "is the build environment only."),
             "source_refs": ["SRC-GEMINI-ICD203-2026-11-23"]},
        ]
        text = render_mod.build_rendering(
            title="Renderings: MuseIntelligence ICD203 — Gemini Conversation",
            system="MuseIntelligence ICD203",
            sources=sources,
            sections=sections,
            entities=["Gemini", "MuseIntelligence", "ICD203",
                      "Qwen/Qwen2.5-7B-Instruct", "Hugging Face",
                      "TOOL-GH-01", "TOOL-MKT-01"],
            links=[{"label": "Gemini conversation — share link",
                    "url": "https://share.gemini.google/gPK7Vf1HHMx6"},
                   {"label": "Qwen/Qwen2.5-7B-Instruct — model repo",
                    "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"}],
            notes=("Example rendering built by the app from the "
                   "MuseIntelligence ICD203 Gemini specification. All "
                   "claims are SOURCE_REPORTED (GENERATED_ANALYSIS), "
                   "never VERIFIED_FACT."))
        target = self.data_dir / "renderings" / "museintelligence-icd203-gemini.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target


def _page(ctx: AppContext, title: str, body: str) -> bytes:
    nav = "".join(f'<a href="{href}">{label}</a>' for href, label in NAV)
    doc = (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
           f"<title>{_esc(title)} — MuseIntelligence ICD203</title>"
           f"<style>{CSS}</style></head><body>"
           f"<nav><strong>MuseIntelligence ICD203</strong> &nbsp; {nav}</nav>"
           f"<h1>{_esc(title)}</h1>{body}</body></html>")
    return doc.encode("utf-8")


def _status_badge(status: str) -> str:
    cls = {"PASS": "pass", "FAIL": "fail", "MANUAL": "manual"}.get(status, "")
    return f'<span class="{cls}">{_esc(status)}</span>'


class MuseRequestHandler(BaseHTTPRequestHandler):
    ctx: AppContext  # set by make_server

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def _send(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 — BaseHTTPRequestHandler naming
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        route = parsed.path.rstrip("/") or "/"
        try:
            if route == "/":
                self._send(_page(self.ctx, "Dashboard", self._dashboard()))
            elif route == "/documents":
                self._send(_page(self.ctx, "Documents", self._documents()))
            elif route == "/renderings":
                if query.get("build") == ["1"]:
                    target = self.ctx.build_example_rendering()
                    body = (f"<p>Built example rendering: "
                            f"<code>{_esc(target.name)}</code></p>"
                            f"<p><a href='/renderings/{_esc(target.name)}'>"
                            f"View it</a></p>")
                    self._send(_page(self.ctx, "Renderings", body))
                else:
                    self._send(_page(self.ctx, "Renderings",
                                     self._renderings()))
            elif route.startswith("/renderings/"):
                name = urllib.parse.unquote(route[len("/renderings/"):])
                self._send(_page(self.ctx, "Rendering",
                                 self._rendering(name)))
            elif route == "/provenance":
                self._send(_page(self.ctx, "Provenance",
                                 self._provenance()))
            elif route == "/quarantine":
                self._send(_page(self.ctx, "Quarantine",
                                 self._quarantine()))
            elif route == "/gates":
                if query.get("run") == ["1"]:
                    self.ctx.last_gate_run = gates_mod.run_linter(
                        self.ctx.repo_root)
                self._send(_page(self.ctx, "18-Gate Checklist",
                                 self._gates()))
            elif route == "/market":
                self._send(_page(self.ctx, "Sentiment Envelope",
                                 self._market()))
            elif route == "/github":
                self._send(_page(self.ctx, "GitHub — TOOL-GH-01",
                                 self._github(query)))
            else:
                self._send(_page(self.ctx, "Not found",
                                 "<p>Unknown page. "
                                 "<a href='/'>Back to dashboard</a></p>"),
                           status=404)
        except Exception as exc:  # noqa: BLE001 — show, don't crash
            self._send(_page(self.ctx, "Error",
                             f"<p>Something went wrong: {_esc(exc)}</p>"),
                       status=500)

    def do_POST(self):  # noqa: N802 — BaseHTTPRequestHandler naming
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.rstrip("/") == "/market/validate":
            length = int(self.headers.get("Content-Length", "0"))
            fields = urllib.parse.parse_qs(
                self.rfile.read(length).decode("utf-8", errors="replace"))
            raw = fields.get("envelope", [""])[0]
            try:
                envelope = json.loads(raw)
                ok, errors, note = market_mod.validate_envelope(envelope)
                if ok:
                    result = ("<p class='pass'>Envelope valid.</p>"
                              f"<p>{_esc(note)}</p>")
                else:
                    items = "".join(f"<li>{_esc(e)}</li>" for e in errors)
                    result = ("<p class='fail'>Envelope invalid.</p>"
                              f"<ul>{items}</ul><p>{_esc(note)}</p>")
            except (json.JSONDecodeError, ValueError) as exc:
                result = f"<p class='fail'>Not valid JSON: {_esc(exc)}</p>"
            body = (result + "<p><a href='/market'>Back to the "
                             "sentiment viewer</a></p>")
            self._send(_page(self.ctx, "Envelope validation", body))
            return
        self._send(_page(self.ctx, "Not found",
                         "<p>Unknown page.</p>"), status=404)

    # -- pages -----------------------------------------------------

    def _dashboard(self) -> str:
        ctx = self.ctx
        available, reason = ctx.backend.available()
        model_status = ("<span class='pass'>Available</span>" if available
                        else "<span class='manual'>Unavailable</span>")
        gates = ctx.last_gate_run
        gates_line = ("Not run yet — <a href='/gates?run=1'>run the "
                      "checklist</a>" if gates is None else
                      f"{gates.summary_line()} "
                      f"(exit {gates.exit_code})")
        return f"""
<div class="card"><h2>Observe</h2><p>{len(ctx.registry)} source(s)
registered. <a href="/documents">Documents</a> ·
<a href="/provenance">Provenance</a></p></div>
<div class="card"><h2>Orient</h2><p>Governance precedence: Human-Approved
Policy &gt; AGENTS.md &gt; AEQUITAS Gate &gt; Task Contract &gt;
CHAIN.md Dispatch &gt; Model Preference. Modes: Spatial, Convergent.
</p></div>
<div class="card"><h2>Decide</h2><p>18-gate checklist: {gates_line}</p>
<p>Quarantined claims: {len(ctx.quarantine)} — see
<a href="/quarantine">Quarantine</a>. Model: {model_status} —
{_esc(reason)}</p></div>
<div class="card"><h2>Act</h2><p>{len(ctx.renderings())} rendering(s)
built. <a href="/renderings">Renderings</a> ·
<a href="/renderings?build=1">Build the example rendering</a></p></div>
<p>All claims are SOURCE_REPORTED until a human reviews the source.
Nothing here assigns VERIFIED_FACT.</p>"""

    def _documents(self) -> str:
        rows = "".join(
            f"<tr><td><code>{_esc(r.source_id)}</code></td>"
            f"<td>{_esc(r.source_locator)}</td>"
            f"<td>{_esc(r.retrieval_timestamp)}</td>"
            f"<td>{_esc(r.kind)}</td>"
            f"<td><code>{_esc(r.sha256[:16])}…</code></td></tr>"
            for r in self.ctx.registry.all())
        files = sorted(
            (self.ctx.data_dir / "documents").glob("*")) \
            if (self.ctx.data_dir / "documents").is_dir() else []
        stored = "".join(f"<li><code>{_esc(p.name)}</code></li>"
                         for p in files)
        return f"""
<p>Ingested sources, each registered with source_id, source_locator
and retrieval_timestamp. Ingest is done with
<code>museintelligence.ingest</code> (see README); .pdf is refused
until text extraction is implemented.</p>
<table><thead><tr><th>source_id</th><th>locator</th><th>retrieved</th>
<th>kind</th><th>sha256</th></tr></thead><tbody>{rows or
'<tr><td colspan="5">No sources registered yet.</td></tr>'}
</tbody></table>
<h2>Stored files</h2><ul>{stored or '<li>None yet.</li>'}</ul>"""

    def _renderings(self) -> str:
        items = "".join(
            f"<li><a href='/renderings/{_esc(p.name)}'>{_esc(p.name)}</a>"
            f"</li>" for p in self.ctx.renderings())
        return f"""
<p>Renderings in the Renderings.md canonical format (index with
anchors, sections, entity/link indexes, rendering notes).</p>
<ul>{items or '<li>No renderings yet.</li>'}</ul>
<p><a href="/renderings?build=1">Build the example rendering</a></p>"""

    def _rendering(self, name: str) -> str:
        if "/" in name or "\\" in name or name.startswith("."):
            return "<p>Invalid rendering name.</p>"
        target = self.ctx.data_dir / "renderings" / name
        if not target.is_file() or target.suffix.lower() != ".md":
            return "<p>Rendering not found.</p>"
        return _md_to_html(target.read_text(encoding="utf-8"))

    def _provenance(self) -> str:
        rows = "".join(
            f"<tr><td><code>{_esc(r.source_id)}</code></td>"
            f"<td>{_esc(r.source_locator)}</td>"
            f"<td>{_esc(r.retrieval_timestamp)}</td>"
            f"<td>{'yes' if r.human_reviewed else 'no'}</td>"
            f"<td><code>{_esc(r.sha256)}</code></td></tr>"
            for r in self.ctx.registry.all())
        return f"""
<p>Every source object carries a source_id, a stable source_locator,
and a UTC retrieval_timestamp. A payload lacking any of the three is
INCOMPLETE_PROVENANCE and is refused at ingest.</p>
<table><thead><tr><th>source_id</th><th>locator</th><th>retrieved</th>
<th>human-reviewed</th><th>sha256 (canonical content)</th></tr></thead>
<tbody>{rows or '<tr><td colspan="5">Registry is empty.</td></tr>'}
</tbody></table>"""

    def _quarantine(self) -> str:
        claims = self.ctx.quarantine.all()
        if not claims:
            return "<p>No quarantined claims.</p>"
        cards = ""
        for claim in claims:
            cards += f"""
<div class="card"><h2>{_esc(claim.claim_id)}</h2>
<p>{_esc(claim.text)}</p>
<p><span class="tag">{_esc(claim.epistemic_state)}</span>
<span class="tag">{_esc(claim.confidence)}</span></p>
<p><strong>Reason:</strong> {_esc(claim.reason)}</p>
<p><strong>Temporal reference:</strong>
{_esc(claim.temporal_reference)}</p>
<p><strong>Source:</strong> <code>{_esc(claim.source_id)}</code> —
{_esc(claim.source_locator)} — retrieved
{_esc(claim.retrieval_timestamp)}</p>
<p>Human review is required before any promotion. This item is never
settled fact.</p></div>"""
        return cards

    def _gates(self) -> str:
        run = self.ctx.last_gate_run
        if run is None:
            return ("<p>The 18-gate acceptance checklist has not been run "
                    "in this session.</p><p><a href='/gates?run=1'>Run the "
                    "checklist now</a></p>")
        rows = "".join(
            f"<tr><td><code>{_esc(r.gate)}</code></td>"
            f"<td>{_esc(r.name)}</td><td>{_status_badge(r.status)}</td>"
            f"<td>{_esc(r.note)}</td>"
            f"<td>{'<br>'.join(_esc(f) for f in r.findings)}</td></tr>"
            for r in run.results)
        return f"""
<p>{_esc(run.summary_line())} — exit code {run.exit_code}.
D2 and E3 are MANUAL by design and are confirmed by a human, not by
the scan.</p>
<p><a href="/gates?run=1">Run again</a></p>
<table><thead><tr><th>Gate</th><th>Name</th><th>Status</th><th>Note</th>
<th>Findings</th></tr></thead><tbody>{rows}</tbody></table>"""

    def _market(self) -> str:
        envelope = market_mod.example_envelope()
        ok, errors, note = market_mod.validate_envelope(envelope)
        status = ("<p class='pass'>Example envelope valid.</p>" if ok
                  else "<p class='fail'>Example envelope invalid.</p>"
                  + "".join(f"<li>{_esc(e)}</li>" for e in errors))
        pretty = _esc(json.dumps(envelope, indent=2, sort_keys=True))
        return f"""
<p>Market-sentiment envelopes are crowd-sentiment snapshots — never
event evidence. <span class="tag">SENTIMENT_ONLY</span>,
graph_mutation_authorized is false, human_review_required is true,
confidence_weight is 0.0.</p>
{status}<p>{_esc(note)}</p>
<pre>{pretty}</pre>
<h2>Validate an envelope</h2>
<form method="post" action="/market/validate">
<textarea name="envelope" rows="12" cols="80"
placeholder='{{"market_id": "...", ...}}'></textarea><br>
<input type="submit" value="Validate envelope"></form>"""

    def _github(self, query: dict) -> str:
        body = """
<p>All GitHub reads go through TOOL-GH-01 (tools/github_call.py):
pin a ref to a commit SHA, then fetch only at that SHA. Branch names
are refused. <strong>commit_sha is the anchor; branch names are
not.</strong></p>
<p><a href="/github?selftest=1">Run the offline self-test</a></p>
<form method="get" action="/github">
<label>Repo (owner/name): <input name="repo" value="psf/requests"
size="24"></label>
<label>Ref (tag or 40-hex SHA — branch names are refused):
<input name="ref" value="v2.32.3" size="24"></label>
<label>Path: <input name="path" value="LICENSE" size="24"></label>
<input type="submit" value="Pin and fetch"></form>"""
        if query.get("selftest") == ["1"]:
            result = gh.self_test()
            body += (f"<p>Self-test exit code: {result} "
                     f"({'passed' if result == 0 else 'failed'})</p>")
        repo = query.get("repo", [None])[0]
        ref = query.get("ref", [None])[0]
        path = query.get("path", [None])[0]
        if repo and ref:
            try:
                anchor = gh.GitHubAnchor(repo)
                sha = anchor.pin(ref)
                body += (f"<p>Pinned <code>{_esc(repo)}@{_esc(ref)}</code> "
                         f"to <code>{_esc(sha)}</code></p>")
                if path:
                    data = anchor.fetch(path)
                    body += (f"<p>Fetched <code>{_esc(path)}</code>: "
                             f"{len(data)} bytes, SHA-256 "
                             f"<code>{_esc(anchor.digest(data))}</code></p>")
            except (ValueError, RuntimeError) as exc:
                body += f"<p class='fail'>Refused or failed: {_esc(exc)}</p>"
        return body


def make_server(ctx: AppContext, host: str = "127.0.0.1",
                port: int = 8000) -> ThreadingHTTPServer:
    """Build the HTTP server for a context (does not start it)."""
    handler = type("BoundHandler", (MuseRequestHandler,), {"ctx": ctx})
    return ThreadingHTTPServer((host, port), handler)


def serve(repo_root: str | Path | None = None, host: str = "127.0.0.1",
          port: int = 8000) -> None:
    """Start the web UI (blocking)."""
    root = Path(repo_root).resolve() if repo_root is not None else \
        Path(__file__).resolve().parent.parent
    ctx = AppContext(root)
    server = make_server(ctx, host, port)
    print(f"MuseIntelligence ICD203 — http://{host}:{port}/ "
          "(Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
