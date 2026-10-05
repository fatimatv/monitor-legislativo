import json
import unittest
from pathlib import Path

from legislative_monitor.normalization import attach_detail, normalize_project


ROOT = Path(__file__).parents[1]


class NormalizationTests(unittest.TestCase):
    def test_normalizes_official_identifier_and_url(self):
        raw = json.loads((ROOT / "tests/fixtures/list_response.json").read_text(encoding="utf-8"))
        item = normalize_project(raw)
        self.assertEqual(item.official_id, "00498-2026-2031-CD")
        self.assertEqual(item.number, 498)
        self.assertTrue(item.official_url.endswith("/2026/498"))

    def test_collects_document_urls_from_detail_without_schema_assumption(self):
        item = normalize_project(json.loads((ROOT / "tests/fixtures/list_response.json").read_text(encoding="utf-8")))
        attach_detail(item, {"adjuntos": [{"archivoId": 99, "descripcion": "Texto principal"}]})
        self.assertTrue(item.documents[0].original_url.endswith("/archivo/99/pdf"))
