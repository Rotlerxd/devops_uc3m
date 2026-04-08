# ADR 0004: ORM y persistencia de datos (SQLAlchemy asíncrono + PostgreSQL)

- **Estado:** Aceptado
- **Fecha:** 2026-03-16
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

El proyecto requiere dos sistemas de gestión de datos diferenciados (según el
enunciado, sección 4):

1. Un **sistema gestor de datos para las entidades del sistema** (usuarios,
   alertas, fuentes RSS, roles, notificaciones).
2. Un **sistema gestor de datos para el almacenamiento de la información**
   capturada (noticias indexadas, búsqueda de texto completo).

Este ADR cubre la decisión sobre el primer sistema (entidades relacionales).
La elección del motor de búsqueda para noticias se trata de forma independiente.

Al haber elegido FastAPI como framework asíncrono (ver ADR 0001), las consultas
a la base de datos relacional no pueden ser síncronas: una consulta bloqueante
detendría el Event Loop de Python, degradando el rendimiento de toda la API
mientras dura esa operación.

## Decisión

Se decide utilizar:

- **PostgreSQL 15** como motor de base de datos relacional.
- **SQLAlchemy 2.0** como ORM, configurado en modo asíncrono.
- **asyncpg** como driver de conexión asíncrono entre SQLAlchemy y PostgreSQL.
- **Docker** para levantar la instancia de PostgreSQL en desarrollo (imagen
  `postgres:15-alpine`).

## Justificación

- PostgreSQL es el motor relacional más robusto de código abierto, con soporte
  completo de tipos, transacciones ACID y compatibilidad con `asyncpg`.
- SQLAlchemy 2.0 introduce un API moderno y explícito para el modo asíncrono
  (`AsyncSession`, `async with engine.begin()`), eliminando los problemas de
  la API legacy de SQLAlchemy 1.x con `asyncio`.
- `asyncpg` es el driver asíncrono más rápido disponible para PostgreSQL en
  Python y es el recomendado por la documentación de SQLAlchemy 2.0.
- La combinación FastAPI + SQLAlchemy 2.0 + asyncpg es el stack de referencia
  más documentado y probado para APIs Python asíncronas.

## Consecuencias

### Positivas

- Se aprovecha al máximo el rendimiento de E/S asíncrono: la API puede atender
  otras peticiones mientras espera respuesta de la base de datos.
- SQLAlchemy 2.0 ofrece un modelo de definición de esquemas claro (declarativo
  con `Base`) y consultas seguras frente a inyección SQL.
- La creación automática de tablas en el startup de la aplicación
  (`Base.metadata.create_all`) simplifica el despliegue inicial.

### Negativas / riesgos

- Ciertas operaciones ORM deben manejarse con cuidado con `await` y
  `AsyncSession` para evitar el error `"Event loop is closed"` o desconexiones
  prematuras.
- Las migraciones de esquema en producción requerirán **Alembic** (pendiente
  de configurar en sprints posteriores). Usar `create_all` en producción no
  es aceptable para cambios de esquema sin pérdida de datos.

## Relación con otros sistemas de datos

| Sistema | Motor | Propósito |
|---|---|---|
| Entidades (este ADR) | PostgreSQL + SQLAlchemy | Usuarios, alertas, fuentes, roles |
| Noticias / búsqueda | Elasticsearch 8.12 | Indexación y búsqueda de texto completo |

Ambos servicios se levantan mediante el mismo `docker-compose.yml` del proyecto.

## Variables de entorno requeridas

```
POSTGRES_USER=newsradar_admin
POSTGRES_PASSWORD=<contraseña_segura>
POSTGRES_DB=newsradar_db
DATABASE_URL=postgresql+asyncpg://newsradar_admin:<contraseña>@localhost:5432/newsradar_db
```
