from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .congress import CongressClient, CongressSourceError
from .models import Document, Proposition


def safe_filename(value: str) -> str:
    text = re.sub(r'[<>:"/\\|?*]+', "-", value).strip(" .-")
    return text[:120] or "documento"


def extract_pdf_text(path: Path) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages).strip()
        return text if len(text) >= 30 else None
    except Exception:
        return None


class DocumentService:
    def __init__(self, client: CongressClient, download_dir: Path, captcha_token: str | None):
        self.client = client
        self.download_dir = download_dir
        self.captcha_token = captcha_token or ""

    def download(self, proposition: Proposition, document: Document) -> Document:
        target_dir = self.download_dir / str(proposition.parliamentary_period) / safe_filename(proposition.official_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{safe_filename(document.label)}-{safe_filename(document.official_id)}.pdf"
        if not target.exists():
            body, _ = self.client.download_document(document.original_url, self.captcha_token)
            if not body.startswith(b"%PDF"):
                raise CongressSourceError(f"El documento {document.official_id} no parece ser un PDF válido.")
            target.write_bytes(body)
        document.local_path = str(target)
        document.sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
        document.extracted_text = extract_pdf_text(target)
        document.status = "LISTO" if document.extracted_text else "PENDIENTE_OCR"
        return document
