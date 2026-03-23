from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.crud.usuario import get_user_by_email
from app.models.usuario import Usuario, RolUsuario

# Le decimos a FastAPI cuál es la URL para conseguir el token (para que Swagger funcione bien)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Usuario:
    """Valida el token JWT y devuelve el usuario de la base de datos."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Intentamos descifrar el token con nuestra llave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        # Si el token es falso, ha sido modificado o ha caducado, salta este error
        raise credentials_exception
        
    # Si el token es válido, buscamos al usuario en la base de datos
    user = await get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_gestor(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependencia extra: Comprueba si el usuario validado tiene el rol de GESTOR."""
    if current_user.rol != RolUsuario.GESTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes (Se requiere rol GESTOR)"
        )
    return current_user