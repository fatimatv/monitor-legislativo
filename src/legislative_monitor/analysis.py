from __future__ import annotations

import re

from .models import Analysis, Proposition


OBLIGATION_MARKERS = re.compile(
    r"(?is)(?:deber[aá]n|debe(?:r[aá])?|se (?:proh[ií]be|establece|crea|autoriza)|obligaci[oó]n|sanci[oó]n|infracci[oó]n|plazo|registro|supervisi[oó]n).{0,450}[.;]"
)


class EvidenceAnalyzer:
    """Análisis conservador: solo expone fragmentos extraídos del PDF oficial."""

    def analyze(self, proposition: Proposition) -> Analysis:
        source_text = "\n".join(document.extracted_text or "" for document in proposition.documents)
        if len(source_text.strip()) < 30:
            return Analysis(
                "No se identifica con suficiente claridad en el documento analizado: no hay texto extraíble oficial disponible.",
                "HECHO NORMATIVO: pendiente de documento oficial legible. INTERPRETACIÓN: no se emite para evitar inferencias sin evidencia.",
                "PENDIENTE_DOCUMENTO",
            )
        excerpts = [" ".join(match.group(0).split()) for match in OBLIGATION_MARKERS.finditer(source_text)]
        excerpts = list(dict.fromkeys(excerpts))[:4]
        obligations = "HECHO NORMATIVO: " + (" ".join(excerpts) if excerpts else "No se identifican obligaciones explícitas con suficiente claridad en el texto extraído.")
        categories = ", ".join((proposition.classification.categories if proposition.classification else []))
        impact = (
            f"HECHO NORMATIVO: el texto fue extraído de documentos oficiales de la iniciativa. "
            f"INTERPRETACIÓN: por su relación con {categories or 'el ecosistema digital'}, podría requerir revisión de cumplimiento por los actores afectados; "
            "la conclusión debe contrastarse con el articulado completo."
        )
        return Analysis(obligations, impact, "ANALIZADO")
