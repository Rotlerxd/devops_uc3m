# ADR 0008: Herramientas de calidad de código (Ruff + Ty)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (NEWSRADAR)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

El proyecto NEWSRADAR necesita herramientas automatizadas de calidad de código
para garantizar consistencia, detectar errores antes de que lleguen a producción
y facilitar la revisión de código en el equipo.

Las opciones evaluadas para linting, formateo y análisis de tipos fueron:

- **Linting:** Flake8, Pylint, Ruff
- **Formateo:** Black, autopep8, Ruff formatter
- **Tipos estáticos:** MyPy, Pyright, Ty

El enunciado del proyecto requiere que el código supere métricas de calidad
(RNF-03) y que las pruebas y verificaciones se automaticen (RNF-02).

## Decisión

Se decide utilizar:

- **Ruff** para linting y formateo (reemplaza a Flake8 + Black + isort).
- **Ty** para verificación de tipos estáticos (reemplaza a MyPy).

Ambas herramientas están desarrolladas por Astral, comparten filosofía de
diseño y ofrecen rendimiento significativamente superior a las alternativas
tradicionales.

## Justificación

- **Ruff** es 10-100x más rápido que Flake8 y ejecuta linting + formateo +
  orden de imports en una sola herramienta. Configura reglas equivalentes a
  Flake8 (E, F, W), flake8-bugbear (B), flake8-simplify (SIM) e isort (I).
- Elimina la necesidad de instalar y configurar Black, Flake8 e isort por
  separado, reduciendo la superficie de dependencias del proyecto.
- **Ty** es el verificador de tipos de nueva generación de Astral, diseñado
  para ser rápido y compatible con anotaciones de tipo modernas de Python 3.11+.
- MyPy, aunque más maduro, es más lento y tiene una configuración más compleja
  para proyectos con Pydantic V2 y SQLAlchemy 2.0.
- La configuración se centraliza en `pyproject.toml`, manteniendo el repositorio
  limpio y la sincronización con pytest y coverage.

## Consecuencias

### Positivas

- Un solo archivo de configuración (`pyproject.toml`) para Ruff, pytest y coverage.
- Formateo y linting automáticos y consistentes en local y en CI.
- Hooks de pre-commit que ejecutan Ruff antes de cada commit.
- Rendimiento: verificaciones de calidad en segundos, no minutos.

### Negativas / riesgos

- Ty es más joven que MyPy; puede tener menos cobertura de edge cases en
  tipos complejos de SQLAlchemy o Pydantic.
- El equipo debe aprender las reglas específicas de Ruff (aunque son
  equivalentes a las de Flake8 en su mayoría).
- Ruff no incluye todas las reglas de Pylint; si se necesitan reglas más
  avanzadas en el futuro, podría requerirse una herramienta adicional.

## Configuración aplicada

Ver `pyproject.toml` sección `[tool.ruff]` y `[tool.ty]`.

Reglas habilitadas: E, F, I, UP, B, SIM, W, RUF.
Reglas ignoradas: E501 (manejado por el formateador), B008 (patrón FastAPI Depends), SIM108.
