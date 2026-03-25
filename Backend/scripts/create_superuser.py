import asyncio
import os
import sys

# Esto permite a Python encontrar el módulo 'app' ejecutando el script desde la raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select

# Ajusta el import de tu sesión según cómo la llamaras en database.py
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.usuario import RolUsuario, Usuario


async def create_superuser():
    print("--- Creación de Administrador (GESTOR) ---")
    email = input("Email: ")
    password = input("Contraseña: ")
    nombre = input("Nombre: ")
    apellidos = input("Apellidos: ")

    async with AsyncSessionLocal() as db:
        # 1. Comprobar si ya existe
        result = await db.execute(select(Usuario).filter(Usuario.email == email))
        if result.scalars().first():
            print("Error: Ya existe un usuario con ese email.")
            return

        # 2. Insertar forzando el rol a GESTOR
        hashed_pw = get_password_hash(password)
        super_user = Usuario(
            email=email,
            password_hash=hashed_pw,
            nombre=nombre,
            apellidos=apellidos,
            rol=RolUsuario.GESTOR,
            is_verified=True,  # Al ser admin, lo damos por verificado
        )

        db.add(super_user)
        await db.commit()
        print(f"¡Superusuario '{email}' creado con éxito con rol GESTOR!")


if __name__ == "__main__":
    asyncio.run(create_superuser())
