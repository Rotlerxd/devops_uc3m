# ADR 0010: Migraciones de base de datos (Alembic)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0015](0015-postgresql-sqlalchemy-alembic.md)

---

## Contexto

La creación inicial de tablas en desarrollo se realiza con
`Base.metadata.create_all()` en el startup de FastAPI, pero en producción es
necesario versionar la evolución del esquema sin perder los datos existentes
en cada despliegue.

## Decisión

Adoptar **Alembic** como sistema oficial de migraciones de esquema para
PostgreSQL, integrado con SQLAlchemy y configurado en `Backend/alembic/`.

El flujo es:

```bash
# Generar una nueva migración a partir de los modelos actuales
cd Backend && alembic revision --autogenerate -m "<descripción>"

# Aplicar las migraciones pendientes
cd Backend && alembic upgrade head
```

## Justificación

- **Integración nativa con SQLAlchemy:** reutiliza las definiciones de
  modelos del backend.
- **Autogeneración de migraciones:** reduce el error humano al derivar los
  cambios de esquema directamente del código ORM.
- **Versionado y reversibilidad:** cada migración queda como un artefacto
  numerado en `alembic/versions/`, aplicable y revertible.

## Consecuencias

### Positivas
- Despliegues seguros: el esquema de producción se actualiza sin destruir
  los datos.
- Trazabilidad: cada cambio de esquema queda registrado en el repositorio.

### Negativas / riesgos
- Requiere disciplina del equipo para regenerar la migración cada vez que
  cambien los modelos.

## Relación con el ADR 0015

El [ADR 0015](0015-postgresql-sqlalchemy-alembic.md) ratifica esta decisión
como parte de la persistencia vigente del proyecto (PostgreSQL 15 +
SQLAlchemy 2.0 síncrono + Alembic).