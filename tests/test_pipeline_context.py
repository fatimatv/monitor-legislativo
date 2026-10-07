import json
import unittest
from pathlib import Path

from legislative_monitor.analysis import EvidenceAnalyzer
from legislative_monitor.classification import RuleClassifier
from legislative_monitor.config import load_topics
from legislative_monitor.normalization import normalize_project
from legislative_monitor.pipeline import MonitorPipeline, RunSummary


ROOT = Path(__file__).parents[1]


class DetailCongress:
    def __init__(self):
        self.calls = 0

    def detail(self, period, number, chamber):
        self.calls += 1
        return {"general": {"sumilla": "Regula sistemas de videovigilancia vehicular."}}


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
