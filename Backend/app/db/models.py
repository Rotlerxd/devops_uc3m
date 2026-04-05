from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base

# Tabla intermedia para la relación N:M entre Usuarios y Roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id")),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)
    hashed_password = Column(String, nullable=False)  # Nunca guardamos la contraseña en plano
    is_verified = Column(Boolean, default=False)  # Clave para la verificación por email con Mailtrap
    roles = relationship("Role", secondary=user_roles)

    @property
    def role_ids(self):
        """Extrae automáticamente los IDs de los roles para que Pydantic los lea"""
        return [role.id for role in self.roles]

    
class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    channels = relationship("RssChannel", back_populates="source", cascade="all, delete-orphan")

class RssChannel(Base):
    __tablename__ = "rss_channels"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    name = Column(String(150), nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False) # Para mapear luego con IPTC
    
    source = relationship("Source", back_populates="channels")
    
    
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # Palabra clave principal
    cron_expression = Column(String(50), nullable=False)
    descriptors = Column(JSON, nullable=False)  # Lista de 3 a 10 sinónimos
    categories = Column(JSON, nullable=False) # Lista de categorías IPTC
    owner = relationship("User", backref="alerts")
