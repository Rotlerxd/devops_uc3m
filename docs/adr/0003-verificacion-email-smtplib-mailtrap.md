# ADR 0003: Sistema de verificación por email (smtplib + Mailtrap)

- **Estado:** Aceptado
- **Fecha:** 2026-03-16
- **Autores:** Equipo Backend (Alberto Nuñez, Francisco Ruiz)
- **Reemplaza a:** ADR inicial que proponía `fastapi-mail`
- **Reemplazado por:** —

---

## Contexto

El enunciado exige que al darse de alta un nuevo usuario, el sistema envíe un
correo de verificación con una caducidad de 24 horas (Inspección manual nº 2
del Anexo I).

La primera propuesta fue usar la librería `fastapi-mail`, que ofrece una API
de alto nivel integrada con FastAPI. Sin embargo, durante la implementación
presentó un fallo crítico de incompatibilidad:

```
NameError: name 'SecretStr' is not defined
```

Este error se produce por una incompatibilidad entre `fastapi-mail` y la versión
actual de **Pydantic V2**, que ya está adoptada en el proyecto (ver ADR 0001).
Adicionalmente, el uso de cuentas de Gmail reales en desarrollo supone un riesgo
de bloqueo por envío masivo de pruebas.

## Decisión

Se decide:

1. **Sustituir `fastapi-mail`** por la librería estándar de Python (`smtplib` +
   `email.mime`), eliminando la dependencia externa problemática.
2. **Procesar el envío de forma asíncrona** mediante `BackgroundTasks` de
   FastAPI, para que el registro de usuario responda inmediatamente sin esperar
   al servidor SMTP.
3. **Usar Mailtrap** como servidor SMTP en el entorno de desarrollo, garantizando
   que los correos de prueba no lleguen a bandejas reales.

## Justificación

- Eliminar `fastapi-mail` reduce la deuda técnica y las dependencias externas
  inestables.
- `smtplib` es parte de la biblioteca estándar de Python: no requiere instalación,
  no tiene problemas de compatibilidad y es suficiente para el caso de uso.
- `BackgroundTasks` garantiza que el endpoint `/register` responde con
  `201 Created` inmediatamente, sin que el tiempo de respuesta del SMTP afecte
  a la experiencia del usuario.
- Mailtrap intercepta todos los correos enviados en desarrollo, permitiendo
  verificar el contenido del email sin riesgo de spam.

## Consecuencias

### Positivas

- Sin dependencias de terceros para envío de email: menos riesgo de roturas
  por actualizaciones externas.
- El envío de correos no bloquea la respuesta de la API (no-blocking I/O via
  `BackgroundTasks`).
- Entorno de desarrollo limpio: los correos de prueba no llegan a usuarios reales.
- El token de verificación usa JWT (mismo mecanismo que ADR 0002), con campo
  `type: "email_verification"` y expiración de 24 horas.

### Negativas / riesgos

- La construcción del mensaje MIME es ligeramente más manual que con una
  librería empaquetada.
- En producción se deberá configurar un servidor SMTP real (p.ej. SendGrid,
  Amazon SES) mediante variables de entorno. Este cambio no requiere modificar
  el código, solo la configuración.

## Variables de entorno requeridas

```
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=<usuario_mailtrap>
MAIL_PASSWORD=<contraseña_mailtrap>
MAIL_FROM=noreply@newsradar.local
```
