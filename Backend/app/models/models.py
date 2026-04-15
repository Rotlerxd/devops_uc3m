from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, Float
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm import relationship
from app.db.database import Base

# Tabla de asociación Muchos-a-Muchos para Usuarios y Roles
user_role_table = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)
    password = Column(String(128), nullable=False)
    is_verified = Column(Boolean, default=False)
    
    roles = relationship("Role", secondary=user_role_table)
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    cron_expression = Column(String(120), nullable=False)
    
    # Arrays y JSON para adaptarnos a los Pydantic actuales sin crear tablas extra innecesarias
    descriptors = Column(ARRAY(String), default=list)
    categories = Column(JSON, default=list) # Guarda list[AlertCategoryItem]

    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(String, nullable=False) # Guardamos ISO format
    metrics = Column(JSON, default=list) # Guarda list[Metric]
    iptc_category = Column(String, nullable=False)

    alert = relationship("Alert", back_populates="notifications")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    source = Column(String, default="IPTC")

    channels = relationship("RSSChannel", back_populates="category")

class InformationSource(Base):
    __tablename__ = "information_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    url = Column(String, nullable=False)

    channels = relationship("RSSChannel", back_populates="source", cascade="all, delete-orphan")

class RSSChannel(Base):
    __tablename__ = "rss_channels"
    id = Column(Integer, primary_key=True, index=True)
    information_source_id = Column(Integer, ForeignKey("information_sources.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    url = Column(String, nullable=False)

    source = relationship("InformationSource", back_populates="channels")
    category = relationship("Category", back_populates="channels")

class Stats(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True, index=True)
    total_news = Column(Integer, default=0)
    total_notifications = Column(Integer, default=0)
    metrics = Column(JSON, default=list)