# ADR 0015: Persistencia con PostgreSQL, SQLAlchemy y Alembic

- **Estado:** Aceptado
- **Fecha:** 2026-04-22
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez) y Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** [ADR 0004](0004-persistencia-en-memoria.md)
- **Relacionado con:** [ADR 0002](0002-autenticacion-jwt.md), [ADR 0008](0008-calidad-codigo-ruff-ty.md), [ADR 0011](0011-pipeline-cicd-github-actions.md)

---

## Contexto

La rama actual consolida la persistencia relacional del backend sobre PostgreSQL.
El código ya utiliza SQLAlchemy para las entidades principales (`users`, `alerts`,
`notifications`, `information_sources`, `rss_channels`, `stats`), y el uso de
estructuras en memoria había quedado desalineado tanto con la implementación
real como con las necesidades de validación en CI.

Además, Ty detectaba falsos positivos y huecos de tipado en los modelos ORM
declarados con el estilo clásico `Column(...)`, y la creación implícita del
esquema en el arranque de la aplicación hacía más difícil garantizar entornos
reproducibles.

## Decisión

Se decide adoptar de forma explícita:

- **PostgreSQL 15** como persistencia principal de entidades del backend.
- **SQLAlchemy 2.0** con modelos tipados (`Mapped[...]`, `mapped_column(...)`), en modo **síncrono** (no async).
- **Alembic** como única fuente de verdad para la creación y evolución del esquema.
- **JWT stateless** para autenticación, sin almacenamiento de sesiones en memoria.

## Justificación

- La persistencia relacional cubre mejor los requisitos funcionales de usuarios,
  alertas, notificaciones y fuentes RSS.
- Los modelos tipados reducen deuda técnica y eliminan falsos positivos de Ty en
  asignaciones sobre instancias ORM.
- Alembic permite que CI y los entornos locales construyan el esquema de forma
  reproducible con `alembic upgrade head`.
- La eliminación de stores y sesiones en memoria alinea la implementación con la
  arquitectura objetivo del proyecto.

## Consecuencias

### Positivas

- Persistencia real entre reinicios del backend.
- Esquema versionado y verificable en CI.
- Tipado ORM más robusto y mantenible.
- Autenticación consistente con el ADR 0002.

### Riesgos / costes

- Mayor dependencia operativa de PostgreSQL y migraciones.
- Mayor cuidado al evolucionar el esquema y los datos semilla.
- La documentación previa basada en memoria debe mantenerse actualizada para no
  volver a divergir.
