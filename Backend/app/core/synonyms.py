"""Generación local de sinónimos usando WordNet multilingüe de NLTK."""

from __future__ import annotations

import re
import threading
import unicodedata

from nltk.corpus import wordnet

DEFAULT_LANGUAGE = "spa"
MIN_SYNONYM_LIMIT = 3
MAX_SYNONYM_LIMIT = 10
DEFAULT_SYNONYM_LIMIT = MAX_SYNONYM_LIMIT
FALLBACK_SYNONYMS: dict[str, list[str]] = {
    "ia": ["inteligencia artificial", "aprendizaje automático", "ai"],
    "inteligencia artificial": ["ia", "aprendizaje automático", "ai"],
}
WARMUP_PROBE_TERM = "casa"
WARMUP_STATUS_COLD = "cold"
WARMUP_STATUS_WARMING = "warming"
WARMUP_STATUS_WARMED = "warmed"
WARMUP_STATUS_FAILED = "failed"

_warmup_lock = threading.Lock()
_warmup_status = WARMUP_STATUS_COLD
_warmup_error: str | None = None


class SynonymDataNotAvailableError(RuntimeError):
    """Indica que los corpus locales de NLTK no están instalados."""


def warmup_synonym_resources(language: str = DEFAULT_LANGUAGE) -> tuple[str, str | None]:
    """Precarga recursos de sinónimos para evitar latencia en la primera consulta."""
    global _warmup_error
    global _warmup_status

    with _warmup_lock:
        if _warmup_status == WARMUP_STATUS_WARMED:
            return "already_warmed", None
        if _warmup_status == WARMUP_STATUS_FAILED:
            return "failed", _warmup_error
        if _warmup_status == WARMUP_STATUS_WARMING:
            return "warming", None
        _warmup_status = WARMUP_STATUS_WARMING

    try:
        _synsets_for(WARMUP_PROBE_TERM, language)
    except SynonymDataNotAvailableError as exc:
        with _warmup_lock:
            _warmup_status = WARMUP_STATUS_FAILED
            _warmup_error = str(exc)
        print(f"[SYNONYMS] Warmup fallido: {exc}")
        return "failed", _warmup_error

    with _warmup_lock:
        _warmup_status = WARMUP_STATUS_WARMED
        _warmup_error = None

    return "warmed", None


def _reset_warmup_state_for_tests() -> None:
    """Reinicia el estado de warmup para pruebas unitarias."""
    global _warmup_error
    global _warmup_status
    with _warmup_lock:
        _warmup_status = WARMUP_STATUS_COLD
        _warmup_error = None


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

    _append_wordnet_synonyms(
        lookup_terms=lookup_terms,
        language=language,
        excluded_terms=excluded_terms,
        seen=seen,
        synonyms=synonyms,
        max_results=max_results,
    )

    # Para frases compuestas sin entrada directa en WordNet, intentamos con cada token.
    if len(synonyms) < max_results and " " in normalized_term:
        phrase_tokens = [token for token in normalized_term.split(" ") if token]
        _append_wordnet_synonyms(
            lookup_terms=phrase_tokens,
            language=language,
            excluded_terms=excluded_terms,
            seen=seen,
            synonyms=synonyms,
            max_results=max_results,
        )

    if len(synonyms) < max_results:
        _append_fallback_synonyms(
            term=normalized_term,
            excluded_terms=excluded_terms,
            seen=seen,
            synonyms=synonyms,
            max_results=max_results,
        )

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


def _append_wordnet_synonyms(
    lookup_terms: list[str],
    language: str,
    excluded_terms: set[str],
    seen: set[str],
    synonyms: list[str],
    max_results: int,
) -> None:
    for lookup_term in lookup_terms:
        for synset in _synsets_for(lookup_term, language):
            for lemma in synset.lemma_names(lang=language):
                _append_synonym_candidate(
                    candidate=lemma,
                    excluded_terms=excluded_terms,
                    seen=seen,
                    synonyms=synonyms,
                    max_results=max_results,
                )
                if len(synonyms) >= max_results:
                    return


def _append_fallback_synonyms(
    term: str,
    excluded_terms: set[str],
    seen: set[str],
    synonyms: list[str],
    max_results: int,
) -> None:
    for candidate in FALLBACK_SYNONYMS.get(term, []):
        _append_synonym_candidate(
            candidate=candidate,
            excluded_terms=excluded_terms,
            seen=seen,
            synonyms=synonyms,
            max_results=max_results,
        )
        if len(synonyms) >= max_results:
            return


def _append_synonym_candidate(
    candidate: str,
    excluded_terms: set[str],
    seen: set[str],
    synonyms: list[str],
    max_results: int,
) -> None:
    synonym = normalize_text(candidate)
    if not synonym or synonym in excluded_terms or synonym in seen:
        return

    synonyms.append(synonym)
    seen.add(synonym)

    if len(synonyms) >= max_results:
        return
