"""Generación local de sinónimos usando WordNet multilingüe de NLTK."""

from __future__ import annotations

import re
import unicodedata

from nltk.corpus import wordnet

DEFAULT_LANGUAGE = "spa"
MIN_SYNONYM_LIMIT = 3
MAX_SYNONYM_LIMIT = 10
DEFAULT_SYNONYM_LIMIT = MAX_SYNONYM_LIMIT


class SynonymDataNotAvailableError(RuntimeError):
    """Indica que los corpus locales de NLTK no están instalados."""


def normalize_text(value: str) -> str:
    """Normaliza espacios, guiones bajos y capitalización sin eliminar acentos."""
    normalized = unicodedata.normalize("NFKC", value.replace("_", " "))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.casefold()


def normalize_limit(limit: int) -> int:
    """Ajusta el límite al rango soportado por la aplicación."""
    return max(MIN_SYNONYM_LIMIT, min(limit, MAX_SYNONYM_LIMIT))


def generate_synonyms(term: str, limit: int = DEFAULT_SYNONYM_LIMIT, language: str = DEFAULT_LANGUAGE) -> list[str]:
    """Devuelve sinónimos limpios y deduplicados para un término."""
    normalized_term = normalize_text(term)
    if not normalized_term:
        return []

    max_results = normalize_limit(limit)
    lookup_terms = _lookup_terms(normalized_term)
    excluded_terms = {normalize_text(lookup_term) for lookup_term in lookup_terms}
    synonyms: list[str] = []
    seen: set[str] = set()

    for lookup_term in lookup_terms:
        for synset in _synsets_for(lookup_term, language):
            for lemma in synset.lemma_names(lang=language):
                synonym = normalize_text(lemma)
                if not synonym or synonym in excluded_terms or synonym in seen:
                    continue

                synonyms.append(synonym)
                seen.add(synonym)

                if len(synonyms) >= max_results:
                    return synonyms

    return synonyms


def _synsets_for(term: str, language: str):
    try:
        return wordnet.synsets(term.replace(" ", "_"), lang=language)
    except LookupError as exc:
        raise SynonymDataNotAvailableError(
            "Los corpus de NLTK 'wordnet' y 'omw-1.4' deben estar instalados para generar sinónimos."
        ) from exc


def _lookup_terms(term: str) -> list[str]:
    candidates = [term]

    if len(term) > 4 and term.endswith("ces"):
        candidates.append(f"{term[:-3]}z")
    if len(term) > 4 and term.endswith("es"):
        candidates.append(term[:-2])
    if len(term) > 3 and term.endswith("s"):
        candidates.append(term[:-1])

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)

    return deduped
