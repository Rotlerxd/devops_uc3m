# ADR 0001: Elección del framework backend (FastAPI)

- **Estado:** Aceptado
- **Fecha:** 2026-03-16
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

Para el desarrollo de la API REST del proyecto NewsRadar necesitábamos un
framework de Python moderno que permitiera un desarrollo ágil, alto rendimiento
y buena integración con herramientas de documentación automática. Las
alternativas evaluadas fueron:

- **Flask**: ligero y flexible, pero requiere configuración manual de validación
  y documentación.
- **Django REST Framework**: completo y maduro, pero con mayor overhead para
  proyectos de tamaño mediano y curva de aprendizaje más alta.
- **FastAPI**: moderno, asíncrono, con validación automática de datos y
  generación de documentación OpenAPI incluida.

## Decisión

Se decide utilizar **FastAPI** junto con **Pydantic V2** como framework principal
del backend.

## Justificación

- Genera documentación interactiva (Swagger UI / OpenAPI) de forma automática,
  lo que facilita las pruebas durante los Sprint Reviews y cubre el requisito
  del enunciado de documentar la API con OpenAPI.
- La validación de datos es automática y estricta gracias a Pydantic, reduciendo
  el código de validación manual.
- El soporte nativo de `async/await` es necesario para integrarse correctamente
  con el driver asíncrono de PostgreSQL (`asyncpg`) y con Elasticsearch sin
  bloquear el Event Loop.
- Es el framework utilizado en el fichero de referencia `newsradar_api.zip`
  proporcionado por el enunciado.

## Consecuencias

### Positivas

- Validación automática de datos de entrada y salida mediante esquemas Pydantic.
- Documentación Swagger UI disponible en `/docs` desde el primer momento.
- Alto rendimiento en operaciones de I/O gracias al modelo asíncrono.
- Ecosistema activo y compatible con SQLAlchemy 2.0 asíncrono.

### Negativas / riesgos

- Requiere manejar el paradigma de programación asíncrona (`async/await`) en
  Python, lo que aumenta ligeramente la curva de aprendizaje frente a un
  framework síncrono tradicional.
- Algunas operaciones complejas con el ORM deben manejarse con cuidado para
  evitar errores de cierre prematuro del Event Loop.

## Alternativas consideradas y descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Flask | Sin soporte asíncrono nativo; validación y documentación manuales |
| Django REST Framework | Overhead excesivo; no alineado con el stack asíncrono elegido |
