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

    def classify(self, proposition: Proposition) -> Classification:
        searchable = fold(" ".join([proposition.title, proposition.proponent, proposition.authors]))
        scores: dict[str, list[str]] = defaultdict(list)
        for topic in self.topics:
            for keyword in topic["keywords"]:
                term = fold(keyword)
                if term in searchable:
                    scores[topic["name"]].append(keyword)
        if not scores:
            return Classification(False)
        categories = sorted(scores)
        terms = sorted({term for matches in scores.values() for term in matches})
        negative = [term for term in self.negative_context if term in searchable]
        score = len(terms) + len(categories)
        relevance = "ALTA" if score >= 4 else "MEDIA" if score >= 2 else "BAJA"
        rationale = f"Coincidencias configuradas: {', '.join(terms)}."
        if negative and score == 2:
            return Classification(False, categories, "BAJA", rationale + f" Contexto no material: {', '.join(negative)}.")
        return Classification(True, categories, relevance, rationale)
