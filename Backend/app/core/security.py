import os
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from app.db.database import get_db
from app.db import models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
# Cargar variables de entorno desde el archivo .env
load_dotenv(find_dotenv())

SECRET_KEY = os.getenv("SECRET_KEY", "newsradar_secret_key_temporal")
ALGORITHM = "HS256"
VERIFICATION_TOKEN_EXPIRE_HOURS = 24

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", 2525))
MAILTRAP_USER = os.getenv("MAIL_USERNAME")
MAILTRAP_PASS = os.getenv("MAIL_PASSWORD")

def create_verification_token(email: str) -> str:
    """Genera un JWT con el email del usuario y una caducidad de 24 horas."""
    expire = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": email}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def send_verification_email(to_email: str, token: str):
    """Envía el correo de verificación usando el SMTP de Mailtrap."""
    print(f"DEBUG - Intentando conectar a {MAILTRAP_HOST}:{MAILTRAP_PORT}")
    print(f"DEBUG - Usuario Mailtrap: {MAILTRAP_USER}")
    
    msg = MIMEMultipart()
    msg['Subject'] = "NEWSRADAR - Verifica tu cuenta"
    msg['From'] = "noreply@newsradar.com"
    msg['To'] = to_email

    # Enlace hacia nuestro futuro endpoint de verificación
    verification_link = f"http://localhost:8000/api/v1/auth/verify?token={token}"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>¡Bienvenido a NewsRadar!</h2>
        <p>Gracias por registrarte. Para poder empezar a usar tu cuenta, necesitamos que verifiques tu dirección de correo electrónico.</p>
        <p>Por favor, haz clic en el siguiente botón:</p>
        <a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verificar mi cuenta</a>
        <p><small>Si el botón no funciona, copia y pega este enlace en tu navegador:<br>{verification_link}</small></p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
            server.ehlo()
            server.starttls()
            
            server.login(MAILTRAP_USER, MAILTRAP_PASS)
            server.send_message(msg)
            print(f"Correo de verificación enviado a {to_email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
    
    
    
# Añade esto en app/core/security.py

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """Genera el JWT de sesión para el usuario."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
    
    

security = HTTPBearer()
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    # El token ahora se extrae así:
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            os.getenv("SECRET_KEY", "tu_clave_secreta"), 
            algorithms=["HS256"]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Buscamos al usuario en la base de datos
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user

def require_role(required_role: str):
    """
    Fábrica de dependencias. Devuelve una función que verifica 
    si el usuario actual tiene el rol especificado.
    """
    def role_checker(current_user: models.User = Depends(get_current_user)):
        # Extraemos los nombres de los roles que tiene el usuario
        user_roles = [role.name for role in current_user.roles]
        
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción"
            )
        return current_user
    
    return role_checker

# Creamos atajos limpios para usarlos directamente en los endpoints
get_current_admin = require_role("Admin")
get_current_manager = require_role("Gestor")