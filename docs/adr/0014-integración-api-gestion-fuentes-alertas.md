# ADR 0006: Integración con API REST para Gestión de Fuentes y Alertas

- **Estado:** Aceptado
- **Fecha:** 2026-04-18
- **Autores:** Equipo Frontend (Ignacio Barrero, Ignacio Feijoó)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

Tras definir el framework en el ADR 0005, el Sprint 2 requiere implementar la lógica de negocio para la gestión de fuentes (medios de comunicación), canales RSS y alertas personalizadas. El sistema debe interactuar con un backend que protege sus endpoints mediante JWT y organiza la información por usuario.

Se requería una solución para:
1.  Consumir los endpoints de la API de forma centralizada.
2.  Gestionar el estado de la UI (modales y tablas) tras operaciones CRUD.
3.  Vincular canales RSS a categorías IPTC y fuentes existentes.

## Decisión

Se ha decidido implementar una **Capa de Servicios de API** independiente de los componentes de React, utilizando la API nativa `fetch` y almacenando las credenciales (token e ID de usuario) en `localStorage`.

## Justificación

- **Desacoplamiento:** Separar la lógica de red en `sourcesService.js` y `alertsService.js` permite que los componentes de React (`SourcesPage`, `AlertsPage`) se ocupen solo de la visualización, facilitando el mantenimiento.
- **Persistencia Simple:** El uso de `localStorage` permite recuperar el token en cada petición sin obligar al usuario a loguearse tras refrescar la página, cumpliendo el requisito de usabilidad.
- **Interoperabilidad:** La estructura de los servicios permite transformar los datos del backend (que entrega canales por fuente) en estructuras planas fáciles de renderizar en tablas de Bootstrap.

## Consecuencias

### Positivas
- **Modularidad:** Si el backend cambia la URL de un endpoint, solo se modifica el archivo de servicio correspondiente.
- **UX Consistente:** El uso de estados (`useState`) para manejar errores de la API permite mostrar mensajes claros al usuario mediante alertas de Bootstrap en lugar de fallos silenciosos.
- **Escalabilidad:** Esta arquitectura deja el terreno preparado para el Sprint 3, donde el motor de captura empezará a generar datos que el frontend deberá consultar.

### Negativas / riesgos
- **Seguridad:** El almacenamiento del JWT en `localStorage` es vulnerable a ataques XSS. Se mitiga mediante la validación estricta de entradas, pero deberá revisarse si se manejan datos extremadamente sensibles en el futuro.
- **Sincronización:** Al no usar una librería de gestión de estado global (como Redux), la actualización de la UI depende de rellamadas manuales a la API tras cada creación/borrado.

## Requisitos de Sprint 2 Cubiertos

| Funcionalidad | Implementación |
|---|---|
| CRUD de Fuentes | Tabla con alta y baja de medios de comunicación. |
| Gestión RSS | Vinculación de canales a medios y categorías IPTC. |
| Gestión de Alertas | Creación de alertas con descriptores (3-10) y categorías. |
| Autenticación | Uso de Bearer Token en cabeceras para todas las peticiones. |