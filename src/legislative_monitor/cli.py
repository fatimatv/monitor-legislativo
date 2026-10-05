from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path

from .analysis import EvidenceAnalyzer
from .classification import RuleClassifier
from .config import Settings, load_topics
from .congress import CongressClient
from .documents import DocumentService
from .google_workspace import GoogleWorkspace, GoogleWorkspaceError
from .pipeline import MonitorPipeline
from .storage import StateStore


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor legislativo digital del Congreso del Perú")
    parser.add_argument("mode", choices=["daily", "backfill", "dry-run"])
    parser.add_argument("--start-date", type=date.fromisoformat, help="Fecha inicial YYYY-MM-DD (obligatoria en backfill)")
    parser.add_argument("--period", type=int, action="append", help="Período parlamentario; repetible")
    return parser.parse_args()


def main() -> None:
    load_dotenv(Path(".env"))
    args = parse_args()
    settings = Settings.from_env()
    logging.basicConfig(level=os.getenv("MONITOR_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if args.mode == "backfill" and not args.start_date:
        raise SystemExit("BACKFILL requiere --start-date YYYY-MM-DD para evitar una descarga histórica accidental.")
    congress = CongressClient(settings.timeout_seconds, settings.max_retries, settings.page_size)
    periods_metadata = congress.periods()
    if args.period:
        periods = args.period
    elif args.mode == "backfill":
        periods = [int(item["perParId"]) for item in periods_metadata if date.fromisoformat(str(item["fecFin"])[:10]) >= args.start_date]
    else:
        periods = [congress.current_period()]
    start_date = args.start_date if args.mode == "backfill" else date.today() - timedelta(days=settings.lookback_days)
    dry_run = args.mode == "dry-run"
    store = None if dry_run else StateStore(settings.db_path)
    workspace = None
    if not dry_run and all([settings.google_service_account_file, settings.google_drive_root_folder_id, settings.google_sheet_id]):
        try:
            workspace = GoogleWorkspace(settings.google_service_account_file, settings.google_drive_root_folder_id, settings.google_sheet_id)
        except GoogleWorkspaceError as exc:
            logging.getLogger(__name__).warning("Google Workspace no disponible: %s", exc)
    elif not dry_run:
        logging.getLogger(__name__).warning("Google Workspace no configurado; se conserva estado local y se omite la sincronización remota.")
    pipeline = MonitorPipeline(
        congress=congress,
        classifier=RuleClassifier(load_topics(settings.topics_path)),
        analyzer=EvidenceAnalyzer(),
        documents=DocumentService(congress, settings.downloads_dir, settings.captcha_token),
        store=store,
        workspace=workspace,
        dry_run=dry_run,
    )
    try:
        summary = pipeline.run(periods, start_date)
        print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
    finally:
        if store:
            store.close()


if __name__ == "__main__":
    main()
