from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from .models import Classification, Proposition


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


class RuleClassifier:
    """Filtro de alta cobertura, explicable y configurable."""

    def __init__(self, taxonomy: dict):
        self.topics = taxonomy["topics"]
        self.negative_context = [fold(item) for item in taxonomy.get("negative_context", [])]

    @staticmethod
    def _official_fields(proposition: Proposition) -> list[tuple[str, str]]:
        fields = [("título", proposition.title), ("proponente", proposition.proponent), ("autores", proposition.authors)]
        labels = {"sumilla": "sumilla oficial", "detalle": "seguimiento oficial", "observacion": "observación oficial", "descripcion": "descripción de adjunto", "nombreArchivo": "nombre de adjunto"}

        def walk(value: object) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in labels and isinstance(child, (str, int, float)):
                        fields.append((labels[key], str(child)))
                    if isinstance(child, (dict, list)):
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(proposition.source_data.get("detail", {}))
        return [(label, value) for label, value in fields if value]

    def classify(self, proposition: Proposition) -> Classification:
        fields = self._official_fields(proposition)
        searchable = fold(" ".join(value for _, value in fields))
        scores: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for source, value in fields:
            normalized = fold(value)
            for topic in self.topics:
                for keyword in topic["keywords"]:
                    term = fold(keyword)
                    if term in normalized:
                        scores[topic["name"]].append((keyword, source))
        if not scores:
            return Classification(False)
        categories = sorted(scores)
        terms = sorted({term for matches in scores.values() for term, _ in matches})
        evidence = sorted({f"{term} ({source})" for matches in scores.values() for term, source in matches})
        negative = [term for term in self.negative_context if term in searchable]
        score = len(terms) + len(categories)
        relevance = "ALTA" if score >= 4 else "MEDIA" if score >= 2 else "BAJA"
        rationale = f"Coincidencias configuradas: {', '.join(evidence)}."
        if negative and score == 2:
            return Classification(False, categories, "BAJA", rationale + f" Contexto no material: {', '.join(negative)}.")
        return Classification(True, categories, relevance, rationale)
