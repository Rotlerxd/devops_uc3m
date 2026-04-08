# ADR 0013: Documentación del backend con docstrings + MkDocs

- **Estado:** Aceptado
- **Fecha:** 2026-04-08
- **Autores:** Equipo NEWSRADAR
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0011](0011-pipeline-cicd-github-actions.md)

---

## Contexto

Necesitamos mantener la documentación técnica del backend Python alineada con el código real y versionada en el repositorio.

Además, se requiere automatizar la generación/publicación de documentación usando GitHub Actions.

## Decisión

Se adopta:

- **Docstrings** en el backend Python como fuente primaria de documentación técnica.
- **MkDocs** + **mkdocstrings** para construir documentación navegable desde esos docstrings.
- **GitHub Actions** para validar (`mkdocs build --strict`) y desplegar en GitHub Pages en `main`.

## Justificación

- Reduce deriva entre documentación y código.
- Permite mantener trazabilidad por commits y PR.
- Estandariza el proceso de documentación dentro del flujo CI/CD ya existente.

## Consecuencias

### Positivas

- Referencia backend siempre actualizable desde el propio código.
- Validación automática de documentación en CI.
- Publicación continua y accesible del sitio de documentación.

### Riesgos / costes

- Requiere disciplina para mantener docstrings al día.
- Añade tiempo adicional de build en CI.

## Configuración aplicada

- `mkdocs.yml`
- `docs/backend/docstrings.md`
- `docs/backend/api-reference.md`
- `.github/workflows/docs.yml`
- Docstrings en `Backend/app/main.py` y `Backend/app/core/security.py`
