from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate


async def get_user_by_email(db: AsyncSession, email: str):
    """
    Busca un usuario por su email.
    Devuelve el usuario si existe, o None si el email está libre.
    """
    # Usamos la sintaxis moderna (v2.0) de SQLAlchemy con select()
    result = await db.execute(select(Usuario).filter(Usuario.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UsuarioCreate):
    """
    Recibe los datos validados del Pydantic, encripta la contraseña,
    y guarda el nuevo usuario en PostgreSQL.
    """
    # 1. Hasheamos la contraseña plana que nos llega del esquema
    hashed_password = get_password_hash(user.password)

    # 2. Creamos la instancia del modelo SQLAlchemy.
    # ¡Ojo! Le pasamos password_hash, la contraseña plana muere aquí.
    db_user = Usuario(
        email=user.email,
        password_hash=hashed_password,
        nombre=user.nombre,
        apellidos=user.apellidos,
        organizacion=user.organizacion,
        # Los campos 'rol' (LECTOR) e 'is_verified' (False) se ponen por defecto
    )

    # 3. Guardamos en la base de datos de forma asíncrona
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)  # Refrescamos para obtener el 'id' autogenerado

    return db_user


async def get_all_users(db: AsyncSession):
    """Obtiene la lista completa de usuarios de la base de datos."""
    result = await db.execute(select(Usuario))
    return result.scalars().all()
