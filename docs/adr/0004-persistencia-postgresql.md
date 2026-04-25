# ADR 0004: Persistencia con PostgreSQL 15 + SQLAlchemy 2.0 síncrono

- **Estado:** Aceptado
- **Fecha:** 2026-04-13
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** Versión previa de este ADR (2026-04-08) que optaba por persistencia en memoria con `dict` de Python
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0001](0001-framework-backend-fastapi.md), [ADR 0006](0006-elasticsearch-indexacion-noticias.md), [ADR 0010](0010-migraciones-bd-alembic.md)

---

## Contexto

Durante el Sprint 3 se experimentó con persistencia en memoria (`dict` de Python)
siguiendo una sugerencia inicial del profesor para simplificar el desarrollo.
Al avanzar a los Sprints 4.1 y 4.2 (estadísticas globales, relaciones
usuario/rol/alerta/categoría, dashboard con datos agregados y despliegue con
Docker Compose), las limitaciones del enfoque en memoria se hicieron evidentes:

- Los datos se perdían en cada reinicio del servidor, lo que complicaba la
  verificación funcional a lo largo de varias sesiones de pruebas.
- El escalado a múltiples instancias previsto para el Sprint 6 no era viable
  sin un almacenamiento externo compartido.
- Las relaciones muchos-a-muchos (usuario ↔ rol) y las consultas agregadas
  para estadísticas globales (IM-06) resultaban engorrosas sobre estructuras
  de datos planas.

## Decisión

Se adopta **PostgreSQL 15** como motor de persistencia para todas las
entidades relacionales del sistema, accedido desde Python mediante
**SQLAlchemy 2.0 en modo síncrono** con el driver **psycopg2-binary**.

La configuración vive en [Backend/app/db/database.py](../../Backend/app/db/database.py):

```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

Los modelos ORM se definen en [Backend/app/models/models.py](../../Backend/app/models/models.py)
y cubren las tablas: `users`, `roles`, `alerts`, `notifications`, `categories`,
`information_sources`, `rss_channels`, `stats`, más la tabla de asociación
`user_roles`.

La creación inicial de tablas en entornos de desarrollo y test se realiza al
arranque mediante `Base.metadata.create_all(bind=engine)` en `main.py`. Los
datos iniciales (fuentes y canales RSS) se cargan desde
`Backend/app/data/rss_seed.json` con la función `create_seed_data()`.

## Justificación

- **Persistencia real** entre reinicios del servidor y entre despliegues
  sucesivos del Sprint 6.
- **Soporte para estadísticas globales** (IM-06) y consultas relacionales
  complejas necesarias para el dashboard del Sprint 4.2.
- **SQLAlchemy síncrono** (no async): simplifica la depuración y el stack de
  ejecución, y evita la complejidad de `async`/`await` en toda la capa de
  acceso a datos. El throughput de FastAPI sigue siendo adecuado para la
  escala del proyecto.
- **Docker Compose** permite levantar PostgreSQL junto al backend con un
  único comando, cumpliendo el requisito de despliegue simple del Sprint 6.

## Consecuencias

### Positivas
- Los datos sobreviven a reinicios y redespliegues.
- Posibilidad de escalar a múltiples réplicas del backend sobre una misma
  base de datos.
- SQL estándar disponible para consultas agregadas y reporting.

### Negativas / riesgos
- Se introduce una dependencia operativa (PostgreSQL) que debe estar
  disponible al arrancar el backend. Docker Compose lo mitiga.
- La gestión de cambios de esquema en producción requiere Alembic; la
  configuración actual de Alembic tiene defectos pendientes de corregir
  (ver [ADR 0010](0010-migraciones-bd-alembic.md)).

## Relación con otros sistemas de datos

| Sistema | Motor | Propósito |
|---|---|---|
| Entidades relacionales (este ADR) | PostgreSQL 15 + SQLAlchemy 2.0 sync | Usuarios, roles, alertas, fuentes, canales RSS, notificaciones, estadísticas |
| Noticias / búsqueda | Elasticsearch 8.12 | Indexación y búsqueda de texto completo |