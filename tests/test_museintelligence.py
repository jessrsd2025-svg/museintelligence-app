"""Stdlib unittest suite for the MuseIntelligence ICD203 app.

All tests run offline: no network calls, no model downloads, no
GitHub account. The GitHub tests exercise the refusal paths, which
happen before any network call.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from museintelligence import github as gh  # noqa: E402
from museintelligence import market as market_mod  # noqa: E402
from museintelligence import model as model_mod  # noqa: E402
from museintelligence import render as render_mod  # noqa: E402
from museintelligence.ingest import (  # noqa: E402
    UnsupportedSourceError, ingest_file, ingest_text)
from museintelligence.provenance import (  # noqa: E402
    IncompleteProvenanceError, SourceRecord, SourceRegistry,
    canonical_sha256)
from museintelligence.quarantine import (  # noqa: E402
    RUBYGEMS_CLAIM, QuarantineStore, QuarantinedClaim)


def _record(**overrides):
    data = {
        "source_id": "SRC-TEST-001",
        "source_locator": "https://example.invalid/test",
        "retrieval_timestamp": "2026-11-25T12:00:00Z",
    }
    data.update(overrides)
    return SourceRecord(**data)


class TestProvenance(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(_record().validate(), [])

    def test_missing_source_id_rejected(self):
        self.assertIn("source_id", _record(source_id="").validate())

    def test_missing_locator_rejected(self):
        self.assertIn("source_locator",
                      _record(source_locator="").validate())

    def test_missing_timestamp_rejected(self):
        self.assertIn("retrieval_timestamp",
                      _record(retrieval_timestamp="").validate())

    def test_non_utc_timestamp_rejected(self):
        self.assertIn("retrieval_timestamp",
                      _record(
                          retrieval_timestamp="2026-11-25T12:00:00+05:00"
                      ).validate())

    def test_duplicate_source_id_rejected(self):
        registry = SourceRegistry()
        registry.register(_record())
        with self.assertRaises(ValueError):
            registry.register(_record())

    def test_register_incomplete_raises(self):
        registry = SourceRegistry()
        with self.assertRaises(IncompleteProvenanceError):
            registry.register(_record(source_locator=""))

    def test_canonical_sha_is_stable(self):
        value = {"b": 1, "a": [3, 2, 1]}
        self.assertEqual(canonical_sha256(value),
                         canonical_sha256({"a": [3, 2, 1], "b": 1}))


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.registry = SourceRegistry()
        self.docs = self.root / "documents"

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_ingest_markdown(self):
        path = self._write("note.md", "# Hello\n")
        record = ingest_file(path, source_id="SRC-TEST-MD",
                             source_locator="file://note.md",
                             retrieval_timestamp="2026-11-25T12:00:00Z",
                             registry=self.registry,
                             documents_dir=self.docs)
        self.assertEqual(record.source_id, "SRC-TEST-MD")
        self.assertEqual(len(record.sha256), 64)
        self.assertTrue((self.docs / "SRC-TEST-MD.md").is_file())

    def test_ingest_json_validates(self):
        path = self._write("data.json", '{"a": 1}')
        record = ingest_file(path, source_id="SRC-TEST-JSON",
                             source_locator="file://data.json",
                             retrieval_timestamp="2026-11-25T12:00:00Z",
                             registry=self.registry,
                             documents_dir=self.docs)
        self.assertEqual(len(record.sha256), 64)
        self.assertTrue((self.docs / "SRC-TEST-JSON.json").is_file())

    def test_ingest_invalid_json_rejected(self):
        path = self._write("bad.json", "{not json")
        with self.assertRaises(ValueError):
            ingest_file(path, source_id="SRC-TEST-BAD",
                        source_locator="file://bad.json",
                        retrieval_timestamp="2026-11-25T12:00:00Z",
                        registry=self.registry)

    def test_ingest_missing_provenance_rejected(self):
        path = self._write("note.md", "# Hello\n")
        with self.assertRaises(IncompleteProvenanceError):
            ingest_file(path, source_id="SRC-TEST-MD",
                        source_locator="",
                        retrieval_timestamp="2026-11-25T12:00:00Z",
                        registry=self.registry)

    def test_ingest_pdf_refused(self):
        path = self._write("doc.pdf", "%PDF-1.4 fake")
        with self.assertRaises(UnsupportedSourceError):
            ingest_file(path, source_id="SRC-TEST-PDF",
                        source_locator="file://doc.pdf",
                        retrieval_timestamp="2026-11-25T12:00:00Z",
                        registry=self.registry)

    def test_ingest_text(self):
        record = ingest_text("hello", source_id="SRC-TEST-TXT",
                             source_locator="inline://hello",
                             retrieval_timestamp="2026-11-25T12:00:00Z",
                             registry=self.registry,
                             documents_dir=self.docs)
        self.assertEqual(record.source_id, "SRC-TEST-TXT")
        self.assertTrue((self.docs / "SRC-TEST-TXT.md").is_file())


class TestQuarantine(unittest.TestCase):
    def test_seed_contains_rubygems(self):
        store = QuarantineStore.seeded()
        claim = store.get("CLAIM-RUBYGEMS-AI-SWARM-2026")
        self.assertIsNotNone(claim)
        assert claim is not None
        self.assertEqual(claim.epistemic_state, "QUARANTINED")
        self.assertEqual(claim.confidence, "SOURCE_REPORTED")
        self.assertEqual(claim.relationship, "QUARANTINED_AS")

    def test_add_incomplete_claim_rejected(self):
        store = QuarantineStore()
        claim = QuarantinedClaim(
            claim_id="CLAIM-TEST-001", text="a claim",
            source_id="", source_locator="",
            retrieval_timestamp="", reason="test")
        with self.assertRaises(IncompleteProvenanceError):
            store.add(claim)

    def test_route_incomplete_keeps_payload(self):
        store = QuarantineStore()
        claim = store.route_incomplete(
            claim_id="CLAIM-TEST-002", text="payload with no provenance",
            reason="INCOMPLETE_PROVENANCE")
        self.assertEqual(store.get("CLAIM-TEST-002"), claim)
        self.assertEqual(claim.reason, "INCOMPLETE_PROVENANCE")
        self.assertEqual(claim.epistemic_state, "QUARANTINED")

    def test_duplicate_claim_rejected(self):
        store = QuarantineStore.seeded()
        with self.assertRaises(ValueError):
            store.add(QuarantinedClaim.from_dict(dict(RUBYGEMS_CLAIM)))


class TestMarket(unittest.TestCase):
    def test_example_envelope_passes(self):
        ok, errors, _note = market_mod.validate_envelope(
            market_mod.example_envelope())
        self.assertTrue(ok, f"errors: {errors}")

    def test_bad_epistemic_tag_fails(self):
        envelope = market_mod.example_envelope()
        envelope["epistemic_tag"] = "VERIFIED_FACT"
        ok, errors, _note = market_mod.validate_envelope(envelope)
        self.assertFalse(ok)
        self.assertTrue(any("SENTIMENT_ONLY" in e for e in errors))

    def test_graph_mutation_true_fails(self):
        envelope = market_mod.example_envelope()
        envelope["graph_mutation_authorized"] = True
        ok, _errors, _note = market_mod.validate_envelope(envelope)
        self.assertFalse(ok)

    def test_probability_out_of_range_fails(self):
        envelope = market_mod.example_envelope()
        envelope["implied_probability_float"] = 1.5
        ok, _errors, _note = market_mod.validate_envelope(envelope)
        self.assertFalse(ok)

    def test_missing_field_fails(self):
        envelope = market_mod.example_envelope()
        del envelope["market_id"]
        ok, _errors, _note = market_mod.validate_envelope(envelope)
        self.assertFalse(ok)

    def test_additional_property_fails(self):
        envelope = market_mod.example_envelope()
        envelope["surprise"] = True
        ok, _errors, _note = market_mod.validate_envelope(envelope)
        self.assertFalse(ok)


class TestGitHub(unittest.TestCase):
    def test_fetch_refuses_branch_main(self):
        with self.assertRaises(ValueError):
            gh.fetch_bytes_at_sha("psf/requests", "main", "LICENSE")

    def test_fetch_refuses_head(self):
        with self.assertRaises(ValueError):
            gh.fetch_bytes_at_sha("psf/requests", "HEAD", "LICENSE")

    def test_fetch_refuses_short_sha(self):
        with self.assertRaises(ValueError):
            gh.fetch_bytes_at_sha("psf/requests", "abc123", "LICENSE")

    def test_fetch_refuses_64_hex(self):
        with self.assertRaises(ValueError):
            gh.fetch_bytes_at_sha(
                "psf/requests",
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                "LICENSE")

    def test_is_pinned_sha_shapes(self):
        self.assertTrue(gh.is_pinned_sha("a" * 40))
        self.assertFalse(gh.is_pinned_sha("main"))
        self.assertFalse(gh.is_pinned_sha("a" * 39))
        self.assertFalse(gh.is_pinned_sha("a" * 41))

    def test_cli_refuses_branch_ref_without_network(self):
        from museintelligence.github import _tool
        self.assertEqual(
            _tool.main(["--repo", "psf/requests", "--ref", "main",
                        "--path", "LICENSE"]), 1)

    def test_self_test_passes_offline(self):
        self.assertEqual(gh.self_test(), 0)


class TestRender(unittest.TestCase):
    def test_rendering_has_index_anchors_and_notes(self):
        sources = [_record()]
        text = render_mod.build_rendering(
            title="Test Rendering", system="Test System",
            sources=sources,
            sections=[{"heading": "Purpose", "body": "Why.",
                       "source_refs": ["SRC-TEST-001"]}],
            entities=["Test Entity"],
            links=[{"label": "Example",
                    "url": "https://example.invalid/"}],
            notes="Test notes.")
        self.assertIn("# Test Rendering", text)
        self.assertIn("1. [Purpose](#purpose)", text)
        self.assertIn("## Purpose", text)
        self.assertIn("## Entity index", text)
        self.assertIn("## Links", text)
        self.assertIn("## Rendering notes", text)
        self.assertIn("SOURCE_REPORTED", text)

    def test_rendering_rejects_dangling_source_ref(self):
        with self.assertRaises(ValueError):
            render_mod.build_rendering(
                title="Test", system="Test", sources=[_record()],
                sections=[{"heading": "Purpose", "body": "Why.",
                           "source_refs": ["SRC-NOPE"]}])


class TestModel(unittest.TestCase):
    def test_unpinned_config_is_not_available(self):
        backend = model_mod.ModelBackend(
            model_mod.ModelConfig(sha="to be pinned at build time"))
        available, reason = backend.available()
        self.assertFalse(available)
        self.assertIn("not pinned", reason)

    def test_load_unpinned_raises_cleanly(self):
        backend = model_mod.ModelBackend(
            model_mod.ModelConfig(sha="to be pinned at build time"))
        with self.assertRaises(model_mod.ModelUnavailable):
            backend.load()

    def test_generate_unpinned_raises_cleanly(self):
        backend = model_mod.ModelBackend(
            model_mod.ModelConfig(sha="to be pinned at build time"))
        with self.assertRaises(model_mod.ModelUnavailable):
            backend.generate("hello")

    def test_config_parses_example(self):
        example = (Path(__file__).resolve().parent.parent
                   / "config.example.yaml")
        config = model_mod.load_config(example)
        self.assertEqual(config.repo, "Qwen/Qwen2.5-7B-Instruct")
        self.assertEqual(config.sha, "to be pinned at build time")
        self.assertFalse(config.is_pinned)


class TestGates(unittest.TestCase):
    def test_linter_runs_on_clean_tree(self):
        from museintelligence import gates as gates_mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "note.md").write_text("# Note\n", encoding="utf-8")
            run = gates_mod.run_linter(root)
            self.assertEqual(run.total, 18)
            self.assertEqual(run.failed, 0)
            self.assertGreaterEqual(run.passed, 16)


if __name__ == "__main__":
    unittest.main()
