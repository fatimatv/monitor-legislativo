import unittest
from pathlib import Path


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
