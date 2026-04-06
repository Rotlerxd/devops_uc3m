# ADR 0011: Pipeline de CI/CD (GitHub Actions)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0008](0008-calidad-codigo-ruff-ty.md), [ADR 0009](0009-estrategia-testing-pytest-vitest-playwright.md)

---

## Contexto

El enunciado del proyecto requiere:

- **RNF-02:** Las pruebas unitarias y funcionales deben automatizarse mediante
  un pipeline de CI en GitHub Actions.
- **RNF-03:** El código debe superar las métricas de calidad de SonarQube.
- **RNF-01:** El sistema debe desplegarse con un único comando o pipeline.

El repositorio está alojado en GitHub, lo que hace natural el uso de GitHub
Actions como plataforma de CI/CD.

## Decisión

Se implementa un pipeline de CI/CD con **GitHub Actions** compuesto por:

- **ci.yml:** verificación completa en cada push y pull request.
- **cd.yml:** construcción y publicación de imágenes Docker en el registro
  de contenedores de GitHub (GHCR).

## Justificación

- GitHub Actions está integrado nativamente con GitHub: no requiere
  infraestructura adicional ni herramientas externas.
- Soporte nativo para **service containers**: PostgreSQL y Elasticsearch
  se levantan automáticamente como servicios en el runner, sin necesidad
  de docker-compose en CI.
- Ecosistema extenso de acciones pre-construidas (setup-python, setup-node,
  docker/build-push-action, SonarQube, Trivy).
- Caché integrado para dependencias Python (pip) y Node (npm).
- Gratuito para repositorios públicos y con cuotas generosas para privados.

## Pipeline diseñado

### ci.yml (10 jobs)

1. **backend-lint** — Ruff lint + format check
2. **backend-typecheck** — Ty type check
3. **backend-unit** — pytest unit tests con coverage
4. **backend-integration** — pytest integration con PostgreSQL + Elasticsearch
5. **frontend-test** — Vitest + build check
6. **e2e** — Playwright con stack completo
7. **security** — pip-audit + npm audit
8. **docker-build** — validación de build de imagen
9. **sonarqube** — análisis de calidad SonarQube
10. **trivy-scan** — escaneo de vulnerabilidades de contenedor

### cd.yml (2 jobs)

1. **build-and-push** — build y push a GHCR
2. **deploy** — placeholder para despliegue

## Consecuencias

### Positivas

- Feedback rápido en PRs: lint, typecheck y tests unitarios en minutos.
- Validación completa antes de merge: integración, E2E, seguridad.
- Imágenes Docker publicadas automáticamente en cada push a main.
- Service containers eliminan la complejidad de docker-compose en CI.
- Caché de dependencias reduce tiempos de ejecución.

### Negativas / riesgos

- GitHub Actions tiene límites de minutos de ejecución (relevantes para
  repositorios privados con muchos builds).
- Los service containers no soportan todos los patrones de docker-compose
  (no hay redes personalizadas, volúmenes persistentes, etc.).
- El pipeline E2E es el más lento (~5-10 min) por necesitar levantar
  backend + frontend + PostgreSQL.
- Secrets de SonarQube deben configurarse manualmente en el repositorio.

## Secrets requeridos

| Secret | Propósito |
|---|---|
| `SONAR_TOKEN` | Autenticación con SonarQube/SonarCloud |
| `SONAR_HOST_URL` | URL del servidor SonarQube |

`GITHUB_TOKEN` se proporciona automáticamente.

## Configuración aplicada

- `.github/workflows/ci.yml` — pipeline completo de CI
- `.github/workflows/cd.yml` — pipeline de despliegue (stub)
