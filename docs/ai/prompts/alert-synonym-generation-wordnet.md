# Prompt: Alert Synonym Generation with Local Lexical Fallback

- **Date:** 2026-04-27
- **Tool:** Codex (gpt-5.5)
- **Task:** Implement local synonym generation for alert descriptors and refine the selection UX

---

## Prompt Summary

The session requested implementation of a local synonym-generation feature for
the alert creation flow, followed by a second refinement pass focused on UX and
lexical coverage.

The implemented work covered:

1. Backend synonym generation using NLTK WordNet and `omw-1.4`.
2. Spanish as the primary supported language.
3. Clean, deduplicated results with configurable limits and exclusion of the
   original term.
4. Frontend integration through the normal alert creation interface.
5. ADR documentation for the decision and its operational implications.
6. Automated backend and frontend tests.
7. UX refinement so synonym generation no longer replaces user-entered
   descriptors.
8. Suggestion generation for every entered descriptor, not only the first.
9. Clickable suggestion chips so the user can choose which synonyms to add.
10. Hard enforcement of the 10-descriptor limit in the UI.
11. A lightweight lexical fallback for terms such as `IA`, without introducing
    a local LLM runtime.

## Key Constraints from Prompt

- Prefer a free, deterministic, lightweight local lexical approach over an LLM.
- Do not use hosted APIs or paid services.
- Do not introduce Ollama or another separate local AI server/process unless
  absolutely necessary.
- Keep the implementation native to the current FastAPI backend and React
  frontend architecture.
- Reuse existing conventions for API design, tests, CI, ADRs, and error
  handling.
- Add fallback behavior for unrecognized descriptors only if it remains
  operationally lightweight.

## Files Produced

See `docs/ai/usage.md` for the traceability entry covering the backend synonym
service, frontend alert UX changes, tests, and ADR update derived from this
prompted work.

## Full Prompt

Implement a new synonym-generation functionality for this project with the following requirements and constraints.

Context:

* The project has a backend server, a PostgreSQL database, and a frontend application.
* The backend and frontend are both written in Python.
* We want a completely free solution with good Spanish support.
* Do not use external hosted APIs or paid services.
* Do not introduce Ollama or other separate local AI servers/processes unless absolutely necessary.
* Prefer a lightweight local lexical approach over an LLM.

Goal:

* Add support for generating 3 to 10 synonyms for a given term, with Spanish as the primary supported language.
* The solution should be deterministic, lightweight, and suitable for production use in our existing architecture.

Implementation requirements:

1. Use a local Python-based approach centered on:

   * NLTK WordNet
   * NLTK omw-1.4
2. Use Spanish through Open Multilingual WordNet via NLTK.
3. If appropriate, normalize or lemmatize the input term before lookup.
4. Return clean, deduplicated synonyms.
5. Exclude the original term from the final result set.
6. Make the result limit configurable, but support the 3-10 range cleanly.
7. Prefer a design where this functionality lives in the backend and is exposed to the frontend through the project’s normal interfaces.
8. Avoid heavy dependencies unless they are clearly justified.
9. If there is already an established service/module/controller pattern in the codebase, follow it exactly.
10. Reuse existing coding conventions, typing style, logging style, configuration patterns, and error-handling patterns.

Design expectations:

* First inspect the repository structure and existing architecture before making changes.
* Find the appropriate place to implement the feature rather than inventing a parallel pattern.
* If there is already a text-processing, dictionary, search, or utilities area, consider integrating there.
* If dependencies must be added, add only the minimum necessary ones.
* Ensure the app behaves reasonably when no synonyms are found.
* Ensure the functionality is easy to extend later.

ADR requirement:

* Create a new ADR in `./docs/adr/`.
* Match the style, structure, naming convention, and tone of the existing ADRs exactly.
* The ADR should explain:

  * the problem,
  * the chosen solution,
  * alternatives considered,
  * why a lightweight lexical solution was chosen over an LLM,
  * operational implications,
  * testing implications,
  * any dependency/storage/runtime considerations.

Testing requirement:

* Add or update automated tests for this functionality.
* Integrate them into the existing CI pipeline conventions already used by the repository.
* Follow the existing testing style and folder structure.
* Cover at least:

  * basic Spanish synonym lookup,
  * deduplication,
  * exclusion of the original term,
  * limit handling,
  * no-results behavior,
  * any API/service integration points introduced by your implementation.

CI requirement:

* Make sure the tests are included in the existing CI pipeline.
* Do not invent a separate ad hoc test command if the repo already has a standard way to run tests.
* If CI configuration updates are needed, make them in the style already used by the repository.

Validation steps:

* Inspect the codebase and determine the correct architectural integration points.
* Implement the feature fully.
* Run the relevant tests locally.
* Run formatting/linting/type checks if those are part of the project workflow.
* Confirm the new functionality is wired through appropriately end to end.

Git requirement:

* Commit the changes in sensible commits as you see fit.
* Do not push anything to the GitHub repository.
* Do not create a PR.
* Do not modify remote settings.

Output expectations:

* After finishing, provide a concise summary of:

  * what was changed,
  * where it was changed,
  * what ADR was added,
  * what tests were added,
  * which commands were run,
  * any follow-up concerns or assumptions.

Important:

* Before coding, inspect the existing ADRs and mirror their style closely.
* Before choosing file locations or patterns, inspect the current repository and follow its conventions.
* Make the implementation feel native to the codebase rather than bolted on.
