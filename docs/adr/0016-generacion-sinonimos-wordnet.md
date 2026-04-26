# ADR 0016: Generación local de sinónimos con NLTK WordNet

- **Estado:** Aceptado
- **Fecha:** 2026-04-27
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez) y Backend
- **Reemplaza a:** —
- **Relacionado con:** [ADR 0001](0001-framework-backend-fastapi.md), [ADR 0009](0009-estrategia-testing-pytest-vitest-playwright.md), [ADR 0014](0014-integracion-api-gestion-fuentes-alertas.md)

---

## Contexto

La creación de alertas requiere introducir entre 3 y 10 descriptores o palabras
clave. Para reducir trabajo manual y mejorar la cobertura de búsquedas en
castellano, se necesita generar sinónimos para un término base dentro del flujo
normal de alta de alertas.

La solución debía cumplir varias restricciones:

- No depender de APIs externas, servicios alojados ni costes de uso.
- No introducir un servidor local adicional de IA, como Ollama, salvo necesidad
  justificada.
- Priorizar castellano como idioma principal.
- Mantener una solución ligera, determinista y sencilla de operar en la
  arquitectura actual de backend FastAPI y frontend.

## Decisión

Se decide implementar la generación de sinónimos en el backend mediante
**NLTK WordNet** y el corpus **omw-1.4** de Open Multilingual WordNet.

El backend expone un endpoint autenticado para el flujo de alertas:

- `GET /api/v1/alerts/synonyms?term=<termino>&limit=<3-10>`

La lógica queda encapsulada en `app/core/synonyms.py` y aplica:

- Normalización de espacios, guiones bajos y capitalización.
- Búsqueda en WordNet usando el idioma `spa`.
- Variantes simples para plurales frecuentes en castellano.
- Limpieza, deduplicación y exclusión del término original.
- Límite configurable dentro del rango soportado de 3 a 10 resultados.

## Justificación

- **Simplicidad operativa:** NLTK se ejecuta dentro del proceso del backend y no
  requiere nuevos contenedores, workers ni servicios locales.
- **Coste cero:** WordNet y Open Multilingual WordNet son recursos locales y no
  generan llamadas a proveedores externos.
- **Determinismo:** La respuesta depende de corpus versionados y reglas locales,
  no de prompts, sampling ni disponibilidad de un modelo remoto.
- **Buen soporte inicial en castellano:** OMW permite consultar lemas en español
  mediante `lang="spa"`, suficiente para el caso de uso de descriptores.
- **Extensibilidad:** La separación en un módulo de core permite sustituir o
  enriquecer la fuente léxica más adelante sin cambiar el contrato del frontend.

## Alternativas consideradas

### LLM local

Se descartó introducir un LLM local porque aumenta el consumo de CPU/RAM, añade
dependencias operativas y requiere gestionar modelos, arranque y salud de un
proceso adicional. Para generar una lista corta de sinónimos, el coste y la
complejidad no están justificados.

### APIs externas de lenguaje

Se descartaron porque incumplen la restricción de no usar servicios alojados o
potencialmente de pago, y añaden dependencia de red y proveedor.

### Diccionario propio en base de datos

Se descartó como solución inicial porque obligaría a mantener datos léxicos
manualmente. Puede ser una extensión futura si el dominio periodístico necesita
sinónimos curados.

## Consecuencias

### Positivas

- La funcionalidad queda disponible para el frontend sin cambiar el modelo de
  datos de alertas.
- El comportamiento ante términos sin resultados es simple: se devuelve una
  lista vacía y la interfaz mantiene la entrada manual.
- La ejecución es rápida y local para listas cortas de descriptores.

### Riesgos / costes

- El paquete `nltk` no incluye los corpus por defecto. Los datos `wordnet` y
  `omw-1.4` deben instalarse en CI, en la imagen Docker y en entornos locales.
- La cobertura léxica de OMW no es equivalente a un tesauro especializado; puede
  haber términos periodísticos, nombres propios o neologismos sin resultados.
- La lematización en castellano se mantiene deliberadamente ligera; no se añade
  una dependencia pesada de NLP para este caso de uso.

## Implicaciones de testing

Se añaden pruebas unitarias para:

- Búsqueda básica de sinónimos en castellano.
- Deduplicación.
- Exclusión del término original.
- Manejo del límite de resultados.
- Comportamiento sin resultados.

También se añade una prueba funcional del endpoint del backend y una prueba del
servicio de frontend que consume la API.

## Implicaciones operativas

La imagen Docker descarga `wordnet` y `omw-1.4` durante el build. La pipeline de
CI instala los mismos corpus antes de ejecutar las pruebas que los necesitan.

Si los corpus no están disponibles en runtime, el backend devuelve `503` para el
endpoint de sinónimos en lugar de fallar con un error interno.
