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

    def test_classifies_videovigilance_as_data_and_privacy(self):
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(project("Derecho de acceso a información de sistemas de videovigilancia vehicular"))
        self.assertTrue(result.relevant)
        self.assertIn("Datos y privacidad", result.categories)

    def test_classifies_term_found_in_official_summary_and_identifies_source(self):
        item = project("Proposición sobre transporte terrestre")
        item.source_data["detail"] = {"general": {"sumilla": "Regula el acceso a información de videovigilancia vehicular."}}
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(item)
        self.assertTrue(result.relevant)
        self.assertIn("Datos y privacidad", result.categories)
        self.assertIn("sumilla oficial", result.rationale)

    def test_classifies_regulated_service_compensations_as_potential_digital_impact(self):
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(project("Compensaciones automáticas por interrupciones de servicios regulados"))
        self.assertTrue(result.relevant)
        self.assertIn("Servicios regulados y usuarios digitales", result.categories)

    def test_classifies_remote_betting_as_digital_platform_market(self):
        result = RuleClassifier(load_topics(ROOT / "config/topics.json")).classify(project("Impuesto a juegos a distancia y apuestas deportivas a distancia"))
        self.assertTrue(result.relevant)
        self.assertIn("Plataformas y comercio digital", result.categories)
