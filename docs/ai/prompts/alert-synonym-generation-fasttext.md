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

Improve the existing Spanish synonym-generation feature by adding an optional fastText-based fallback/ranking layer alongside the current NLTK WordNet + omw-1.4 implementation.

Context:

* The project has a Python backend, PostgreSQL database, and Python frontend.
* The current synonym feature uses NLTK WordNet + omw-1.4 for Spanish synonyms.
* WordNet/OMW works for some general vocabulary but misses many RSS/news/technical terms.
* Examples of weak or missing terms include “tecnología”, “ingeniería”, and “gpu”.
* The app processes arbitrary RSS feeds, so we cannot rely only on a curated domain synonym table.
* We want a free, local-first, lightweight solution.
* Do not use hosted APIs, paid services, Ollama, or an LLM.

Goal:

* Keep WordNet/OMW as the high-precision source.
* Add fastText Spanish vectors as a lower-precision but higher-coverage fallback for related terms.
* Merge results deterministically.
* Make it clear in code/docs/tests that fastText results are semantically related terms, not guaranteed strict synonyms.

Required behavior:

1. Preserve the existing WordNet/OMW lookup.
2. Add a fastText Spanish vector lookup layer.
3. Use WordNet/OMW results first.
4. Use fastText when:

   * WordNet returns too few results,
   * the term is missing from WordNet,
   * or the configured result limit has not been reached.
5. Merge WordNet and fastText results.
6. Deduplicate results.
7. Exclude the original term case-insensitively.
8. Preserve the configurable 3-10 result limit.
9. Return deterministic ordering:

   * WordNet/OMW results first,
   * then fastText candidates ranked by vector similarity.
10. Avoid returning obvious junk tokens, punctuation, URLs, numbers-only strings, or very short meaningless fragments.
11. Normalize common acronyms case-insensitively, for example “gpu” and “GPU”.
12. Keep the feature local and free.

Dependency/model expectations:

* Investigate the most appropriate Python package for loading fastText vectors in this project.
* Prefer a practical implementation that can load pretrained Spanish fastText vectors locally.
* Do not download large vector files at runtime during normal app use unless the project already has an accepted asset-download mechanism.
* Make the vector path configurable through the project’s existing configuration system.
* Handle the case where fastText vectors are not installed/configured:

  * WordNet/OMW should still work.
  * The app should not crash.
  * Log or report the missing optional fallback using existing conventions.
* Consider memory/startup implications and lazy loading.
* Reuse or extend the existing synonym warmup mechanism if one exists.

Important citation/reference requirement:

* If fastText pretrained vectors are used, documentation and/or the ADR must explicitly reference:
  https://fasttext.cc/docs/en/pretrained-vectors#references
* Mention that fastText vectors require citation according to the official fastText pretrained vectors reference section.
* Include the appropriate reference in the ADR/docs in the style used by this repository.

Implementation expectations:

* First inspect the repository structure and the existing synonym implementation.
* Follow existing service/repository/controller/API/frontend patterns.
* Keep the change native to the codebase.
* Avoid adding heavy dependencies unless clearly justified.
* Do not add an LLM.
* Do not add a separate model server.
* If the frontend currently displays these as “synonyms”, consider whether UI wording should distinguish strict synonyms from related suggestions. Follow existing product wording and keep the change minimal.

Filtering/ranking guidance:

* fastText candidates should be filtered before returning.
* Prefer same-language-looking terms.
* Remove candidates containing invalid characters, URLs, punctuation-only values, numbers-only values, or candidates equal to the original term.
* Consider filtering out multiword candidates only if the existing UI cannot handle them.
* Keep the ranking simple and explainable.

Tests:

* Add or update automated tests in the existing test structure.
* Cover:

  * WordNet results still work,
  * fastText fallback is used when WordNet returns too few results,
  * fastText is not required for the app to function,
  * missing/unconfigured vector file is handled gracefully,
  * results are deduplicated,
  * original term is excluded,
  * limit handling still works,
  * acronym lookup such as “gpu”/“GPU” behaves case-insensitively,
  * deterministic ordering of WordNet results before fastText results.
* Use mocks/fakes for fastText in unit tests where appropriate so CI does not need to download or load a huge vector file.

CI:

* Ensure tests are included in the existing CI pipeline.
* Do not make CI download huge fastText vectors unless the project already supports cached test assets.
* Prefer mocked fastText vectors in CI.

ADR/docs:

* Update the existing synonym ADR if one exists, or create a new ADR under `./docs/adr/` if that matches the project’s ADR style.
* Match the existing ADR naming, style, tone, and structure.
* Explain:

  * why WordNet/OMW alone is insufficient for random RSS/news/technical vocabulary,
  * why fastText was added as a fallback,
  * why fastText results are related terms rather than guaranteed synonyms,
  * why this remains local/free,
  * dependency, storage, memory, startup, and warmup implications,
  * how missing vector files are handled,
  * testing strategy,
  * alternatives considered: curated PostgreSQL table, ConceptNet, hosted Gemini/API, local LLM.
* Explicitly include/reference:
  https://fasttext.cc/docs/en/pretrained-vectors#references

Validation:

* Run relevant tests.
* Run linting/formatting/type checks if used by the project.
* Commit the changes in sensible commits.
* Do not push anything to GitHub.
* Do not create a PR.

At the end, report:

* implementation approach chosen,
* files changed,
* dependencies/config added,
* ADR/docs updated,
* tests added/updated,
* commands run,
* whether fastText is optional or required,
* any assumptions, limitations, or follow-up concerns.
