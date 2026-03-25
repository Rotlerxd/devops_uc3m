from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.usuario import RolUsuario  # Importamos el Enum que creamos en el modelo


# 1. Propiedades compartidas (Lo que siempre pedimos/mostramos)
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellidos: str
    organizacion: str | None = None


# 2. Esquema para CREAR un usuario (Petición POST desde el Frontend)
class UsuarioCreate(UsuarioBase):
    password: str


# 3. Esquema para DEVOLVER el usuario (Respuesta de la API)
class UsuarioResponse(UsuarioBase):
    id: int
    rol: RolUsuario
    is_verified: bool

    # IMPORTANTE: No incluimos el campo 'password' aquí.

    # Esta configuración permite a Pydantic leer el objeto directamente de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
