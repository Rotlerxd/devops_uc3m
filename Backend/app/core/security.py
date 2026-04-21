"""Utilidades de seguridad para hashing, JWT y envío de emails de verificación."""

import os
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from fastapi.security import HTTPBearer
from jose import jwt
from passlib.context import CryptContext

# --- Variables de entorno ---

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_TOKEN_EXPIRE_HOURS = 24

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST")
MAILTRAP_PORT = int(os.getenv("MAIL_PORT", 2525))
MAILTRAP_USER = os.getenv("MAIL_USERNAME")
MAILTRAP_PASS = os.getenv("MAIL_PASSWORD")

GMAIL_HOST = os.getenv("GMAIL_HOST")
GMAIL_PORT = int(os.getenv("GMAIL_PORT", 587))
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

# bhpj ehrl napj pzgj


# --- Configuración de bcrypt ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- FUNCIONES DE CONTRASEÑAS ---


def get_password_hash(password: str) -> str:
    """Devuelve el hash seguro de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba si una contraseña en claro coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- FUNCIONES DE TOKENS ---


def create_verification_token(email: str) -> str:
    """Genera un JWT de verificación de email con validez limitada."""
    expire = datetime.now(UTC) + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": email}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un token JWT de acceso para autenticación de sesión."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- ENVÍO DE EMAIL ---


def send_verification_email(to_email: str, token: str):
    """Envía el correo de verificación de cuenta vía SMTP."""
    load_dotenv(dotenv_path=env_path)

    msg = MIMEMultipart()
    msg["Subject"] = "NEWSRADAR - Verifica tu cuenta"
    msg["From"] = GMAIL_USER
    msg["To"] = to_email

    verification_link = f"http://localhost:8000/api/v1/auth/verify?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>¡Bienvenido a NewsRadar!</h2>
        <p>Gracias por registrarte. Para poder empezar a usar tu cuenta,
        necesitamos que verifiques tu dirección de correo electrónico.</p>
        <p>Por favor, haz clic en el siguiente botón:</p>
        <a href="{verification_link}"
           style="background-color: #4CAF50; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
           Verificar mi cuenta
        </a>
        <p><small>Si el botón no funciona, copia y pega este enlace en tu navegador:
        <br>{verification_link}</small></p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    try:
        # with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        #     server.ehlo()
        #     server.starttls()
        #     server.login(MAILTRAP_USER, MAILTRAP_PASS)
        #     server.send_message(msg)
        #     print(f"Correo de verificación enviado a Mailtrap{to_email}")
        with smtplib.SMTP(GMAIL_HOST, GMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
            print(f"Correo de verificación enviado a {to_email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


def send_alert_email(to_email: str, alert_name: str, news_data):
    """
    Envía el correo de alerta de noticias siguiendo el formato estricto del Sprint 3.2.
    """
    load_dotenv(dotenv_path=env_path)

    msg = MIMEMultipart()
    # 1. ASUNTO ESTRICTO: “Actualización de <alerta> en <día/hora>”
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg["Subject"] = f"Actualización de {alert_name} en {now_str}"
    msg["From"] = GMAIL_USER
    msg["To"] = to_email

    # 2. CUERPO HTML (Siguiendo tu estilo pero con los datos requeridos)
    html_items = ""
    for n in news_data:
        html_items += f"""
        <div style="border-bottom: 1px solid #ddd; padding: 10px 0;">
            <p><strong>{n.get("title", "Sin título")}</strong></p>
            <p><small>{n.get("published", "N/A")} | <a href="{n.get("link")}">Ver noticia</a></small></p>
        </div>
        """
    html = f"""
    <html>
        <body>
            <h2>Actualización para tu alerta: {alert_name}</h2>
            <p>Hemos encontrado {len(news_data)} noticias nuevas:</p>
            {html_items}
        </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        # Envío a Mailtrap (Desarrollo)
        # with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        #     server.ehlo()
        #     server.starttls()
        #     server.login(MAILTRAP_USER, MAILTRAP_PASS)
        #     server.send_message(msg)
        #     print(f"[MAILTRAP] Alerta '{alert_name}' enviada a {to_email}")

        # Envío a Gmail (Producción)
        with smtplib.SMTP(GMAIL_HOST, GMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
            print(f"[GMAIL] Alerta '{alert_name}' enviada a {to_email}")

    except Exception as e:
        print(f"Error al enviar el correo de alerta: {e}")


# --- DEPENDENCIAS DE AUTENTICACIÓN ---

_bearer_scheme = HTTPBearer()
