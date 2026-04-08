# Documentación técnica de NEWSRADAR

Bienvenido a la documentación versionada de NEWSRADAR.

En este sitio encontrarás:

- Requisitos y arquitectura del sistema.
- Decisiones de arquitectura (ADR).
- Documentación del backend Python generada desde docstrings.
- Guías de desarrollo, testing y CI/CD.

## Backend Python documentado con docstrings

La referencia del backend se genera automáticamente con **MkDocs + mkdocstrings** a partir de:

- `Backend/app/main.py`
- `Backend/app/core/security.py`

Consulta:

- [Documentación de docstrings](backend/docstrings.md)
- [Referencia API Python](backend/api-reference.md)
