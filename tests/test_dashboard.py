import unittest
from unittest.mock import patch
from pathlib import Path

from api import health
from legislative_monitor.normalization import normalize_project


ROOT = Path(__file__).parents[1]


class DashboardTests(unittest.TestCase):
    def test_defaults_to_digital_signal_and_offers_all_initiatives_toggle(self):
        source = (ROOT / "api" / "health.py").read_text(encoding="utf-8")

        self.assertIn('id="scope"', source)
        self.assertIn("let data=[],showAll=false", source)
        self.assertIn("showAll||p.tags.length", source)

    def test_dashboard_taxonomy_includes_new_digital_search_terms(self):
        source = (ROOT / "api" / "health.py").read_text(encoding="utf-8")

        for term in ("billetera digital", "dinero electrónico", "paytech", "derechos digitales", "aplicación móvil", "transformación digital"):
            with self.subTest(term=term):
                self.assertIn(term, source)

    @patch.object(health, "official_json", return_value={"data": [{"perParId": 2026, "fecIni": "2026-01-01", "fecFin": "2099-12-31", "desPerParAbrev": "2026-2031"}]})
    @patch.object(health, "CongressClient")
    def test_dashboard_uses_official_detail_and_full_recent_window(self, congress_type, _official_json):
        raw = {"proyectoLey": "PL-TEST", "titulo": "Proposición general sobre transporte", "perParId": 2026, "pleyNum": 999, "codTipoParl": "D", "fecPresentacion": "2026-10-06", "desEstado": "PRESENTADO"}
        proposition = normalize_project(raw)
        congress_type.return_value.iter_projects.return_value = [proposition]
        congress_type.return_value.detail.return_value = {"general": {"sumilla": "Garantiza derechos digitales de las personas usuarias."}}

        payload = health.latest_projects()

        self.assertEqual(payload["projects"][0]["id"], "PL-TEST")
        self.assertIn("Derechos digitales", payload["projects"][0]["tags"])
