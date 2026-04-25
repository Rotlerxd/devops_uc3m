# ADR 0010: Migraciones de base de datos (Alembic)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0004](0004-persistencia-en-memoria.md)

---

## Nota de supersesión

Este ADR queda **obsoleto** a raíz de la decisión documentada en el ADR 0004
(revisado el 2026-04-08): el proyecto no utiliza PostgreSQL ni SQLAlchemy
para la persistencia de entidades, adoptando en su lugar estructuras de datos
en memoria.

Al no existir base de datos relacional que gestionar, **Alembic deja de ser
necesario**. Los ficheros de configuración (`alembic.ini`, `alembic/env.py`,
`alembic/versions/`) pueden mantenerse en el repositorio como referencia
histórica o eliminarse en un sprint posterior.

---

## Contenido original (archivado)

### Contexto (original)

En el ADR 0004 original se documentó que la creación inicial de tablas se
realiza con `Base.metadata.create_all()` en el startup de FastAPI, señalando
que Alembic sería necesario para gestionar cambios de esquema en producción
sin pérdida de datos.

### Decisión original

Configurar Alembic como sistema de migraciones de esquema para PostgreSQL,
con soporte asíncrono mediante `asyncpg`.

### Por qué se descartó

La decisión de eliminar PostgreSQL (ADR 0004, 2026-04-08) hace que el problema
que Alembic resolvía —versionar cambios de esquema en una base de datos
relacional— deje de existir. No hay esquema que migrar.