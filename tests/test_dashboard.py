import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DashboardTests(unittest.TestCase):
    def test_defaults_to_digital_signal_and_offers_all_initiatives_toggle(self):
        source = (ROOT / "api" / "health.py").read_text(encoding="utf-8")

        self.assertIn('id="scope"', source)
        self.assertIn("let data=[],showAll=false", source)
        self.assertIn("showAll||p.tags.length", source)
