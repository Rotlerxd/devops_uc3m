# Documentación del backend con docstrings

La documentación de backend se mantiene dentro del propio código Python mediante docstrings.

## Alcance

- Solo backend Python (`Backend/app`).
- Sin cambios funcionales de lógica: únicamente documentación embebida.
- Generación automática de referencia con MkDocs.

## Flujo

1. Se escriben/actualizan docstrings en módulos, utilidades y endpoints del backend.
2. `mkdocstrings` extrae estos docstrings.
3. `mkdocs build --strict` valida y construye el sitio.
4. GitHub Actions publica la documentación en Pages en `main`.

## Módulos documentados

- `app.main`
- `app.core.security`
