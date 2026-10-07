import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SchedulerScriptTests(unittest.TestCase):
    def test_daily_runner_prefers_current_source_tree(self):
        source = (ROOT / "scripts" / "run-daily.ps1").read_text(encoding="utf-8")

        self.assertIn("$env:PYTHONPATH = (Join-Path $ProjectRoot 'src')", source)

