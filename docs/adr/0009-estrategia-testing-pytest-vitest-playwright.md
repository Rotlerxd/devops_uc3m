# ADR 0009: Estrategia de testing (Pytest + Vitest + Playwright)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0001](0001-framework-backend-fastapi.md), [ADR 0005](0005-frontend-react-vite.md)

---

## Contexto

El proyecto NEWSRADAR requiere pruebas automatizadas en múltiples niveles
según los requisitos:

- **RNF-02:** Las pruebas unitarias y funcionales deben automatizarse.
- **RNF-01:** El sistema debe desplegarse con un único comando o pipeline.

Se necesita cubrir:
1. Lógica de negocio del backend (esquemas, seguridad, CRUD).
2. Endpoints de la API REST (autenticación, autorización, respuestas).
3. Componentes del frontend React.
4. Flujos completos de usuario a través de la interfaz.

## Decisión

Se adopta una estrategia de **pirámide de tests** con tres herramientas:

| Nivel | Herramienta | Alcance |
|---|---|---|
| Backend unitario | **pytest** + pytest-asyncio | Lógica aislada, esquemas, seguridad |
| Backend integración | **pytest** + httpx AsyncClient | Endpoints API, PostgreSQL, JWT |
| Frontend unitario | **Vitest** + Testing Library | Componentes React, páginas |
| E2E | **Playwright** | Flujos completos de usuario |

Marcadores de pytest: `unit`, `integration`, `e2e`.

## Justificación

### pytest

- Es el estándar de facto para testing en Python.
- Soporte nativo de `async/await` mediante `pytest-asyncio` (modo `auto`),
  compatible con el paradigma asíncrono de FastAPI + SQLAlchemy.
- Integración con `httpx.AsyncClient` para testear endpoints sin servidor real.
- Fixtures potentes para configurar base de datos de test, sesión DB, etc.
- Alternativas: unittest (más verboso), nose2 (menos activo).

### Vitest

- Diseñado para Vite: configuración mínima, usa la misma pipeline de
  transformación que el proyecto.
- Compatible con la API de Jest (migración futura sencilla si es necesario).
- Más rápido que Jest para proyectos Vite.
- Integración con `@testing-library/react` para testing centrado en el usuario.
- Alternativas: Jest (requiere configuración extra con Vite), React Testing Library standalone.

### Playwright

- Multi-navegador (aunque en CI usamos solo Chromium para velocidad).
- Auto-esperas inteligentes: reduce la flakiness en comparación con Cypress o Selenium.
- Genera traces y screenshots automáticos en fallos.
- Integración directa con GitHub Actions.
- Alternativas: Cypress (más limitado en navegadores), Selenium (más lento y frágil).

## Consecuencias

### Positivas

- Cobertura completa: desde lógica aislada hasta flujos de usuario reales.
- Ejecución rápida: tests unitarios en segundos, integración en decenas de segundos.
- Separación clara por marcadores: `make test-unit`, `make test-integration`, `make test-e2e`.
- Las dependencias de test están separadas (`requirements-dev.txt`) del
  código de producción.

### Negativas / riesgos

- Mantener tres frameworks de test requiere conocimiento en cada uno.
- Los tests de integración necesitan PostgreSQL y Elasticsearch disponibles
  (resuelto con service containers en CI y docker-compose en local).
- Playwright necesita Chromium instalado; el CI lo instala con `npx playwright install`.
- Los tests E2E son inherentemente más lentos y frágiles que los unitarios.

## Configuración aplicada

- pytest: ver `pyproject.toml` sección `[tool.pytest.ini_options]`
- Vitest: ver `Frontend/vitest.config.js`
- Playwright: ver `e2e/playwright.config.js`
- Coverage: umbral 60% configurable en `pyproject.toml`
