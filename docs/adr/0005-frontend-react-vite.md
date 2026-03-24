# ADR 0005: Elección del framework frontend (React + Vite)

- **Estado:** Aceptado
- **Fecha:** 2026-03-09
- **Autores:** Equipo Frontend (Ignacio Barrero, Ignacio Feijoó)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

El enunciado requiere una capa de visualización con un panel de mando que
incluya nubes de palabras, estadísticas globales, gestión de alertas y fuentes,
notificaciones y gestión de perfil de usuario. Adicionalmente indica como
tecnologías candidatas Angular.js, React.js o similar, con posibilidad de
integrar D3.js para visualizaciones.

Se evaluaron las siguientes opciones:

- **React.js**: librería de componentes, ecosistema muy amplio, gran cantidad
  de librerías de visualización compatibles (Recharts, D3.js, react-wordcloud).
- **Angular**: framework completo con TypeScript por defecto; más estructura,
  mayor curva de aprendizaje inicial.
- **Vue.js**: equilibrio entre React y Angular, pero menor familiaridad en
  el equipo.

## Decisión

Se decide utilizar **React 19** con **Vite** como bundler y servidor de
desarrollo.

## Justificación

- React es la opción más conocida por los miembros del equipo frontend,
  lo que reduce el tiempo de arranque.
- Vite ofrece un servidor de desarrollo con Hot Module Replacement (HMR)
  extremadamente rápido, mejorando la productividad.
- El ecosistema de React incluye librerías directamente aplicables al proyecto:
  `react-wordcloud` o `d3-cloud` para nubes de palabras, `recharts` o `chart.js`
  para estadísticas, `react-i18next` para el soporte ES/EN requerido.
- React está explícitamente mencionado en el enunciado como tecnología candidata.

## Consecuencias

### Positivas

- Componentes reutilizables para las pantallas del panel de mando.
- Integración directa con la API REST del backend mediante `fetch` o `axios`.
- Soporte de internacionalización (ES/EN) mediante `react-i18next`, cubriendo
  el requisito opcional del enunciado (Inspección manual nº 7).
- Ecosistema de librerías de visualización compatible con los requisitos
  del panel de mando.

### Negativas / riesgos

- Sin un gestor de estado global (p.ej. Redux o Zustand) la gestión del
  token JWT y el estado del usuario puede volverse compleja. Se recomienda
  adoptar Context API o Zustand en los primeros sprints de frontend.
- El frontend aún está en fase de plantilla por defecto (Sprint 2). Es
  necesario arrancar las pantallas del proyecto con urgencia.

## Pantallas a desarrollar (referencia enunciado)

| Pantalla | Sprint previsto |
|---|---|
| Login / Registro / Verificación | Sprint 2 |
| Dashboard principal (métricas globales) | Sprint 4.2 |
| Resumen: nubes de palabras por categoría | Sprint 4.2 |
| Gestión de alertas (listado + creación) | Sprint 2–3 |
| Gestión de fuentes y canales RSS | Sprint 2 |
| Buzón de notificaciones | Sprint 3.2 |
| Perfil de usuario | Sprint 2 |
