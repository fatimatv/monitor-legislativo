import json
import unittest
from pathlib import Path

from legislative_monitor.classification import RuleClassifier
from legislative_monitor.config import load_topics
from legislative_monitor.normalization import normalize_project


ROOT = Path(__file__).parents[1]


def project(title: str):
    raw = json.loads((ROOT / "tests/fixtures/list_response.json").read_text(encoding="utf-8"))
    raw["titulo"] = title
    return normalize_project(raw)


class ClassificationTests(unittest.TestCase):
    def test_classifies_social_networks_as_relevant(self):
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(project("Regulación de plataformas y redes sociales para menores"))
        self.assertTrue(result.relevant)
        self.assertIn("Plataformas y comercio digital", result.categories)

    def test_rejects_road_project_without_digital_context(self):
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(project("Ley de infraestructura vial para rutas nacionales"))
        self.assertFalse(result.relevant)
