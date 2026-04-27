"""Generación local de sinónimos usando WordNet y sugerencias fastText opcionales."""

from __future__ import annotations

import importlib
import os
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any

from nltk.corpus import wordnet

DEFAULT_LANGUAGE = "spa"
MIN_SYNONYM_LIMIT = 3
MAX_SYNONYM_LIMIT = 10
DEFAULT_SYNONYM_LIMIT = MAX_SYNONYM_LIMIT
FASTTEXT_MODEL_PATH_ENV = "NEWSRADAR_FASTTEXT_MODEL_PATH"
FASTTEXT_CANDIDATE_MULTIPLIER = 4
FASTTEXT_MIN_CANDIDATES = 20
FALLBACK_SYNONYMS: dict[str, list[str]] = {
    "ia": ["inteligencia artificial", "aprendizaje automático", "ai"],
    "inteligencia artificial": ["ia", "aprendizaje automático", "ai"],
}
WARMUP_PROBE_TERM = "casa"
FASTTEXT_WARMUP_PROBE_TERM = "tecnologia"
WARMUP_STATUS_COLD = "cold"
WARMUP_STATUS_WARMING = "warming"
WARMUP_STATUS_WARMED = "warmed"
WARMUP_STATUS_FAILED = "failed"
FASTTEXT_STATUS_COLD = "cold"
FASTTEXT_STATUS_LOADING = "loading"
FASTTEXT_STATUS_LOADED = "loaded"
FASTTEXT_STATUS_UNAVAILABLE = "unavailable"

_warmup_lock = threading.Lock()
_warmup_status = WARMUP_STATUS_COLD
_warmup_error: str | None = None
_fasttext_lock = threading.Lock()
_fasttext_model: Any | None = None
_fasttext_status = FASTTEXT_STATUS_COLD
_fasttext_error: str | None = None
_fasttext_notice_logged = False


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
        _warmup_fasttext_resources()
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
    _reset_fasttext_state_for_tests()


def _reset_fasttext_state_for_tests() -> None:
    """Reinicia el estado de fastText para pruebas unitarias."""
    global _fasttext_error
    global _fasttext_model
    global _fasttext_notice_logged
    global _fasttext_status
    with _fasttext_lock:
        _fasttext_model = None
        _fasttext_status = FASTTEXT_STATUS_COLD
        _fasttext_error = None
        _fasttext_notice_logged = False


def normalize_text(value: str) -> str:
    """Normaliza espacios, guiones bajos y capitalización sin eliminar acentos."""
    normalized = unicodedata.normalize("NFKC", value.replace("_", " "))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.casefold()


def normalize_limit(limit: int) -> int:
    """Ajusta el límite al rango soportado por la aplicación."""
    return max(MIN_SYNONYM_LIMIT, min(limit, MAX_SYNONYM_LIMIT))


def generate_synonyms(term: str, limit: int = DEFAULT_SYNONYM_LIMIT, language: str = DEFAULT_LANGUAGE) -> list[str]:
    """Devuelve sinónimos y términos relacionados limpios y deduplicados."""
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

    if len(synonyms) < max_results:
        _append_fasttext_related_terms(
            lookup_terms=lookup_terms,
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


def _append_fasttext_related_terms(
    lookup_terms: list[str],
    excluded_terms: set[str],
    seen: set[str],
    synonyms: list[str],
    max_results: int,
) -> None:
    """Añade términos relacionados por vectores fastText; no son sinónimos estrictos."""
    remaining = max_results - len(synonyms)
    if remaining <= 0:
        return

    model = _get_fasttext_model()
    if model is None:
        return

    candidates_to_fetch = max(FASTTEXT_MIN_CANDIDATES, remaining * FASTTEXT_CANDIDATE_MULTIPLIER)
    for lookup_term in lookup_terms:
        for candidate in _fasttext_candidates_for(model, lookup_term, candidates_to_fetch):
            _append_synonym_candidate(
                candidate=candidate,
                excluded_terms=excluded_terms,
                seen=seen,
                synonyms=synonyms,
                max_results=max_results,
                strict_token=True,
            )
            if len(synonyms) >= max_results:
                return


def _fasttext_candidates_for(model: Any, term: str, limit: int) -> list[str]:
    try:
        neighbors = model.get_nearest_neighbors(term.replace(" ", "_"), k=limit)
    except Exception as exc:
        _log_fasttext_notice(f"fallback fastText no disponible para '{term}': {exc}")
        return []

    return [candidate for _score, candidate in neighbors]


def _warmup_fasttext_resources() -> None:
    model = _get_fasttext_model()
    if model is None:
        return
    _fasttext_candidates_for(model, FASTTEXT_WARMUP_PROBE_TERM, 1)


def _get_fasttext_model() -> Any | None:
    global _fasttext_error
    global _fasttext_model
    global _fasttext_status

    with _fasttext_lock:
        if _fasttext_status == FASTTEXT_STATUS_LOADED:
            return _fasttext_model
        if _fasttext_status == FASTTEXT_STATUS_UNAVAILABLE:
            return None
        if _fasttext_status == FASTTEXT_STATUS_LOADING:
            return None
        _fasttext_status = FASTTEXT_STATUS_LOADING

    model_path = os.getenv(FASTTEXT_MODEL_PATH_ENV, "").strip()
    if not model_path:
        _mark_fasttext_unavailable(f"{FASTTEXT_MODEL_PATH_ENV} no configurado")
        return None

    resolved_model_path = Path(model_path)
    if not resolved_model_path.is_file():
        _mark_fasttext_unavailable(f"modelo no encontrado en {resolved_model_path}")
        return None

    try:
        fasttext = importlib.import_module("fasttext")
        loaded_model = fasttext.load_model(str(resolved_model_path))
    except ImportError as exc:
        _mark_fasttext_unavailable("paquete fasttext no instalado", exc)
        return None
    except Exception as exc:
        _mark_fasttext_unavailable(f"no se pudo cargar {resolved_model_path}", exc)
        return None

    with _fasttext_lock:
        _fasttext_model = loaded_model
        _fasttext_status = FASTTEXT_STATUS_LOADED
        _fasttext_error = None
        return _fasttext_model


def _mark_fasttext_unavailable(reason: str, exc: Exception | None = None) -> None:
    global _fasttext_error
    global _fasttext_status

    detail = f"{reason}: {exc}" if exc else reason
    with _fasttext_lock:
        _fasttext_status = FASTTEXT_STATUS_UNAVAILABLE
        _fasttext_error = detail
    _log_fasttext_notice(f"fallback fastText deshabilitado: {detail}")


def _log_fasttext_notice(message: str) -> None:
    global _fasttext_notice_logged

    with _fasttext_lock:
        if _fasttext_notice_logged:
            return
        _fasttext_notice_logged = True

    print(f"[SYNONYMS] {message}")


def _append_synonym_candidate(
    candidate: str,
    excluded_terms: set[str],
    seen: set[str],
    synonyms: list[str],
    max_results: int,
    strict_token: bool = False,
) -> None:
    synonym = normalize_text(candidate)
    if not synonym or synonym in excluded_terms or synonym in seen:
        return
    if strict_token and not _is_valid_fasttext_candidate(synonym):
        return

    synonyms.append(synonym)
    seen.add(synonym)

    if len(synonyms) >= max_results:
        return


def _is_valid_fasttext_candidate(candidate: str) -> bool:
    if len(candidate) < 3:
        return False
    if candidate.isnumeric():
        return False
    if "://" in candidate or candidate.startswith("www.") or "@" in candidate:
        return False
    if not re.fullmatch(r"[a-záéíóúüñ0-9]+", candidate):
        return False
    return any(char.isalpha() for char in candidate)
