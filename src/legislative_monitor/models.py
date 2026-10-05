from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class Document:
    official_id: str
    label: str
    original_url: str
    kind: str = "documento"
    local_path: str | None = None
    sha256: str | None = None
    drive_file_id: str | None = None
    extracted_text: str | None = None
    status: str = "PENDIENTE"


@dataclass(slots=True)
class Classification:
    relevant: bool
    categories: list[str] = field(default_factory=list)
    relevance: str = "BAJA"
    rationale: str = "Sin coincidencias temáticas configuradas."


@dataclass(slots=True)
class Analysis:
    obligations: str
    impact: str
    status: str


@dataclass(slots=True)
class Proposition:
    official_id: str
    number: int
    parliamentary_period: int
    chamber_code: str
    presented_on: date | None
    title: str
    procedural_status: str
    proponent: str
    authors: str
    official_url: str
    documents: list[Document] = field(default_factory=list)
    classification: Classification | None = None
    analysis: Analysis | None = None
    source_data: dict[str, Any] = field(default_factory=dict)

    def sheet_row(self, drive_folder_url: str = "", download_link: str = "") -> dict[str, str]:
        classification = self.classification or Classification(False)
        analysis = self.analysis or Analysis("Pendiente de análisis.", "Pendiente de análisis.", "PENDIENTE")
        return {
            "PROPOSICIÓN LEGISLATIVA": self.official_id,
            "FECHA DE PRESENTACIÓN": self.presented_on.isoformat() if self.presented_on else "",
            "TÍTULO": self.title,
            "ESTADO PROCESAL": self.procedural_status,
            "PROPONENTE": self.proponent,
            "AUTORES": self.authors,
            "LINK DE DESCARGA": download_link,
            "PRINCIPALES OBLIGACIONES": analysis.obligations,
            "IMPACTO EN EL ECOSISTEMA DIGITAL": analysis.impact,
            "FECHA DE DETECCIÓN": "",
            "CATEGORÍA TEMÁTICA": "; ".join(classification.categories),
            "NIVEL DE RELEVANCIA": classification.relevance,
            "FUNDAMENTO DE RELEVANCIA": classification.rationale,
            "URL DEL EXPEDIENTE": self.official_url,
            "LINK CARPETA DRIVE": drive_folder_url,
            "ÚLTIMA ACTUALIZACIÓN": "",
            "ID DEL EXPEDIENTE": self.official_id,
            "URL DOCUMENTO ORIGINAL": self.documents[0].original_url if self.documents else "",
            "ESTADO DE PROCESAMIENTO": analysis.status,
        }

    def as_json(self) -> dict[str, Any]:
        return asdict(self)
