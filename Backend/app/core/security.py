"""Utilidades de seguridad para hashing, JWT y envío de emails de verificación."""

import os
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from fastapi.security import HTTPBearer
from jose import jwt
from passlib.context import CryptContext

# --- Variables de entorno ---

SECRET_KEY = os.getenv("SECRET_KEY", "newsradar_secret_key_temporal")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_TOKEN_EXPIRE_HOURS = 24

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
MAILTRAP_PORT = int(os.getenv("MAIL_PORT", 2525))
MAILTRAP_USER = os.getenv("MAIL_USERNAME", "f7aab98648814d")
MAILTRAP_PASS = os.getenv("MAIL_PASSWORD", "b34ae07bf8e257")

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
    load_dotenv()

    msg = MIMEMultipart()
    msg["Subject"] = "NEWSRADAR - Verifica tu cuenta"
    msg["From"] = "noreply@newsradar.com"
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
        print(f"DEBUG - Host: {MAILTRAP_HOST}")
        print(f"DEBUG - User: {MAILTRAP_USER}")
        with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(MAILTRAP_USER, MAILTRAP_PASS)
            server.send_message(msg)
            print(f"Correo de verificación enviado a {to_email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


# --- DEPENDENCIAS DE AUTENTICACIÓN ---

_bearer_scheme = HTTPBearer()
