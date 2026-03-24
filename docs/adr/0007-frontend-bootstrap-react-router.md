# ADR 0007: Biblioteca de estilos y enrutamiento frontend (Bootstrap & React Router)

- **Estado:** Aceptado
- **Fecha:** 2026-03-24
- **Autores:** Equipo Frontend (Ignacio Barrero, Ignacio Feijoó)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

El frontend de NEWSRADAR requiere una interfaz profesional y navegación fluida
entre las distintas pantallas de la aplicación (login, registro, dashboard,
alertas, fuentes, notificaciones, perfil) sin recargas de página completa,
siguiendo el patrón de Single Page Application (SPA).

Era necesario decidir:

1. **Biblioteca de estilos y componentes UI**: construir los componentes desde
   cero con CSS puro o apoyarse en un framework de estilos que acelere el
   desarrollo.
2. **Enrutamiento en el cliente**: gestionar la navegación entre vistas sin
   que el servidor sirva una página nueva en cada cambio de ruta.

Las alternativas evaluadas fueron:

- **Estilos**: Bootstrap 5, Tailwind CSS, Material UI.
- **Enrutamiento**: React Router Dom, TanStack Router, Next.js (con SSR).

## Decisión

Se decide utilizar **Bootstrap 5** para los estilos y componentes UI, y
**React Router Dom v6** para el enrutamiento del cliente.

## Justificación

### Bootstrap 5

- Proporciona componentes pre-diseñados (formularios, tablas, modales, navbar,
  cards) que cubren directamente las pantallas descritas en el Anexo II del
  enunciado, acelerando el desarrollo en los sprints de frontend.
- El equipo frontend tiene familiaridad previa con Bootstrap, reduciendo
  la curva de aprendizaje.
- No requiere paso de compilación adicional: se puede importar via CDN o npm
  sin configuración de PostCSS (a diferencia de Tailwind).
- Compatible directamente con React mediante `react-bootstrap` o mediante
  clases CSS estándar.

### React Router Dom v6

- Es la solución de enrutamiento estándar y más adoptada para aplicaciones
  React SPA.
- La v6 introduce una API más limpia basada en componentes (`<Routes>`,
  `<Route>`, `<Outlet>`) que facilita la implementación de rutas protegidas
  por rol (Gestor / Lector), necesarias según RF-05.2 y RF-05.3.
- Permite navegación programática (`useNavigate`) para redirigir al usuario
  tras el login o verificación de email sin recargar la página.

## Consecuencias

### Positivas

- Maquetación rápida de las pantallas del enunciado con componentes
  pre-diseñados de Bootstrap.
- Experiencia de usuario fluida: navegación entre vistas sin recargas
  de página (SPA).
- Rutas protegidas por rol implementables mediante componentes wrapper
  (`<ProtectedRoute role="gestor">`).
- Compatible con el resto del stack: Vite gestiona el bundling sin
  configuración adicional para ninguna de las dos librerías.

### Negativas / riesgos

- Bootstrap añade una carga de CSS extra (~30KB minificado + gzip) que
  no siempre se utiliza al completo. En sprints posteriores se puede
  valorar el tree-shaking con PurgeCSS si el rendimiento lo requiere.
- La configuración de React Router requiere que el servidor de producción
  redirija todas las rutas al `index.html` para que el enrutamiento del
  cliente funcione correctamente (`try_files` en nginx o equivalente).

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR 0005 (React + Vite) | Este ADR extiende la decisión de frontend con las librerías de UI y navegación |
| ADR 0002 (JWT) | React Router gestiona la redirección tras login y protege rutas según el token JWT |
