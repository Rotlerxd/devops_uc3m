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
