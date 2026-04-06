import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.db import models
from app.db.database import SessionLocal


def create_superuser():
    print("--- Creación de Administrador (GESTOR) ---")
    email = input("Email: ")
    password = input("Contraseña: ")
    first_name = input("Nombre: ")
    last_name = input("Apellidos: ")

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            print("Error: Ya existe un usuario con ese email.")
            return

        hashed_pw = get_password_hash(password)
        gestor_role = db.query(models.Role).filter(models.Role.name == "Gestor").first()

        super_user = models.User(
            email=email,
            hashed_password=hashed_pw,
            first_name=first_name,
            last_name=last_name,
            organization="Admin",
            is_verified=True,
        )
        if gestor_role:
            super_user.roles.append(gestor_role)

        db.add(super_user)
        db.commit()
        print(f"¡Superusuario '{email}' creado con éxito con rol GESTOR!")
    finally:
        db.close()


if __name__ == "__main__":
    create_superuser()
