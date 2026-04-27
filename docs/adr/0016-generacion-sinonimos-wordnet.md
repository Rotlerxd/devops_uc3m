# ADR 0016: Generación local de sinónimos con NLTK WordNet

- **Estado:** Aceptado
- **Fecha:** 2026-04-27
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez) y Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** —
- **Relacionado con:** [ADR 0001](0001-framework-backend-fastapi.md), [ADR 0009](0009-estrategia-testing-pytest-vitest-playwright.md), [ADR 0014](0014-integracion-api-gestion-fuentes-alertas.md)

---

## Contexto

La creación de alertas requiere introducir entre 3 y 10 descriptores o palabras
clave. Para reducir trabajo manual y mejorar la cobertura de búsquedas en
castellano, se necesita generar sinónimos para un término base dentro del flujo
normal de alta de alertas.

Además, se observó latencia perceptible en la primera petición de sinónimos
porque NLTK/OMW inicializa parte de los recursos de forma perezosa en memoria.

Tras la primera implementación, se detectó que WordNet/OMW no cubre bien parte
del vocabulario típico de RSS, noticias y tecnología. Términos como
`tecnología`, `ingeniería` o `gpu` pueden devolver pocos resultados o ninguno.
El producto necesita mantener resultados precisos cuando WordNet existe, pero
también ofrecer sugerencias relacionadas para vocabulario arbitrario.

La solución debía cumplir varias restricciones:

- No depender de APIs externas, servicios alojados ni costes de uso.
- No introducir un servidor local adicional de IA, como Ollama, salvo necesidad
  justificada.
- Priorizar castellano como idioma principal.
- Mantener una solución ligera, determinista y sencilla de operar en la
  arquitectura actual de backend FastAPI y frontend.

## Decisión

Se decide implementar la generación de sinónimos en el backend mediante
**NLTK WordNet** y el corpus **omw-1.4** de Open Multilingual WordNet, con una
capa opcional de **fastText** como fallback de términos relacionados.

El backend expone un endpoint autenticado para el flujo de alertas:

- `GET /api/v1/alerts/synonyms?term=<termino>&limit=<3-10>`
- `GET /api/v1/alerts/synonyms/warmup`

La lógica queda encapsulada en `app/core/synonyms.py` y aplica:

- Normalización de espacios, guiones bajos y capitalización.
- Búsqueda en WordNet usando el idioma `spa`.
- Variantes simples para plurales frecuentes en castellano.
- Fallback léxico local para alias/acrónimos frecuentes (por ejemplo `ia`).
- Descomposición de frases en tokens cuando no hay entrada directa útil.
- Fallback opcional con vectores fastText locales cuando WordNet no alcanza el
  límite configurado.
- Warmup idempotente en backend para precargar recursos NLTK/OMW mediante una
  consulta inocua y, si está configurado, cargar el modelo fastText.
- Limpieza, deduplicación y exclusión del término original.
- Límite configurable dentro del rango soportado de 3 a 10 resultados.

El orden de resultados es determinista: primero WordNet/OMW, después alias
léxicos locales y finalmente candidatos fastText ordenados por similitud del
modelo. Los candidatos fastText se tratan explícitamente como términos
relacionados, no como sinónimos estrictos.

El modelo fastText no se descarga en runtime. La ruta del modelo se configura
mediante `NEWSRADAR_FASTTEXT_MODEL_PATH`. Si la variable no está definida, el
fichero no existe o el paquete no está disponible, el backend deshabilita esa
capa y conserva el comportamiento WordNet/OMW.

La capa fastText queda marcada como experimental. No se recomienda activarla en
producción por defecto porque entrega términos relacionados, no sinónimos
estrictos, y porque su calidad y consumo de memoria dependen del modelo local
elegido. Se mantiene como opción explícita para entornos que quieran evaluar
mayor cobertura de vocabulario.

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
- **Mejor UX inicial:** El warmup reduce la latencia visible de la primera
  generación de sinónimos sin bloquear el flujo de creación de alertas.
- **Mayor cobertura:** fastText aporta vecinos semánticos para vocabulario
  técnico o periodístico que no aparece en WordNet/OMW.
- **Fallback local:** fastText mantiene el requisito de coste cero y ejecución
  local, sin introducir un LLM ni un proceso servidor adicional.

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

### ConceptNet

Se descartó como dependencia principal porque introduce una fuente más amplia
pero menos controlada para este flujo, y su integración local exigiría gestionar
datos adicionales. Puede reevaluarse si se necesita una base semántica
explícita, no solo similitud vectorial.

### Modelo local pequeño (SmolLM2 u otros)

Se mantiene fuera de alcance en esta iteración por coste operativo y huella de
runtime (modelos, carga en memoria y latencia), además de introducir
comportamiento menos determinista para un flujo que se beneficia de reglas
léxicas estables.

### fastText como fuente principal

Se descartó porque sus vecinos vectoriales son términos semánticamente
relacionados, no necesariamente sinónimos. WordNet/OMW sigue siendo la fuente
de mayor precisión y fastText solo completa resultados cuando falta cobertura.

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
- La cobertura fastText depende de que exista un fichero de vectores local en
  `NEWSRADAR_FASTTEXT_MODEL_PATH`. La aplicación no lo descarga ni lo versiona
  en el repositorio.
- Los modelos fastText preentrenados pueden ocupar cientos de MB o más, por lo
  que su uso tiene impacto en almacenamiento, memoria y tiempo de carga. Por
  eso se cargan de forma perezosa y el warmup solo los precarga si están
  configurados.
- Los vectores fastText preentrenados requieren citar la referencia oficial
  indicada por fastText:
  https://fasttext.cc/docs/en/pretrained-vectors#references
- La lematización en castellano se mantiene deliberadamente ligera; no se añade
  una dependencia pesada de NLP para este caso de uso.
- Se añade una llamada de warmup desde frontend al abrir el modal de alertas; es
  no bloqueante y se ejecuta una sola vez por sesión de pantalla.

## Implicaciones de testing

Se añaden pruebas unitarias para:

- Búsqueda básica de sinónimos en castellano.
- Deduplicación.
- Exclusión del término original.
- Manejo del límite de resultados.
- Comportamiento sin resultados.
- Warmup exitoso, idempotencia y manejo de fallo sin repetir inicialización
  costosa.
- Uso de fastText cuando WordNet devuelve pocos resultados.
- Funcionamiento sin fastText configurado.
- Manejo de ruta de modelo inexistente.
- Orden determinista: WordNet/OMW antes de fastText.
- Filtrado, deduplicación, exclusión del término original y acrónimos con
  capitalización variable.

También se añade una prueba funcional del endpoint del backend y una prueba del
servicio de frontend que consume la API, incluyendo el trigger de warmup.

Las pruebas unitarias de fastText usan dobles de prueba y no descargan ni cargan
vectores reales en CI.

## Implicaciones operativas

La imagen Docker descarga `wordnet` y `omw-1.4` durante el build. La pipeline de
CI instala los mismos corpus antes de ejecutar las pruebas que los necesitan.

El paquete Python compatible con fastText se instala con las dependencias del
backend, pero el fichero de vectores es opcional y externo. En producción puede
apuntarse `NEWSRADAR_FASTTEXT_MODEL_PATH` a un modelo español preentrenado de
fastText, aunque esta ruta se considera experimental y no forma parte del
comportamiento productivo normal. Si falta, se registra un aviso y se continúa
con WordNet/OMW.

Si los corpus no están disponibles en runtime, el backend devuelve `503` para el
endpoint de sinónimos en lugar de fallar con un error interno.

El warmup se ejecuta exclusivamente en backend. El frontend solo dispara el
endpoint de warmup y nunca carga NLTK ni fastText localmente.
