# ADR 0010: Migraciones de base de datos (Alembic)

- **Estado:** Aceptado
- **Fecha:** 2026-03-25
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0004](0004-orm-sqlalchemy-asincrono-postgresql.md)

---

## Contexto

En el ADR 0004 se documentó que la creación inicial de tablas se realiza con
`Base.metadata.create_all()` en el startup de FastAPI. Sin embargo, el propio
ADR señala que:

> "Las migraciones de esquema en producción requerirán Alembic (pendiente de
> configurar en sprints posteriores). Usar create_all en producción no es
> aceptable para cambios de esquema sin pérdida de datos."

A medida que el proyecto avanza (Sprint 2+), se necesitan:
- Añadir modelos nuevos (Alerta, FuenteRSS, Notificacion).
- Modificar esquemas existentes sin perder datos.
- Versionar los cambios de esquema de forma reproducible.
- Ejecutar migraciones automáticas en CI/CD.

## Decisión

Se configura **Alembic** como sistema de migraciones de esquema para la base
de datos PostgreSQL, con soporte asíncrono mediante `asyncpg`.

## Justificación

- Alembic es la herramienta oficial de migraciones para SQLAlchemy, creada
  por el mismo equipo. Integración perfecta con SQLAlchemy 2.0 declarativo.
- Soporte para modo asíncrono (`async_engine_from_config` + `run_sync`).
- Generación automática de migraciones a partir de diferencias entre modelos
  y base de datos (`--autogenerate`).
- Control granular: cada migración es un fichero versionado con `upgrade()`
  y `downgrade()`.
- Ampliamente documentado y usado en la comunidad FastAPI + SQLAlchemy.

## Consecuencias

### Positivas

- Cambios de esquema versionados y reproducibles.
- Migraciones reversibles (`alembic downgrade`).
- Generación automática de migraciones con `alembic revision --autogenerate`.
- Separación clara entre bootstrap inicial (create_all en dev) y migraciones
  controladas (Alembic en producción).
- Integrable en el pipeline de CI/CD para validar que las migraciones aplican.

### Negativas / riesgos

- Curva de aprendizaje: el equipo debe entender el flujo de Alembic
  (revision → upgrade → downgrade).
- Las migraciones generadas automáticamente deben revisarse manualmente
  antes de aplicar: Alembic puede no detectar todos los cambios (renombres,
  cambios de tipo con transformación de datos).
- En desarrollo, `create_all` sigue siendo útil para bootstrap rápido; Alembic
  solo es necesario para cambios incrementales.

## Flujo de uso

```bash
# Generar migración automática tras modificar modelos
cd Backend
alembic revision --autogenerate -m "describir_cambio"

# Revisar el archivo generado en alembic/versions/
# Aplicar migración
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## Configuración aplicada

- `Backend/alembic.ini` — configuración principal
- `Backend/alembic/env.py` — entorno asíncrono con SQLAlchemy 2.0
- `Backend/alembic/script.py.mako` — plantilla para nuevas revisiones
- `Backend/alembic/versions/0001_initial_schema.py` — migración inicial
