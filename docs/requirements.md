# Especificación de requisitos — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-24
- **Autores:** Equipo NEWSRADAR (UC3M — Desarrollo y Operación de Sistemas Software)
- **Fuente:** Enunciado oficial del proyecto (versión 1.0, 3 de marzo de 2026)

---

## 1. Introducción

Este documento recoge los requisitos funcionales y no funcionales del sistema
NEWSRADAR, trazados directamente contra el enunciado oficial y organizados
por módulo funcional. Cada requisito incluye su identificador, descripción,
criterio de verificación y sprint de implementación previsto.

---

## 2. Requisitos funcionales

### RF-01 — Gestión de alertas

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-01.1 | El sistema permite crear alertas con un nombre y una palabra clave | La alerta se persiste en BD y se devuelve en `GET /api/v1/alerts` | S2 |
| RF-01.2 | Al crear una alerta, el sistema recomienda entre 3 y 10 sinónimos o palabras relacionadas | La respuesta de creación incluye lista de descriptores sugeridos | S2 |
| RF-01.3 | El usuario acepta o rechaza los sinónimos recomendados | El endpoint de creación acepta la lista final de descriptores | S2 |
| RF-01.4 | Una alerta pertenece a exactamente una categoría IPTC Media Topics de primer nivel | El campo `categoria_iptc` solo acepta valores del primer nivel IPTC | S2 |
| RF-01.5 | El gestor puede seleccionar las fuentes RSS de la alerta (por defecto: todas las de su categoría) | El campo `fuentes` de la alerta es configurable | S2 |
| RF-01.6 | La alerta se monitoriza de forma continua mediante una expresión cron | El scheduler ejecuta la búsqueda según `expresion_cron` | S3.1 |
| RF-01.7 | Un gestor puede gestionar un máximo de 20 alertas activas | El sistema devuelve `409 Conflict` al superar el límite | S2 |
| RF-01.8 | El gestor puede editar y eliminar sus alertas | `PUT /api/v1/alerts/{id}` y `DELETE /api/v1/alerts/{id}` funcionan correctamente | S2 |

---

### RF-02 — Clasificación de información

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-02.1 | Las noticias capturadas se clasifican según una categoría IPTC Media Topics de primer nivel | El campo `categoria_iptc` del documento indexado es un valor válido IPTC | S3.2 |
| RF-02.2 | La categoría se obtiene de la alerta o, en su defecto, de la fuente RSS | La lógica prioriza la categoría de la alerta sobre la de la fuente | S3.2 |
| RF-02.3 | Solo se pueden crear categorías pertenecientes a IPTC Media Topics de primer nivel | Inspección manual nº 1 del Anexo I del enunciado | S2 |

**Categorías IPTC de primer nivel aceptadas:**
`arts, culture, entertainment` · `crime, law, justice` · `disaster, accident, emergency` ·
`economy, business, finance` · `education` · `environment` · `health` ·
`human interest` · `labour` · `lifestyle, leisure` · `politics` · `religion, belief` ·
`science, technology` · `society` · `sport` · `conflict, war, peace` · `weather`

---

### RF-03 — Gestión de notificaciones

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-03.1 | Cuando se detecta una noticia que activa una alerta, se genera una notificación | La notificación aparece en el buzón del usuario | S3.2 |
| RF-03.2 | La notificación se envía al buzón interno de la aplicación | `GET /api/v1/notifications` devuelve la notificación | S3.2 |
| RF-03.3 | La notificación se envía también por email al usuario | El email llega al servidor SMTP configurado | S3.2 |
| RF-03.4 | El asunto del email es: `"Actualización de <alerta> en <día/hora>"` | Inspección manual nº 4 del Anexo I del enunciado | S3.2 |
| RF-03.5 | El contenido del email incluye: origen, fecha, título y resumen de la noticia | El cuerpo del email contiene todos los campos requeridos | S3.2 |

---

### RF-04 — Gestión de fuentes RSS

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-04.1 | El gestor puede añadir fuentes RSS con nombre, URL y categoría IPTC | `POST /api/v1/sources` crea la fuente correctamente | S2 |
| RF-04.2 | El sistema incluye un mínimo inicial de 100 canales RSS preconfigurados | `GET /api/v1/sources` devuelve ≥ 100 registros tras la inicialización | S2 |
| RF-04.3 | Los 100 canales pertenecen a al menos 10 medios de comunicación distintos | Los registros tienen al menos 10 valores distintos en el campo `medio` | S2 |
| RF-04.4 | Se cubre al menos 1 canal RSS por cada categoría IPTC de primer nivel | Existe al menos 1 fuente por cada categoría IPTC en la base de datos | S2 |
| RF-04.5 | El gestor puede editar y eliminar fuentes | `PUT` y `DELETE` sobre `/api/v1/sources/{id}` funcionan correctamente | S2 |

**Ejemplos de fuentes RSS a incorporar:**
- https://www.rtve.es/rss/
- https://elpais.com/info/rss/
- https://www.abc.es/rss/
- https://www.elconfidencial.com/rss/
- https://www.marca.com/rss.html
- https://www.antena3.com/rss/
- https://www.lamoncloa.gob.es/paginas/varios/rss.aspx

---

### RF-05 — Gestión de usuarios

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-05.1 | El sistema soporta dos roles: `GESTOR` y `LECTOR` | Los endpoints protegidos devuelven `403` si el rol no tiene acceso | S1 ✅ |
| RF-05.2 | El usuario se identifica por email, nombre, apellidos y organización | El modelo `Usuario` incluye todos estos campos | S1 ✅ |
| RF-05.3 | Al registrarse, el sistema envía un email de verificación con caducidad de 24h | Inspección manual nº 2; el token JWT de verificación expira en 24h | S1 ✅ |
| RF-05.4 | Existe un usuario administrador inicial capaz de asignar roles | El script `create_superuser.py` crea el usuario gestor inicial | S1 ✅ |
| RF-05.5 | El lector no puede gestionar alertas | Inspección manual nº 3; los endpoints de alertas requieren rol GESTOR | S1 ✅ |
| RF-05.6 | El usuario puede editar sus datos personales | `PUT /api/v1/users/{id}` permite actualizar nombre, apellidos, organización | S2 |
| RF-05.7 | El usuario puede recuperar su contraseña | Endpoint de recuperación de contraseña por email | S2 |

---

### RF-06 — Panel de mando y visualización

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-06.1 | El panel muestra nubes de palabras por categoría IPTC | Inspección manual nº 5; la nube se renderiza en la pantalla de Resumen | S4.2 |
| RF-06.2 | El panel muestra estadísticas globales: nº fuentes, noticias, alertas y desglose por categoría | Inspección manual nº 6; todos los contadores aparecen en el Dashboard | S4.1 |
| RF-06.3 | El gestor puede crear y gestionar alertas desde la interfaz | Las pantallas de gestión de alertas funcionan correctamente | S2–S3 |
| RF-06.4 | El gestor puede crear y gestionar fuentes RSS desde la interfaz | Las pantallas de gestión de fuentes funcionan correctamente | S2 |
| RF-06.5 | El usuario puede registrarse, hacer login, editar su perfil y recuperar contraseña | Las pantallas de autenticación y perfil funcionan correctamente | S2 |
| RF-06.6 | (Opcional) El panel soporta dos idiomas: ES y EN | Inspección manual nº 7; el selector de idioma cambia los textos de la UI | S4.2 |

---

### RF-07 — API REST

| ID | Requisito | Criterio de verificación | Sprint |
|---|---|---|---|
| RF-07.1 | El sistema expone una API REST documentada con OpenAPI | Swagger UI disponible en `/docs`; especificación en `/openapi.json` | S1 ✅ |
| RF-07.2 | La API implementa todos los endpoints del fichero `newsradar_api.zip` del enunciado | La verificación automática del enunciado pasa sin errores | S4.1 |
| RF-07.3 | Los endpoints están protegidos mediante JWT | Las rutas devuelven `401` sin token válido | S1 ✅ |

---

## 3. Requisitos no funcionales

| ID | Requisito | Mecanismo de verificación |
|---|---|---|
| RNF-01 | El sistema debe desplegarse con un único comando o pipeline | `docker-compose up` levanta todo el stack; verificado en Sprint 6 |
| RNF-02 | Las pruebas unitarias y funcionales deben automatizarse | Pipeline de CI en GitHub Actions ejecuta `pytest` en cada push |
| RNF-03 | El código debe superar las métricas de calidad de SonarQube | El pipeline de CI incluye análisis SonarQube (Sprint 5) |
| RNF-04 | El repositorio debe incluir scripts de construcción, prueba y despliegue | Scripts en `/scripts/`: `build.sh`, `test.sh`, `deploy.sh`, `gen-docs.sh` |
| RNF-05 | La documentación debe versionarse junto al código | Todo en el repositorio Git; generación automática donde sea posible |
| RNF-06 | Los prompts de IA usados en el desarrollo deben tener trazabilidad | Referenciados en la documentación de cada componente generado con IA |

---

## 4. Inspecciones manuales del enunciado (Anexo I)

Estas inspecciones se verifican el día del examen. El sistema debe superarlas todas:

| # | Área | Escenario | Sprint |
|---|---|---|---|
| 1 | Clasificación | Solo se crean categorías IPTC de primer nivel | S2 |
| 2 | Usuarios | Se envía correo de verificación al registrarse | S1 ✅ |
| 3 | Usuarios | El lector no puede gestionar alertas | S1 ✅ |
| 4 | Notificaciones | Se envía email y buzón al detectar una noticia | S3.2 |
| 5 | Interfaz | Nubes de palabras por categoría visibles en el panel | S4.2 |
| 6 | Interfaz | Estadísticas globales visibles en el panel | S4.1 |
| 7 | Interfaz | Selector de idioma ES/EN funcional (opcional) | S4.2 |

---

## 5. Trazabilidad requisitos — componentes

| Requisito | Componente backend | Componente frontend |
|---|---|---|
| RF-01 Alertas | `api/v1/alerts.py`, `models/alerta.py` | Pantalla gestión de alertas |
| RF-02 Clasificación | `scheduler/classifier.py` | — |
| RF-03 Notificaciones | `api/v1/notifications.py`, `core/email.py` | Pantalla buzón |
| RF-04 Fuentes RSS | `api/v1/sources.py`, `models/fuente.py` | Pantalla fuentes y RSS |
| RF-05 Usuarios | `api/v1/auth.py`, `api/v1/users.py` | Pantallas login/registro/perfil |
| RF-06 Panel de mando | `api/v1/stats.py` (Sprint 4) | Dashboard, resumen, nubes |
| RF-07 API REST | `main.py` + todos los routers | — |

---

## 6. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-03-24 | Versión inicial completa basada en enunciado v1.0 |
