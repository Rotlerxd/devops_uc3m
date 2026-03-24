# ADR 0002: Estrategia de autenticación y autorización (JWT)

- **Estado:** Aceptado
- **Fecha:** 2026-03-16
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** —
- **Reemplazado por:** —

---

## Contexto

El sistema necesita gestionar el acceso de usuarios con distintos roles
(`GESTOR` y `LECTOR`), tal como exige el enunciado. Era necesario decidir cómo
mantener la sesión de los usuarios entre peticiones. Las opciones evaluadas
fueron:

- **Sesiones en servidor (cookies tradicionales):** el servidor almacena el
  estado de sesión en memoria o en base de datos; requiere consultas adicionales
  en cada petición para validar quién es el usuario.
- **JSON Web Tokens (JWT):** tokens firmados y autocontenidos que el cliente
  envía en cada petición; el servidor puede validarlos sin consultar la base
  de datos.

## Decisión

Se decide implementar autenticación basada en **JSON Web Tokens (JWT)**
mediante el estándar `Bearer Token` en la cabecera `Authorization`.

El token incluye en su payload el email del usuario y su rol (`gestor` /
`lector`), lo que permite al middleware de autorización tomar decisiones
sin consultas adicionales a la base de datos.

## Justificación

- El backend es completamente **stateless**: no almacena sesiones en memoria
  ni hace consultas extra a la base de datos para validar identidades.
- El rol del usuario viaja dentro del token, lo que facilita implementar
  el control de acceso basado en roles (RBAC) requerido por el enunciado
  (p.ej. solo el gestor puede crear alertas).
- Es el mecanismo estándar esperado por el API de referencia del enunciado
  (campo `Authorization: Bearer <token>` en Swagger).
- Facilita la escalabilidad futura: cualquier réplica del backend puede
  validar el token sin coordinación entre instancias.

## Consecuencias

### Positivas

- El backend no guarda estado de sesión; cualquier instancia puede validar
  cualquier token.
- Bajo acoplamiento entre el frontend y el backend: el frontend solo necesita
  almacenar el token.
- Control de acceso por rol implementado directamente en el middleware
  (`get_current_gestor`, `get_current_user`).

### Negativas / riesgos

- Una vez emitido un token, **no se puede revocar** hasta que caduque. Para
  mitigar esto se configuran tiempos de expiración controlados.
- Si el `SECRET_KEY` se compromete, todos los tokens en circulación son
  vulnerables. La clave debe gestionarse como secreto de entorno (`.env`),
  nunca en el repositorio.

## Decisiones de implementación

- Librería: `python-jose` para firma y verificación.
- Algoritmo: `HS256`.
- Expiración: configurable mediante variable de entorno
  `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Los tokens de verificación de email usan el mismo mecanismo con un campo
  `type: "email_verification"` para distinguirlos de los tokens de acceso.
