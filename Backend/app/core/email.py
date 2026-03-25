import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jose import jwt

from app.core.security import ALGORITHM, SECRET_KEY

# 1. Calculamos la ruta absoluta a la raíz de tu proyecto
# __file__ es app/core/email.py
# .parent.parent.parent nos lleva a Backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# 2. No longer loading .env here — rely on env vars set by the caller


def create_verification_token(email: str) -> str:
    """Genera un token JWT que caduca en 24 horas para verificar el email."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)  # noqa: UP017
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def send_verification_email(email: str, token: str):
    """
    Construye y envía el email de verificación usando la librería estándar smtplib.
    Al no ser 'async def', FastAPI la ejecutará automáticamente en un hilo
    secundario (Threadpool) gracias a BackgroundTasks, sin bloquear la API.
    """
    link = f"http://localhost:8000/api/v1/auth/verify/{token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>¡Bienvenido a NewsRadar!</h2>
        <p>Gracias por registrarte. Para poder empezar a usar tu cuenta, necesitamos que verifiques tu dirección de correo electrónico.</p>
        <p>Por favor, haz clic en el siguiente botón:</p>
        <a href="{link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verificar mi cuenta</a>
        <p><small>Si el botón no funciona, copia y pega este enlace en tu navegador:<br>{link}</small></p>
    </div>
    """

    # 1. Construimos el mensaje
    msg = MIMEMultipart()
    msg["From"] = os.getenv("MAIL_FROM", "noreply@newsradar.com")
    msg["To"] = email
    msg["Subject"] = "Verifica tu cuenta en NewsRadar"
    msg.attach(MIMEText(html, "html"))

    # 2. Nos conectamos al SMTP de Mailtrap y enviamos
    try:
        server = smtplib.SMTP(os.getenv("MAIL_SERVER", "sandbox.smtp.mailtrap.io"), int(os.getenv("MAIL_PORT", 2525)))
        server.login(os.getenv("MAIL_USERNAME", ""), os.getenv("MAIL_PASSWORD", ""))
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Error interno enviando el correo: {e}")
