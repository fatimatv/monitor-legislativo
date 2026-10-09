import json
import unittest
from pathlib import Path

from legislative_monitor.analysis import EvidenceAnalyzer
from legislative_monitor.classification import RuleClassifier
from legislative_monitor.config import load_topics
from legislative_monitor.normalization import normalize_project
from legislative_monitor.pipeline import MonitorPipeline, RunSummary
from legislative_monitor.models import Document


ROOT = Path(__file__).parents[1]


class DetailCongress:
    def __init__(self):
        self.calls = 0

    def detail(self, period, number, chamber):
        self.calls += 1
        return {"general": {"sumilla": "Regula sistemas de videovigilancia vehicular."}}


class FailingDocuments:
    def __init__(self):
        self.calls = 0

    def download(self, proposition, document):
        self.calls += 1
        raise AssertionError("No debe descargar documentos en modo solo metadatos")


class PipelineContextTests(unittest.TestCase):
    def test_enriches_official_detail_before_classification(self):
        raw = json.loads((ROOT / "tests/fixtures/list_response.json").read_text(encoding="utf-8"))
        raw["titulo"] = "Proposición sobre transporte terrestre"
        proposition = normalize_project(raw)
        congress = DetailCongress()
        pipeline = MonitorPipeline(
            congress=congress,
            classifier=RuleClassifier(load_topics(ROOT / "config/topics.json")),
            analyzer=EvidenceAnalyzer(),
            documents=None,
            store=None,
            workspace=None,
            dry_run=True,
        )
        summary = RunSummary()

        pipeline._process(proposition, summary)

        self.assertEqual(congress.calls, 1)
        self.assertEqual(summary.relevant, 1)
        self.assertEqual(summary.processed, 1)

    def test_metadata_only_sync_skips_blocked_document_downloads(self):
        raw = json.loads((ROOT / "tests/fixtures/list_response.json").read_text(encoding="utf-8"))
        raw["titulo"] = "Propuesta sobre videovigilancia"
        proposition = normalize_project(raw)
        proposition.documents.append(Document("anexo-1", "Anexo", "https://example.invalid/anexo.pdf"))
        documents = FailingDocuments()
        pipeline = MonitorPipeline(
            congress=DetailCongress(),
            classifier=RuleClassifier(load_topics(ROOT / "config/topics.json")),
            analyzer=EvidenceAnalyzer(),
            documents=documents,
            store=None,
            workspace=None,
            dry_run=False,
            download_documents=False,
        )
        summary = RunSummary()

        pipeline._process(proposition, summary)

        self.assertEqual(documents.calls, 0)
        self.assertEqual(summary.processed, 1)
