# Arquitectura del sistema — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-24
- **Autores:** Equipo NEWSRADAR (UC3M — Desarrollo y Operación de Sistemas Software)
- **Estado:** En desarrollo (Sprint 2)

---

## 1. Visión general

NEWSRADAR es un sistema de monitorización de noticias que escucha canales RSS
de distintos medios de comunicación y fuentes oficiales, clasifica las noticias
según el estándar IPTC Media Topics y gestiona alertas por palabras clave,
notificando a los usuarios cuando se detectan noticias relevantes.

El sistema sigue una **arquitectura en capas** con separación clara entre
visualización, lógica de negocio, API REST y persistencia, desplegado mediante
contenedores Docker.

---

## 2. Modelo C4

### 2.1 Nivel 1 — Contexto del sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEWSRADAR                                │
│                                                                 │
│  ┌──────────┐    usa    ┌───────────────────────────────────┐  │
│  │ Gestor   │ ────────► │                                   │  │
│  │ (usuario)│           │         Sistema NEWSRADAR         │  │
│  └──────────┘           │                                   │  │
│                         │  Monitoriza RSS · Clasifica IPTC  │  │
│  ┌──────────┐    usa    │  Gestiona alertas · Notifica      │  │
│  │ Lector   │ ────────► │                                   │  │
│  │ (usuario)│           └───────────────────────────────────┘  │
│  └──────────┘                    │              │               │
│                                  │ lee          │ envía         │
│                         ┌────────▼──────┐  ┌───▼───────────┐  │
│                         │  Fuentes RSS  │  │ Servidor SMTP  │  │
│                         │  (medios de   │  │  (Mailtrap /   │  │
│                         │ comunicación) │  │  producción)   │  │
│                         └───────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Actores:**
- **Gestor de NEWSRADAR:** configura alertas (máx. 20), añade fuentes RSS y
  gestiona la plataforma.
- **Lector:** accede al panel de mando y consulta noticias en modo lectura.

**Sistemas externos:**
- **Fuentes RSS:** canales RSS de medios de comunicación y fuentes oficiales
  (mínimo 100 canales, 10 medios distintos).
- **Servidor SMTP:** Mailtrap en desarrollo; servidor real en producción para
  el envío de correos de verificación y notificaciones.

---

### 2.2 Nivel 2 — Contenedores

| Contenedor | Tecnología | Puerto | Responsabilidad |
|---|---|---|---|
| Frontend | React 19 + Vite | 5173 | Interfaz de usuario, panel de mando |
| Backend API | FastAPI + Python | 8000 | Lógica de negocio, API REST, motor de captura RSS |
| Base de datos relacional | PostgreSQL 15 | 5432 | Entidades: usuarios, alertas, fuentes, notificaciones |
| Motor de búsqueda | Elasticsearch 8.12 | 9200 | Indexación y búsqueda de noticias RSS |

---

### 2.3 Nivel 3 — Componentes del Backend

```
Backend API (FastAPI)
│
├── app/
│   ├── data/
│   │   ├── rss_seed.json       ← Semilla de datos estáticos (fuentes, canales y categorías)
│   │
│   ├── core/
│   │   └── security.py         ← Creacion de tokens y verificación por email
│   │
│   ├── main.py                 ← Esqueleto de la API
│         │ scheduler/          ← Motor de captura RSS
│         │ rss_fetcher_engine  ← Lectura de canales RSS (expresión cron)
│         │ radar               ← Búsquedas en Elastic (multi_match) y generación de notificaciones
```

---

## 3. Decisiones arquitectónicas

Las decisiones de arquitectura están documentadas como ADRs en `/docs/adr/`:

| ADR | Decisión | Estado |
|---|---|---|
| [0001](adr/0001-framework-backend-fastapi.md) | Framework backend: FastAPI + Pydantic V2 | Aceptado |
| [0002](adr/0002-autenticacion-jwt.md) | Autenticación: JWT stateless | Aceptado |
| [0003](adr/0003-verificacion-email-smtplib-mailtrap.md) | Email: smtplib + Mailtrap | Aceptado |
| [0005](adr/0005-frontend-react-vite.md) | Frontend: React 19 + Vite | Aceptado |
| [0006](adr/0006-elasticsearch-indexacion-noticias.md) | Motor de búsqueda: Elasticsearch 8.12 | Aceptado |
| [0007](adr/0007-frontend-bootstrap-react-router.md) | UI: Bootstrap 5 + React Router | Aceptado |
| [0008](adr/0008-calidad-codigo-ruff-ty.md) | Calidad: Ruff + Ty | Aceptado |
| [0009](adr/0009-estrategia-testing-pytest-vitest-playwright.md) | Testing: Pytest + Vitest + Playwright | Aceptado |
| [0010](adr/0010-migraciones-bd-alembic-(obsoleto)) | Migraciones: Alembic | Aceptado |
| [0011](adr/0011-pipeline-cicd-github-actions.md) | CI/CD: GitHub Actions | Aceptado |
| [0012](adr/0012-seguridad-scanning-pip-audit-trivy-sonarqube.md) | Seguridad: pip-audit + Trivy + SonarQube | Aceptado |

---

## 4. Modelo de datos

### 4.1 Documentos indexados (Elasticsearch — índice `newsradar_news`)

```json
{
  "titulo": "string",
  "resumen": "string",
  "url": "string",
  "fuente": "string",
  "medio": "string",
  "categoria_iptc": "string",
  "fecha_publicacion": "date",
  "fecha_captura": "date",
  "alerta_id": "integer"
}
```

---

## 5. Flujos principales

### 5.1 Captura y notificación (Sprint 3)

```
Scheduler (cron)
    │
    ▼
Leer canal RSS ──► Parsear ítems ──► ¿Contiene palabra clave?
                                              │
                              NO ─────────────┘
                              SÍ
                               │
                               ▼
                    Clasificar categoría IPTC
                               │
                               ▼
                    Indexar en Elasticsearch
                               │
                               ▼
                    Generar Notificación
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             Buzón interno          Email al usuario
                                        (SMTP)
```

### 5.2 Registro de usuario

```
POST /api/v1/auth/register
    │
    ▼
Validar datos (Pydantic) ──► ¿Email ya existe? ──► 400 Bad Request
    │
   NO
    ▼
Crear usuario (is_verified=False, rol=LECTOR)
    │
    ▼
BackgroundTask: token (type=email_verification, exp=24h)
    │
    ▼
Enviar email (smtplib → Mailtrap)
    │
    ▼
201 Created
```

---

## 6. Infraestructura y despliegue

### 6.1 Levantar el entorno de desarrollo

```bash
# Bases de datos (PostgreSQL + Elasticsearch)
cd Backend && docker-compose up -d

# Backend API
cd Backend && python -m uvicorn app.main:app --reload

# Frontend
cd Frontend && npm install && npm run dev
```

### 6.2 Variables de entorno requeridas (`Backend/.env`)

```
DATABASE_URL=postgresql+asyncpg://newsradar_admin:<pass>@localhost:5432/newsradar_db
ELASTICSEARCH_URL=http://localhost:9200
SECRET_KEY=<clave_aleatoria_segura>
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=<usuario_mailtrap>
MAIL_PASSWORD=<contraseña_mailtrap>
MAIL_FROM=noreply@newsradar.local
```

> El fichero `.env` está en `.gitignore` y nunca se sube al repositorio.

---

## 7. Atributos de calidad

| Atributo | Mecanismo |
|---|---|
| Mantenibilidad | Arquitectura en capas; responsabilidades separadas por módulo |
| Testabilidad | Inyección de dependencias FastAPI; mocks con pytest |
| Seguridad | JWT, bcrypt, verificación de email, roles GESTOR/LECTOR |
| Escalabilidad | Modelo asíncrono (asyncpg + AsyncSession) |
| Observabilidad | SonarQube (Sprint 5); health check en `/health` |
| Desplegabilidad | Docker Compose; pipeline CI/CD GitHub Actions (Sprint 4) |

---

## 8. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-03-24 | Versión inicial tras Sprints 0 y 1 |
