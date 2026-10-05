from __future__ import annotations

from datetime import date
from typing import Any

from .models import Document, Proposition


APP_URL = "https://wb2server.congreso.gob.pe/spley-portal/#/diputados/expediente"
API_URL = "https://api.congreso.gob.pe/spley-portal-service"


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def normalize_project(raw: dict[str, Any]) -> Proposition:
    period = int(raw["perParId"])
    number = int(raw["pleyNum"])
    chamber = str(raw.get("codTipoParlActual") or raw.get("codTipoParl") or "D")
    official_id = str(raw.get("proyectoLey") or f"{number:05d}-{period}")
    return Proposition(
        official_id=official_id,
        number=number,
        parliamentary_period=period,
        chamber_code=chamber,
        presented_on=parse_date(raw.get("fecPresentacion")),
        title=str(raw.get("titulo") or "").strip(),
        procedural_status=str(raw.get("desEstado") or "").strip(),
        proponent=str(raw.get("desProponente") or "").strip(),
        authors=str(raw.get("autores") or "").strip(),
        official_url=f"{APP_URL}/{period}/{number}",
        source_data=raw,
    )


def _walk_documents(value: Any, found: list[Document]) -> None:
    if isinstance(value, list):
        for item in value:
            _walk_documents(item, found)
        return
    if not isinstance(value, dict):
        return
    identifier = value.get("archivoId") or value.get("idArchivo") or value.get("documentoId")
    uuid = value.get("uuid")
    link = value.get("enlace") or value.get("url")
    if link or identifier or uuid:
        key = str(uuid or identifier or link)
        url = str(link or (f"{API_URL}/archivo/uuid/{uuid}" if uuid else f"{API_URL}/archivo/{identifier}/pdf"))
        label = str(value.get("descripcion") or value.get("nombre") or value.get("tipo") or "documento")
        if not any(document.official_id == key for document in found):
            found.append(Document(key, label, url, "anexo" if "anexo" in label.casefold() else "documento"))
    for child in value.values():
        if isinstance(child, (dict, list)):
            _walk_documents(child, found)


def attach_detail(proposition: Proposition, detail: dict[str, Any]) -> Proposition:
    """Conserva metadatos de lista y añade documentos sin asumir un esquema inestable."""
    proposition.source_data["detail"] = detail
    _walk_documents(detail, proposition.documents)
    return proposition
