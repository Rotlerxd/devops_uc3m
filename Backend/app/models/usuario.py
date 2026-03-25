import enum

from sqlalchemy import Boolean, Column, Enum, Integer, String

from app.core.database import Base


class RolUsuario(enum.StrEnum):
    GESTOR = "gestor"
    LECTOR = "lector"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    nombre = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    organizacion = Column(String, nullable=True)

    rol = Column(Enum(RolUsuario, native_enum=False, length=50), default=RolUsuario.LECTOR)

    # Campo clave para la tarea de envío de email del Sprint 1
    is_verified = Column(Boolean, default=False)
