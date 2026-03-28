import os
import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db

# --- Variables de entorno ---

SECRET_KEY = os.getenv("SECRET_KEY", "newsradar_secret_key_temporal")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_TOKEN_EXPIRE_HOURS = 24

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", 2525))
MAILTRAP_USER = os.getenv("MAIL_USERNAME", "")
MAILTRAP_PASS = os.getenv("MAIL_PASSWORD", "")

# --- Configuración de bcrypt ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- FUNCIONES DE CONTRASEÑAS ---


def get_password_hash(password: str) -> str:
    """Recibe la contraseña en texto plano y devuelve el hash irrompible."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña plana con el hash de la base de datos."""
    return pwd_context.verify(plain_password, hashed_password)


# --- FUNCIONES DE TOKENS ---


def create_verification_token(email: str) -> str:
    """Genera un JWT con el email del usuario y una caducidad de 24 horas."""
    expire = datetime.now(UTC) + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": email}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un JWT de sesión para el usuario."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- ENVÍO DE EMAIL ---


def send_verification_email(to_email: str, token: str):
    """Envía el correo de verificación usando el SMTP de Mailtrap."""
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception from None
    except JWTError:
        raise credentials_exception from None

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception from None

    return user


def require_role(required_role: str):
    """Fábrica de dependencias que verifica si el usuario tiene el rol especificado."""

    def role_checker(current_user: models.User = Depends(get_current_user)):
        user_roles = [role.name for role in current_user.roles]
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción",
            )
        return current_user

    return role_checker


get_current_admin = require_role("Admin")
get_current_manager = require_role("Gestor")
