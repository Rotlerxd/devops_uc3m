# Arquitectura del sistema — NEWSRADAR

- **Versión:** 1.1
- **Fecha:** 2026-04-08
- **Autores:** Equipo NEWSRADAR (UC3M — Desarrollo y Operación de Sistemas Software)
- **Estado:** En desarrollo (Sprint 3)

---

## 1. Visión general

NEWSRADAR es un sistema de monitorización de noticias que escucha canales RSS
de distintos medios de comunicación y fuentes oficiales, clasifica las noticias
según el estándar IPTC Media Topics y gestiona alertas por palabras clave,
notificando a los usuarios cuando se detectan noticias relevantes.

El sistema sigue una **arquitectura en capas** con separación clara entre
visualización, lógica de negocio, API REST y persistencia, desplegado mediante
contenedores Docker.

**Decisión clave actual:** las entidades del sistema se almacenan en
**PostgreSQL 15** mediante **SQLAlchemy 2.0**, con migraciones versionadas por
**Alembic**. Elasticsearch sigue dedicándose a la indexación y búsqueda de
noticias RSS. Ver [ADR 0015](adr/0015-postgresql-sqlalchemy-alembic.md).

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
| Backend API | FastAPI + Python | 8000 | Lógica de negocio, API REST, motor RSS |
| PostgreSQL | PostgreSQL 15 | 5432 | Persistencia relacional de usuarios, alertas, fuentes, canales y estadísticas |
| Motor de búsqueda | Elasticsearch 8.12 | 9200 | Indexación y búsqueda de noticias RSS |

```
┌────────────────────────────────────────────────────────┐
│  Docker Compose                                        │
│                                                        │
│  ┌─────────────────┐   HTTP/JSON   ┌───────────────┐  │
│  │    Frontend     │◄─────────────►│    Backend    │  │
│  │  React + Vite   │  puerto 5173  │    FastAPI    │  │
│  └─────────────────┘               │  puerto 8000  │  │
│                                    │               │  │
│                                    └───────┬────────┘  │
│                                            │            │
│                   puerto 5432              │ puerto     │
│               ┌───────────────┐            │ 9200       │
│               │ PostgreSQL 15 │     ┌──────▼───────┐   │
│               │ SQLAlchemy ORM│     │ Elasticsearch│   │
│               │   Alembic     │     │     8.12     │   │
│               └───────────────┘     │  (noticias)  │   │
│                                     └──────────────┘   │
└────────────────────────────────────────────────────────┘

Comunicaciones externas:
  Backend → Canales RSS externos  (HTTP GET, feedparser)
  Backend → Servidor SMTP         (correos verificación y alertas)
```

---

### 2.3 Nivel 3 — Componentes del Backend

```
Backend API (FastAPI — app/main.py)
│
├── Modelos Pydantic (definidos en main.py)
│   ├── User / UserInDB / UserCreate / UserUpdate
│   ├── Alert / AlertCreate / AlertUpdate
│   ├── InformationSource / RSSChannel / Category
│   ├── Notification / Stats / Role
│   └── LoginRequest / TokenResponse
│
├── Persistencia relacional
│   ├── app/db/database.py      → engine, sesiones, Base tipada
│   ├── app/models/models.py    → modelos SQLAlchemy 2.0 tipados
│   └── alembic/                → migraciones de esquema
│
├── Inicialización (lifespan)
│   └── create_seed_data()  ← carga rss_seed.json en PostgreSQL al arrancar
│
├── Endpoints API REST (/api/v1/...)
│   ├── /auth                                        → login, register, verify
│   ├── /users                                       → CRUD usuarios
│   ├── /roles                                       → CRUD roles
│   ├── /categories                                  → CRUD categorías IPTC
│   ├── /users/{id}/alerts                           → CRUD alertas por usuario
│   ├── /users/{id}/alerts/{id}/notifications        → CRUD notificaciones
│   ├── /information-sources                         → CRUD fuentes
│   ├── /information-sources/{id}/rss-channels       → CRUD canales RSS
│   └── /stats                                       → estadísticas globales
│
├── Motor RSS (background thread)
│   └── rss_fetcher_engine()
│       ├── Descarga feeds con feedparser cada 30s
│       ├── Indexa artículos en Elasticsearch (índice: newsradar_articles)
│       └── Cruza con alertas activas → genera Notifications en PostgreSQL
│
└── core/
    └── security.py  ← bcrypt, JWT, create_verification_token,
                        send_verification_email (smtplib)
```

---

## 3. Decisiones arquitectónicas

| ADR | Decisión | Estado |
|---|---|---|
| [0001](adr/0001-framework-backend-fastapi.md) | Framework backend: FastAPI + Pydantic V2 | Aceptado |
| [0002](adr/0002-autenticacion-jwt.md) | Autenticación: JWT stateless | Aceptado |
| [0003](adr/0003-verificacion-email-smtplib-mailtrap.md) | Email: smtplib + Mailtrap | Aceptado |
| [0004](adr/0004-persistencia-en-memoria.md) | Persistencia en memoria | Histórico, supersedido |
| [0005](adr/0005-frontend-react-vite.md) | Frontend: React 19 + Vite | Aceptado |
| [0006](adr/0006-elasticsearch-indexacion-noticias.md) | Motor de búsqueda: Elasticsearch 8.12 | Aceptado |
| [0007](adr/0007-frontend-bootstrap-react-router.md) | UI: Bootstrap 5 + React Router | Aceptado |
| [0008](adr/0008-calidad-codigo-ruff-ty.md) | Calidad: Ruff + Ty | Aceptado |
| [0009](adr/0009-estrategia-testing-pytest-vitest-playwright.md) | Testing: Pytest + Vitest + Playwright | Aceptado |
| [0010](adr/0010-migraciones-bd-alembic-(obsoleto).md) | Migraciones: Alembic (histórico) | Histórico |
| [0011](adr/0011-pipeline-cicd-github-actions.md) | CI/CD: GitHub Actions | Aceptado |
| [0012](adr/0012-seguridad-scanning-pip-audit-trivy-sonarqube.md) | Seguridad: pip-audit + Trivy + SonarQube | Aceptado |
| [0013](adr/0013-documentacion-backend-mkdocs-docstrings.md) | Documentación backend: docstrings + MkDocs | Aceptado |
| [0014](adr/0014-integración-api-gestion-fuentes-alertas.md) | Integración con API REST para Gestión de Fuentes y Alertas | Aceptado |
| [0015](adr/0015-postgresql-sqlalchemy-alembic.md) | Persistencia: PostgreSQL + SQLAlchemy + Alembic | Aceptado |

---

## 4. Modelo de datos

### 4.1 Esquema relacional principal (PostgreSQL)

Las entidades principales se persisten en PostgreSQL y el esquema se crea con
`alembic upgrade head`.

```
users
  id              int   (autoincremental)
  email           str   (único)
  password        str   (hash bcrypt)
  first_name      str
  last_name       str
  organization    str
  roles           many-to-many → roles
  is_verified     bool  (default: False)

alerts
  id              int
  user_id         int   → users.id
  name            str
  descriptors     list[str]   (3–10 palabras clave)
  categories      list[AlertCategoryItem]  (código + label IPTC)
  cron_expression str

rss_channels
  id                     int
  information_source_id  int  → information_sources.id
  url                    str
  category_id            int  → categories.id

notifications
  id         int
  alert_id   int  → alerts.id
  timestamp  datetime
  metrics    list[Metric]

stats
  id                   int
  total_news           int
  total_notifications  int
  metrics              list[Metric]
```

### 4.2 Documentos indexados (Elasticsearch — índice `newsradar_articles`)

```json
{
  "title":        "string",
  "link":         "string  (ID en Elastic — evita duplicados)",
  "summary":      "string",
  "published_at": "date",
  "channel_id":   "integer",
  "category_id":  "integer"
}
```

---

## 5. Flujos principales

### 5.1 Captura y notificación (motor RSS)

```
asyncio background task (cada 30s en desarrollo)
    │
    ▼
Para cada canal en rss_channels_store:
    │
    ├── feedparser.parse(channel.url)
    └── es_client.index(index="newsradar_articles", id=entry.link, doc=...)

Para cada alerta en alerts_store:
    │
    ├── Query Elasticsearch: multi_match sobre title+summary
    │   con filtro published_at >= now-15m
    │
    └── Si hay hits → Notification en notifications_store
```

### 5.2 Registro de usuario

```
POST /api/v1/auth/register
    │
    ▼
Validar (Pydantic) ──► ¿Email ya existe? ──► 409 Conflict
    │
   NO
    ▼
Crear UserInDB en users_store (is_verified=False)
    │
    ▼
create_verification_token(email)  →  JWT (exp=24h)
    │
    ▼
send_verification_email()  →  smtplib → Mailtrap
    │
    ▼
201 Created
```

### 5.3 Login

```
POST /api/v1/auth/login
    │
    ▼
Buscar usuario en users_store por email
    │
    ▼
verify_password(payload.password, user.password)  ← bcrypt
    │
    ▼
Generar UUID token → active_tokens[token] = user.id
    │
    ▼
200 OK  { access_token, token_type: "bearer" }
```

---

## 6. Infraestructura y despliegue

### 6.1 Levantar el entorno de desarrollo

```bash
# Solo Elasticsearch (PostgreSQL no requerido)
cd Backend && docker compose up -d

# Backend API
cd Backend && pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend
cd Frontend && npm install && npm run dev
```

O con el Makefile desde la raíz del repositorio:

```bash
make up   # Levanta Elasticsearch
make ci   # Pipeline CI completo en local
```

### 6.2 Variables de entorno requeridas (`Backend/.env`)

```
ELASTICSEARCH_URL=http://localhost:9200
SECRET_KEY=<clave_aleatoria_segura>
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=587
MAIL_USERNAME=<usuario_mailtrap>
MAIL_PASSWORD=<contraseña_mailtrap>
MAIL_FROM=noreply@newsradar.local
```

> `DATABASE_URL` ya no es necesaria. El fichero `.env` está en `.gitignore`
> y nunca se sube al repositorio.

---

## 7. Atributos de calidad

| Atributo | Mecanismo |
|---|---|
| Mantenibilidad | Modelos Pydantic como única fuente de verdad para entidades |
| Testabilidad | In-memory stores permiten tests sin servicios externos; mocks con pytest |
| Seguridad | JWT, bcrypt, verificación de email, roles GESTOR/LECTOR |
| Simplicidad operativa | Sin ORM ni migraciones; arranque con un único proceso uvicorn |
| Observabilidad | SonarQube (Sprint 5); health check en `/api/v1/health` |
| Desplegabilidad | Docker Compose (solo Elasticsearch); pipeline CI/CD GitHub Actions |

---

## 8. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-03-24 | Versión inicial tras Sprints 0 y 1 |
| 1.1 | 2026-04-08 | Eliminación de PostgreSQL/SQLAlchemy. Persistencia in-memory (ADR 0004). ADR 0010 marcado como supersedido. Diagramas, modelo de datos y variables de entorno sincronizados con el código real. |
