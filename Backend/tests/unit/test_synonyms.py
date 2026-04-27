"""Unit tests for Spanish synonym generation."""

import pytest

from app.core import synonyms


@pytest.fixture(autouse=True)
def reset_synonym_optional_state(monkeypatch):
    monkeypatch.delenv(synonyms.FASTTEXT_MODEL_PATH_ENV, raising=False)
    synonyms._reset_warmup_state_for_tests()
    yield
    synonyms._reset_warmup_state_for_tests()


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


class FakeFastTextModel:
    def __init__(self, mapping: dict[str, list[tuple[float, str]]]) -> None:
        self.mapping = mapping
        self.calls: list[tuple[str, int]] = []

    def get_nearest_neighbors(self, term: str, k: int):
        self.calls.append((term, k))
        return self.mapping.get(term, [])[:k]


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


@pytest.mark.unit
def test_fasttext_fallback_is_used_when_wordnet_returns_too_few_results(monkeypatch):
    fake_wordnet = MapWordNet({"tecnologia": [FakeSynset(["técnica"])]})
    fake_fasttext = FakeFastTextModel(
        {
            "tecnologia": [
                (0.92, "ingenieria"),
                (0.87, "tecnologia"),
                (0.84, "http://basura"),
                (0.81, "innovacion"),
            ]
        }
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(synonyms, "_get_fasttext_model", lambda: fake_fasttext)

    result = synonyms.generate_synonyms("tecnologia", limit=4)

    assert result == ["técnica", "ingenieria", "innovacion"]


@pytest.mark.unit
def test_fasttext_is_optional_when_model_is_not_configured(monkeypatch):
    fake_wordnet = MapWordNet({"casa": [FakeSynset(["hogar"])]})
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)

    result = synonyms.generate_synonyms("casa", limit=10)

    assert result == ["hogar"]


@pytest.mark.unit
def test_missing_fasttext_model_path_is_handled_gracefully(monkeypatch, tmp_path):
    fake_wordnet = MapWordNet({})
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setenv(synonyms.FASTTEXT_MODEL_PATH_ENV, str(tmp_path / "missing.bin"))

    result = synonyms.generate_synonyms("gpu", limit=10)

    assert result == []


@pytest.mark.unit
def test_fasttext_deduplicates_excludes_original_and_filters_junk(monkeypatch):
    fake_wordnet = MapWordNet({})
    fake_fasttext = FakeFastTextModel(
        {
            "gpu": [
                (0.95, "GPU"),
                (0.91, "tarjeta"),
                (0.88, "tarjeta"),
                (0.84, "3"),
                (0.82, "x"),
                (0.8, "www.ejemplo.com"),
                (0.78, "procesador"),
            ]
        }
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(synonyms, "_get_fasttext_model", lambda: fake_fasttext)

    result = synonyms.generate_synonyms("GPU", limit=10)

    assert result == ["tarjeta", "procesador"]


@pytest.mark.unit
def test_fasttext_limit_and_acronym_lookup_are_case_insensitive(monkeypatch):
    fake_wordnet = MapWordNet({})
    fake_fasttext = FakeFastTextModel(
        {
            "gpu": [
                (0.96, "grafica"),
                (0.94, "nvidia"),
                (0.92, "hardware"),
                (0.9, "cuda"),
            ]
        }
    )
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(synonyms, "_get_fasttext_model", lambda: fake_fasttext)

    assert synonyms.generate_synonyms("GPU", limit=2) == ["grafica", "nvidia", "hardware"]
    assert synonyms.generate_synonyms("gpu", limit=2) == ["grafica", "nvidia", "hardware"]


@pytest.mark.unit
def test_wordnet_and_fallback_order_before_fasttext(monkeypatch):
    fake_wordnet = MapWordNet({"ia": [FakeSynset(["inteligencia"])]})
    fake_fasttext = FakeFastTextModel({"ia": [(0.99, "aprendizaje"), (0.98, "datos")]})
    monkeypatch.setattr(synonyms, "wordnet", fake_wordnet)
    monkeypatch.setattr(synonyms, "FALLBACK_SYNONYMS", {"ia": ["inteligencia artificial"]})
    monkeypatch.setattr(synonyms, "_get_fasttext_model", lambda: fake_fasttext)

    result = synonyms.generate_synonyms("IA", limit=10)

    assert result == ["inteligencia", "inteligencia artificial", "aprendizaje", "datos"]


@pytest.mark.unit
def test_warmup_preloads_fasttext_when_configured(monkeypatch):
    call_counter = {"wordnet": 0, "fasttext": 0}
    fake_fasttext = FakeFastTextModel({synonyms.FASTTEXT_WARMUP_PROBE_TERM: [(0.9, "tecnica")]})

    def fake_synsets_for(term: str, language: str):
        call_counter["wordnet"] += 1
        assert term == synonyms.WARMUP_PROBE_TERM
        assert language == "spa"
        return []

    def fake_get_fasttext_model():
        call_counter["fasttext"] += 1
        return fake_fasttext

    monkeypatch.setattr(synonyms, "_synsets_for", fake_synsets_for)
    monkeypatch.setattr(synonyms, "_get_fasttext_model", fake_get_fasttext_model)

    first_status, _ = synonyms.warmup_synonym_resources()
    second_status, _ = synonyms.warmup_synonym_resources()

    assert first_status == "warmed"
    assert second_status == "already_warmed"
    assert call_counter == {"wordnet": 1, "fasttext": 1}
