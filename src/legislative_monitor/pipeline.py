from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import date

from .analysis import EvidenceAnalyzer
from .classification import RuleClassifier
from .congress import CongressClient, CongressSourceError
from .documents import DocumentService
from .google_workspace import GoogleWorkspace
from .models import Proposition
from .normalization import attach_detail
from .storage import StateStore

LOG = logging.getLogger(__name__)


@dataclass
class RunSummary:
    found: int = 0
    evaluated: int = 0
    relevant: int = 0
    discarded: int = 0
    processed: int = 0
    documents_downloaded: int = 0
    errors: int = 0


class MonitorPipeline:
    def __init__(
        self,
        congress: CongressClient,
        classifier: RuleClassifier,
        analyzer: EvidenceAnalyzer,
        documents: DocumentService,
        store: StateStore | None,
        workspace: GoogleWorkspace | None,
        dry_run: bool,
        download_documents: bool = True,
    ):
        self.congress = congress
        self.classifier = classifier
        self.analyzer = analyzer
        self.documents = documents
        self.store = store
        self.workspace = workspace
        self.dry_run = dry_run
        self.download_documents = download_documents

    def run(self, periods: list[int], start_date: date | None) -> RunSummary:
        summary = RunSummary()
        run_id = self.store.start_run("DRY-RUN" if self.dry_run else "SYNC") if self.store else None
        try:
            for period in periods:
                for proposition in self.congress.iter_projects(period, start_date):
                    self._process(proposition, summary)
            if self.store and run_id:
                self.store.finish_run(run_id, "OK", asdict(summary))
        except Exception:
            if self.store and run_id:
                self.store.finish_run(run_id, "ERROR", asdict(summary))
            raise
        return summary

    def _process(self, proposition: Proposition, summary: RunSummary) -> None:
        summary.found += 1
        summary.evaluated += 1
        try:
            detail = self.congress.detail(proposition.parliamentary_period, proposition.number, proposition.chamber_code)
            attach_detail(proposition, detail)
        except CongressSourceError as exc:
            LOG.warning("Detalle pendiente para %s: %s", proposition.official_id, exc)
        proposition.classification = self.classifier.classify(proposition)
        if not proposition.classification.relevant:
            summary.discarded += 1
            return
        summary.relevant += 1
        is_new = changed = True
        status = None
        if self.store:
            is_new, changed = self.store.upsert_proposition(proposition)
            status = self.store.processing_status(proposition.official_id)
        if (
            not self.dry_run
            and not is_new
            and not changed
            and status == "PROCESADO"
            and not self.store.has_pending_captcha_documents(proposition.official_id)
        ):
            LOG.info("Sin cambios: %s", proposition.official_id)
            return
        try:
            self._enrich_and_sync(proposition, summary)
            summary.processed += 1
        except Exception as exc:  # El expediente aislado no detiene el lote.
            summary.errors += 1
            LOG.exception("Fallo al procesar %s", proposition.official_id)
            if self.store:
                self.store.set_status(proposition.official_id, "ERROR", str(exc)[:1000])

    def _enrich_and_sync(self, proposition: Proposition, summary: RunSummary) -> None:
        if self.download_documents:
            for document in proposition.documents:
                if self.store and self.store.document_known(proposition.official_id, document.official_id):
                    continue
                try:
                    self.documents.download(proposition, document)
                    summary.documents_downloaded += 1
                    if self.store:
                        self.store.save_document(proposition.official_id, document.official_id, document.sha256, None, document.status)
                except CongressSourceError as exc:
                    LOG.warning("Documento pendiente (%s): %s", document.official_id, exc)
                    if self.store:
                        self.store.save_document(proposition.official_id, document.official_id, None, None, "PENDIENTE_CAPTCHA")
        proposition.analysis = self.analyzer.analyze(proposition)
        if self.dry_run:
            LOG.info("DRY-RUN %s: %s", proposition.official_id, proposition.analysis.status)
            return
        drive_url = ""
        download_link = next((item.original_url for item in proposition.documents), "")
        if self.workspace:
            folder_id, drive_url = self.workspace.proposition_folder(proposition)
            for document in proposition.documents:
                if document.local_path:
                    document.drive_file_id = self.workspace.upload_document(folder_id, document)
                    if self.store:
                        self.store.save_document(proposition.official_id, document.official_id, document.sha256, document.drive_file_id, document.status)
            self.workspace.upsert_sheet_row(proposition, drive_url, download_link)
        status = "PROCESADO" if proposition.analysis.status == "ANALIZADO" else proposition.analysis.status
        if self.store:
            self.store.set_status(proposition.official_id, status)
