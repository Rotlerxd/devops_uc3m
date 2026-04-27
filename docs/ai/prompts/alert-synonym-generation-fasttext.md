# Prompt: Experimental fastText Fallback for Alert Synonym Generation

- **Date:** 2026-04-27
- **Tool:** Codex (gpt-5.5)
- **Task:** Add an optional fastText-based related-term fallback for alert descriptor suggestions

---

## Prompt Summary

The session requested an optional fastText layer alongside the existing
WordNet/OMW synonym generation feature for alert descriptors.

The implemented work covered:

1. Keeping WordNet/OMW as the primary high-precision synonym source.
2. Adding an optional local fastText fallback for broader Spanish RSS, news and
   technical vocabulary coverage.
3. Treating fastText candidates as semantically related terms rather than
   guaranteed strict synonyms.
4. Making the fastText model path configurable through
   `NEWSRADAR_FASTTEXT_MODEL_PATH`.
5. Handling missing or unconfigured fastText vectors gracefully.
6. Reusing the synonym warmup flow for optional fastText preload.
7. Adding mocked backend tests so CI does not download or load large vector
   files.
8. Adding a local development download helper and `start-dev.sh` flags for
   explicit experimental use.
9. Documenting fastText as experimental and not enabled for normal production
   deployments by default.

## Key Constraints from Prompt

- Keep the feature local-first and free.
- Do not use hosted APIs, paid services, Ollama, or an LLM.
- Preserve deterministic ordering with WordNet/OMW results before fastText
  candidates.
- Do not download large vector files during normal app startup or CI.
- Make fastText optional so WordNet/OMW continues to work without configured
  vectors.
- Cite the official fastText pretrained vectors reference guidance.

## Files Produced

See `docs/ai/usage.md` for the traceability entry covering the optional
fastText fallback, related backend tests, ADR/README updates, and local model
setup scripts derived from this prompted work.

## Full Prompt

