# ADR 0004: Persistencia de datos en memoria (in-memory stores)

- **Estado:** Aceptado
- **Fecha:** 2026-04-08
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** Propuesta inicial de SQLAlchemy async + PostgreSQL
- **Reemplazado por:** [ADR 0015](0015-postgresql-sqlalchemy-alembic.md)
- **Relacionado con:** [ADR 0001](0001-framework-backend-fastapi.md), [ADR 0006](0006-elasticsearch-indexacion-noticias.md)

---

## Contexto
 
La propuesta inicial del proyecto contemplaba usar PostgreSQL con SQLAlchemy 2.0
asíncrono como motor de persistencia para las entidades del sistema (usuarios,
alertas, fuentes RSS, roles, notificaciones).
 
Tras una revisión con el profesor de la asignatura, se decide **no utilizar
PostgreSQL** para la persistencia de entidades. Los motivos son:
 
- El foco de la asignatura es el ciclo DevOps completo (CI/CD, testing,
  calidad, despliegue), no la integración con bases de datos relacionales.
- La complejidad operativa de mantener migraciones Alembic, gestionar
  conexiones asíncronas y depurar problemas de sesión SQLAlchemy añadía
  fricción innecesaria al desarrollo en el tiempo disponible.
- La verificación funcional del sistema (Anexo I del enunciado) se realiza
  a través del API REST; el mecanismo interno de persistencia no es objeto
  de evaluación directa.
 
## Decisión
 
Se decide utilizar **estructuras de datos en memoria** (`dict` de Python)
como mecanismo de persistencia para todas las entidades del sistema durante
el ciclo de vida del proceso del servidor.
 
```python
# Ejemplo del patrón adoptado en main.py
users_store:   dict[int, UserInDB]         = {}
alerts_store:  dict[int, Alert]            = {}
sources_store: dict[int, InformationSource] = {}
rss_channels_store: dict[int, RSSChannel]  = {}
```
 
Los datos se inicializan en el startup de la aplicación mediante una función
`create_seed_data()` que precarga usuarios, fuentes y canales RSS desde un
fichero `rss_seed.json`.
 
## Justificación
 
- **Simplicidad operativa:** no requiere levantar ni configurar ningún servicio
  adicional; el backend arranca solo con `uvicorn`.
- **Velocidad de desarrollo:** los modelos se definen como clases Pydantic sin
  necesidad de migraciones, ORM ni gestión de sesiones.
- **Suficiente para el alcance del proyecto:** el enunciado requiere que el
  sistema sea verificable funcionalmente a través del API; los datos en memoria
  satisfacen este requisito durante una sesión de uso.
- **Alineado con la decisión del profesor:** confirmada en Sprint 3.
 
## Consecuencias
 
### Positivas
 
- Eliminación de la dependencia de PostgreSQL, `asyncpg` y SQLAlchemy.
- El backend puede ejecutarse sin Docker ni servicios externos (salvo
  Elasticsearch para la indexación de noticias).
- Arranque instantáneo; sin tiempos de espera por conexiones de base de datos.
- Código más simple y directo, más fácil de leer y testear.
 
### Negativas / limitaciones aceptadas
 
- **Los datos no persisten entre reinicios del servidor.** Al detener el proceso,
  todos los datos creados durante la sesión se pierden. Los datos iniciales
  se recargan desde `rss_seed.json` en cada arranque.
- No apto para entornos de producción con múltiples instancias (no hay estado
  compartido entre réplicas).
- Las búsquedas y filtrados son O(n) sobre los diccionarios; aceptable para
  el volumen de datos del proyecto.
 
## Relación con otros sistemas de datos
 
| Sistema | Motor | Propósito |
|---|---|---|
| Entidades (este ADR) | Python `dict` in-memory | Usuarios, alertas, fuentes, roles |
| Noticias / búsqueda | Elasticsearch 8.12 | Indexación y búsqueda de texto completo |
 
Elasticsearch sí mantiene persistencia real en disco y no se ve afectado
por esta decisión.
 
## Datos de inicialización
 
El fichero `Backend/app/data/rss_seed.json` contiene las fuentes y canales RSS
iniciales que se cargan en cada arranque. Debe incluir un mínimo de 100 canales
de 10 medios distintos cubriendo las categorías IPTC de primer nivel, según
exige el enunciado.
