import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from legislative_monitor.normalization import normalize_project
from legislative_monitor.storage import StateStore


class StorageTests(unittest.TestCase):
    def test_store_marks_same_source_as_unchanged(self):
        raw = json.loads((Path(__file__).parent / "fixtures/list_response.json").read_text(encoding="utf-8"))
        work_root = Path(__file__).parents[1] / "work"
        work_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=work_root) as directory:
            store = StateStore(Path(directory) / "monitor.sqlite")
            item = normalize_project(raw)
            self.assertEqual(store.upsert_proposition(item), (True, True))
            self.assertEqual(store.upsert_proposition(item), (False, False))
            raw["desEstado"] = "EN COMISIÓN"
            self.assertEqual(store.upsert_proposition(normalize_project(raw)), (False, True))
            store.close()

    def test_marks_captcha_pending_documents_for_retry(self):
        work_root = Path(__file__).parents[1] / "work"
        work_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=work_root) as directory:
            store = StateStore(Path(directory) / "monitor.sqlite")
            try:
                store.save_document("PL-1", "doc-1", None, None, "PENDIENTE_CAPTCHA")
                self.assertTrue(store.has_pending_captcha_documents("PL-1"))
                store.save_document("PL-1", "doc-1", "hash", None, "LISTO")
                self.assertFalse(store.has_pending_captcha_documents("PL-1"))
            finally:
                store.close()
