# ADR 0012: Seguridad y escaneo de dependencias (pip-audit + Trivy + SonarQube)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (NEWSRADAR)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0011](0011-pipeline-cicd-github-actions.md)

---

## Contexto

El proyecto NEWSRADAR maneja datos sensibles (contraseñas hasheadas, tokens JWT,
emails de usuarios). La seguridad de la cadena de suministro de dependencias
es un aspecto crítico que debe verificarse automáticamente.

El enunciado requiere métricas de calidad de SonarQube (RNF-03), lo que
incluye análisis de seguridad del código. Además, las mejores prácticas de
DevOps recomiendan:

- Escanear dependencias Python y Node en busca de vulnerabilidades conocidas.
- Escanear imágenes Docker antes de publicarlas.
- Analizar la calidad y seguridad del código continuamente.

## Decisión

Se implementa una estrategia de seguridad en tres capas:

| Capa | Herramienta | Alcance |
|---|---|---|
| Dependencias Python | **pip-audit** | Vulnerabilidades en `requirements.txt` |
| Dependencias Node | **npm audit** | Vulnerabilidades en `package.json` |
| Imágenes Docker | **Trivy** | Vulnerabilidades en la imagen del backend |
| Código fuente | **SonarQube** | Code smells, seguridad, cobertura |

## Justificación

### pip-audit

- Herramienta oficial del Python Packaging Authority (PyPA).
- Consulta la base de datos de vulnerabilidades de OSV (Open Source Vulnerabilities).
- Simple de integrar: `pip-audit -r requirements.txt`.
- Alternativas: Safety (requiere API key para la base de datos completa),
  Snyk (más complejo, modelo freemium).

### npm audit

- Integrado en npm: no requiere instalación adicional.
- Consulta la base de datos de vulnerabilidades de npm/Advisories.
- Ejecutado con `npm audit --production` para excluir devDependencies.

### Trivy

- Escáner de contenedores de código abierto de Aqua Security.
- Detecta vulnerabilidades en SO, dependencias del lenguaje y configuraciones.
- Soporta salida en múltiples formatos (table, JSON, SARIF).
- Integración directa con GitHub Actions mediante `aquasecurity/trivy-action`.
- Alternativas: Snyk Container (freemium), Grype (menos integraciones).

### SonarQube/SonarCloud

- Estándar de la industria para análisis estático de código.
- Detecta code smells, bugs, vulnerabilidades y deuda técnica.
- Integra métricas de cobertura de tests.
- Ya mencionado en el enunciado del proyecto (RNF-03).
- Alternativas: CodeClimate (más caro), Codacy (menos configuración).

## Consecuencias

### Positivas

- Detección temprana de vulnerabilidades antes de que lleguen a producción.
- Escaneo automático en cada push/PR, sin intervención manual.
- Trivy escanea no solo dependencias sino también el SO de la imagen Docker.
- SonarQube proporciona un dashboard de calidad tendencial.
- `continue-on-error: true` en escaneos evita bloqueos por vulnerabilidades
  de baja prioridad mientras se establece el proceso.

### Negativas / riesgos

- pip-audit y npm audit pueden generar falsos positivos o reportar
  vulnerabilidades que no aplican al contexto del proyecto.
- Trivy puede reportar cientos de vulnerabilidades en la imagen base
  de Python (debian-slim); requiere triaje regular.
- SonarQube requiere un servidor (self-hosted) o cuenta SonarCloud.
  Se necesita configurar secrets en GitHub.
- El equipo debe dedicar tiempo a revisar y gestionar los hallazgos.

## Configuración aplicada

- Job `security` en `ci.yml` — pip-audit + npm audit
- Job `trivy-scan` en `ci.yml` — escaneo de imagen Docker
- Job `sonarqube` en `ci.yml` — análisis SonarQube
- `sonar-project.properties` — configuración del proyecto SonarQube
