"""Unit tests for Spanish synonym generation."""

import pytest

from app.core import synonyms


class FakeSynset:
    def __init__(self, lemmas: list[str]) -> None:
        self.lemmas = lemmas

    def lemma_names(self, lang: str) -> list[str]:
        assert lang == "spa"
        return self.lemmas


class FakeWordNet:
    def __init__(self, synsets: list[FakeSynset]) -> None:
        self._synsets = synsets

    def synsets(self, term: str, lang: str) -> list[FakeSynset]:
        assert term == "casa"
        assert lang == "spa"
        return self._synsets


class MapWordNet:
    def __init__(self, mapping: dict[str, list[FakeSynset]]) -> None:
        self.mapping = mapping

    def synsets(self, term: str, lang: str) -> list[FakeSynset]:
        assert lang == "spa"
        return self.mapping.get(term, [])


@pytest.mark.unit
def test_spanish_synonym_lookup_returns_clean_results():
    result = synonyms.generate_synonyms("coche", limit=10)

    assert result
    assert len(result) <= 10
    assert "coche" not in result
    assert len(result) == len(set(result))


@pytest.mark.unit
def test_deduplicates_and_excludes_original_term(monkeypatch):
    fake_wordnet = FakeWordNet(
        [
            FakeSynset(["casa", "hogar", "Hogar", "vivienda"]),
            FakeSynset(["casa", "vivienda", "domicilio"]),
        ]
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)

    result = synonyms.generate_synonyms("Casa", limit=10)

    assert result == ["hogar", "vivienda", "domicilio"]


@pytest.mark.unit
def test_limit_is_clamped_to_supported_range(monkeypatch):
    fake_wordnet = FakeWordNet(
        [
            FakeSynset(
                [
                    "casa",
                    "hogar",
                    "vivienda",
                    "domicilio",
                    "residencia",
                    "morada",
                    "piso",
                    "apartamento",
                    "inmueble",
                    "habitacion",
                    "alojamiento",
                ]
            )
        ]
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)

    assert synonyms.generate_synonyms("casa", limit=2) == ["hogar", "vivienda", "domicilio"]
    assert len(synonyms.generate_synonyms("casa", limit=50)) == 10


@pytest.mark.unit
def test_no_results_returns_empty_list(monkeypatch):
    fake_wordnet = FakeWordNet([])
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)

    assert synonyms.generate_synonyms("casa", limit=10) == []


@pytest.mark.unit
def test_fallback_for_ia_when_wordnet_has_no_results(monkeypatch):
    fake_wordnet = MapWordNet({})
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(
        synonyms,
        "FALLBACK_SYNONYMS",
        {"ia": ["inteligencia artificial", "aprendizaje automático", "ia"]},
    )

    result = synonyms.generate_synonyms("IA", limit=10)

    assert result == ["inteligencia artificial", "aprendizaje automático"]


@pytest.mark.unit
def test_phrase_decomposition_for_multiword_terms(monkeypatch):
    fake_wordnet = MapWordNet(
        {
            "inteligencia_artificial": [],
            "inteligencia": [FakeSynset(["capacidad", "razón"])],
            "artificial": [FakeSynset(["falso"])],
        }
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(synonyms, "FALLBACK_SYNONYMS", {})

    result = synonyms.generate_synonyms("inteligencia artificial", limit=10)

    assert result == ["capacidad", "razón", "falso"]


@pytest.mark.unit
def test_warmup_success_is_idempotent(monkeypatch):
    call_counter = {"count": 0}
    synonyms._reset_warmup_state_for_tests()

    def fake_synsets_for(term: str, language: str):
        call_counter["count"] += 1
        assert term == synonyms.WARMUP_PROBE_TERM
        assert language == "spa"
        return []

    monkeypatch.setattr(synonyms, "_synsets_for", fake_synsets_for)

    first_status, first_detail = synonyms.warmup_synonym_resources()
    second_status, second_detail = synonyms.warmup_synonym_resources()

    assert first_status == "warmed"
    assert first_detail is None
    assert second_status == "already_warmed"
    assert second_detail is None
    assert call_counter["count"] == 1


@pytest.mark.unit
def test_warmup_failure_is_idempotent(monkeypatch):
    call_counter = {"count": 0}
    synonyms._reset_warmup_state_for_tests()

    def fake_synsets_for(term: str, language: str):
        call_counter["count"] += 1
        raise synonyms.SynonymDataNotAvailableError("missing resources")

    monkeypatch.setattr(synonyms, "_synsets_for", fake_synsets_for)

    first_status, first_detail = synonyms.warmup_synonym_resources()
    second_status, second_detail = synonyms.warmup_synonym_resources()

    assert first_status == "failed"
    assert first_detail == "missing resources"
    assert second_status == "failed"
    assert second_detail == "missing resources"
    assert call_counter["count"] == 1


@pytest.mark.unit
def test_generate_synonyms_works_after_warmup(monkeypatch):
    synonyms._reset_warmup_state_for_tests()
    mapping = {
        synonyms.WARMUP_PROBE_TERM: [FakeSynset([])],
        "coche": [FakeSynset(["auto", "vehiculo"])],
    }

    def fake_synsets_for(term: str, language: str):
        assert language == "spa"
        return mapping.get(term, [])

    monkeypatch.setattr(synonyms, "_synsets_for", fake_synsets_for)

    status, detail = synonyms.warmup_synonym_resources()
    result = synonyms.generate_synonyms("coche", limit=10)

    assert status == "warmed"
    assert detail is None
    assert result == ["auto", "vehiculo"]
