# ADR 0010: Migraciones de base de datos con Alembic

- **Estado:** Aceptado
- **Fecha:** 2026-04-13
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez)
- **Reemplaza a:** —
- **Reemplazado por:** —
- **Relacionado con:** [ADR 0004](0004-persistencia-postgresql.md)

---

## Contexto

Tras el retorno a PostgreSQL documentado en el [ADR 0004](0004-persistencia-postgresql.md),
el proyecto necesita un mecanismo para evolucionar el esquema de la base de
datos entre versiones sin perder los datos existentes en cada entorno.

Durante el desarrollo local y en los tests funcionales las tablas se crean
al arrancar el backend mediante `Base.metadata.create_all(bind=engine)`, lo
que es aceptable para entornos efímeros pero inadecuado para producción,
donde los despliegues sucesivos del Sprint 6 deben preservar los datos ya
cargados.

## Decisión

Se adopta **Alembic** como herramienta oficial de migraciones de esquema
para PostgreSQL, configurado en [Backend/alembic/](../../Backend/alembic/)
con `alembic.ini`, `alembic/env.py` y el directorio `alembic/versions/`.

El flujo previsto es:

```bash
# Generar una nueva migración a partir de los modelos actuales
cd Backend && alembic revision --autogenerate -m "<descripción>"

# Aplicar las migraciones pendientes a la base de datos
cd Backend && alembic upgrade head
```

## Justificación

- **Integración nativa con SQLAlchemy:** reutiliza las definiciones de
  modelos ya existentes en `app/models/models.py`.
- **Autogeneración de migraciones:** reduce el error humano al derivar los
  cambios de esquema directamente del código ORM.
- **Versionado y reversibilidad:** cada migración queda como un artefacto
  numerado en `alembic/versions/`, aplicable y revertible.

## Consecuencias

### Positivas
- Despliegues seguros en el Sprint 6: el esquema se actualiza sin destruir
  los datos.
- Trazabilidad: cada cambio de esquema queda registrado en el repositorio.

### Negativas / riesgos
- Mientras no se corrijan los defectos listados abajo, Alembic **no es
  operativo**: cualquier invocación de `alembic revision --autogenerate` o
  `alembic upgrade head` falla.

## Estado actual

Alembic está instalado como dependencia de desarrollo (`requirements-dev.txt`)
y los ficheros de configuración están presentes en el repositorio, pero la
configuración **no es ejecutable** por los siguientes defectos conocidos:

1. **Import roto en [Backend/alembic/env.py](../../Backend/alembic/env.py)**:
   la línea 7 hace `from app.db.models import Role, User`, pero los modelos
   reales viven en `app/models/models.py`. El módulo `app/db/models` no existe.
2. **Migración inicial desfasada**:
   [Backend/alembic/versions/0001_initial_schema.py](../../Backend/alembic/versions/0001_initial_schema.py)
   crea una tabla `usuarios` con columnas en español (`nombre`, `apellidos`,
   `organizacion`, `rol`), que no se corresponde con los modelos actuales
   (`users`, `roles`, `alerts`, `notifications`, etc.).

Mientras tanto, el arranque en desarrollo y tests sigue usando
`Base.metadata.create_all(bind=engine)` en `app/main.py`, y Alembic **no
está invocado** desde el Makefile, los workflows de GitHub Actions ni los
scripts de despliegue.

## Trabajo pendiente

Antes del Sprint 6 (despliegue con un único comando) deben completarse:

- [ ] Corregir el import de `Backend/alembic/env.py` para apuntar a
      `app.models.models` e importar todos los modelos.
- [ ] Regenerar `0001_initial_schema.py` con
      `alembic revision --autogenerate -m "initial schema"` sobre los modelos
      actuales (eliminando la migración antigua de `usuarios`).
- [ ] Integrar `alembic upgrade head` en el flujo de despliegue (script o
      Makefile) para sustituir a `create_all()` en producción.