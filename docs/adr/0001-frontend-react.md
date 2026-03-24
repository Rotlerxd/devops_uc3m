# ADR 1: Elección del Framework Frontend (React + Vite)

**Estado:** Aceptado  
**Contexto:** Para desarrollar la interfaz de usuario de NewsRadar en el Sprint 0, necesitábamos una tecnología moderna, rápida para el desarrollo y con un amplio ecosistema de librerías.  

**Decisión:** Se decide utilizar **React** como librería principal para construir la interfaz, inicializando el proyecto con **Vite** (en lugar del antiguo Create React App).  

**Consecuencias:** * **Positivas:** Tiempos de arranque del servidor y recarga (HMR) ultrarrápidos gracias a Vite. El ecosistema gigante de React nos permite encontrar componentes fácilmente.  
* **Negativas/Riesgos:** Requiere que el equipo se familiarice con la sintaxis de JSX y el manejo de estados (`useState`, `useEffect`).