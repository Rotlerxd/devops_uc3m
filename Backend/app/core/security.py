import os
from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

# 1. Variables de entorno (¡En producción esto va en un archivo .env que no se sube a GitHub!)
# TODO Esta es la llave maestra que firma los tokens. Si alguien la roba, puede falsificar sesiones.
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_para_desarrollo_newsradar")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # El token caducará en media hora por seguridad

# 2. Configuración del motor de encriptación (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- FUNCIONES DE CONTRASEÑAS ---


def get_password_hash(password: str) -> str:
    """Recibe la contraseña en texto plano y devuelve el hash irrompible."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña plana que llega del login con el hash de la base de datos."""
    return pwd_context.verify(plain_password, hashed_password)


# --- FUNCIONES DE TOKENS JWT ---


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un token firmado criptográficamente con los datos del usuario."""
    to_encode = data.copy()

    # Configuramos cuándo caduca el token
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Añadimos la fecha de expiración ('exp' es una palabra reservada del estándar JWT)
    to_encode.update({"exp": expire})

    # Firmamos el token con nuestra SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
