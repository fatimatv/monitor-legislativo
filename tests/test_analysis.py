import unittest

from legislative_monitor.analysis import EvidenceAnalyzer
from legislative_monitor.models import Classification, Document, Proposition


class AnalysisTests(unittest.TestCase):
    def test_analysis_labels_evidence_and_interpretation(self):
        item = Proposition("001", 1, 2026, "D", None, "Ley de plataformas", "PRESENTADO", "", "", "https://example.test")
        item.classification = Classification(True, ["Plataformas y comercio digital"], "ALTA", "prueba")
        item.documents = [Document("d", "texto", "https://example.test", extracted_text="Las plataformas deberán informar sus mecanismos de moderación.")]
        analysis = EvidenceAnalyzer().analyze(item)
        self.assertIn("HECHO NORMATIVO:", analysis.obligations)
        self.assertIn("INTERPRETACIÓN:", analysis.impact)

