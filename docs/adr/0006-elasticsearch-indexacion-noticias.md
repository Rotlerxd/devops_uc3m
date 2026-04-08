# ADR 0006: Motor de búsqueda e indexación de noticias (Elasticsearch)

- **Estado:** Aceptado
- **Fecha:** 2026-03-09
- **Autores:** Equipo DevOps (Konstantin Rannev, Álvaro Rodriguez) y Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto
 
El enunciado requiere un sistema gestor de datos dedicado al almacenamiento
de la información capturada (noticias provenientes de canales RSS). Este
sistema debe permitir:
 
- Almacenar noticias con sus metadatos (título, resumen, origen, fecha, categoría
  IPTC).
- Búsqueda de texto completo sobre los campos de las noticias para detectar
  palabras clave de las alertas.
- Generación de estadísticas agregadas: nº de noticias por categoría, temas
  más frecuentes para las nubes de palabras.
 
Las alternativas consideradas fueron:
 
- **MongoDB**: base de datos documental flexible; buen soporte para documentos
  anidados, pero sin búsqueda de texto completo nativa de alto rendimiento.
- **Elasticsearch**: motor de búsqueda y análisis distribuido; diseñado
  específicamente para búsqueda de texto completo, agregaciones y análisis
  de documentos.
- **SQLite / tablas adicionales**: simple, pero no óptimo para búsqueda de
  texto completo a escala.
 
## Decisión
 
Se decide utilizar **Elasticsearch 8.12** para el almacenamiento e indexación
de noticias, gestionado mediante el cliente oficial `elasticsearch-py`.
 
## Justificación
 
- Elasticsearch está diseñado específicamente para búsqueda de texto completo,
  que es el núcleo de la funcionalidad de detección de alertas por palabra clave.
- Sus capacidades de agregación (`terms`, `date_histogram`) permiten calcular
  directamente las estadísticas requeridas por el panel de mando sin procesamiento
  adicional en Python.
- Permite extraer los términos más frecuentes por categoría para alimentar las
  nubes de palabras (Inspección manual nº 5 del Anexo I).
- Es una de las tecnologías candidatas mencionadas explícitamente en el enunciado.
 
## Consecuencias
 
### Positivas
 
- Búsqueda de texto completo de alto rendimiento sobre los campos `title` y
  `summary` de las noticias.
- Agregaciones nativas para estadísticas globales y por categoría.
- Análisis de texto con soporte de tokenización en español e inglés.
- Se integra con el `docker-compose.yml` del proyecto en modo `single-node`
  para desarrollo local.
- Es el único sistema con persistencia real en disco del proyecto: las noticias
  indexadas sobreviven a reinicios del servidor (ver ADR 0004).
 
### Negativas / riesgos
 
- Mayor complejidad operativa que una solución en memoria.
- La seguridad de Elasticsearch está desactivada en desarrollo
  (`xpack.security.enabled=false`) para simplificar la configuración local.
  **Debe habilitarse en producción.**
- Consume memoria RAM significativa: se limita a 512MB en desarrollo
  (`ES_JAVA_OPTS=-Xms512m -Xmx512m`).
 
## Relación con otros sistemas de datos
 
| Sistema | Motor | Propósito |
|---|---|---|
| Entidades | Python `dict` in-memory (ver ADR 0004) | Usuarios, alertas, fuentes, roles |
| Noticias / búsqueda | Elasticsearch 8.12 (este ADR) | Indexación y búsqueda de texto completo |
 
## Índices previstos
 
| Índice | Descripción |
|---|---|
| `newsradar_articles` | Noticias capturadas: título, resumen, url, fuente, fecha, categoría IPTC |
 
## Variables de entorno requeridas
 
```
ELASTICSEARCH_URL=http://localhost:9200
```
 
