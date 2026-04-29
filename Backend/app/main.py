"""API backend de NewsRadar con PostgreSQL, SQLAlchemy y motor RSS."""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import feedparser
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_verification_token,
    get_password_hash,
    send_alert_email,
    send_verification_email,
    verify_password,
)
from app.core.synonyms import (
    DEFAULT_LANGUAGE,
    DEFAULT_SYNONYM_LIMIT,
    MAX_SYNONYM_LIMIT,
    MIN_SYNONYM_LIMIT,
    SynonymDataNotAvailableError,
    generate_synonyms,
    warmup_synonym_resources,
)
from app.db.database import SessionLocal, get_db
from app.models import models as db_models

ELASTICSEARCH_URL = "http://localhost:9200"
NEWS_INDEX = "newsradar_articles"

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Instanciar el cliente global
es_client = Elasticsearch(ELASTICSEARCH_URL, request_timeout=30, retry_on_timeout=True, max_retries=3)


def check_elastic_connection():
    """Comprueba que Elasticsearch responde durante el arranque."""
    try:
        # .ping() devuelve True si el clúster responde
        if es_client.ping():
            print("[STARTUP] Conexión exitosa a Elasticsearch.")
            # Opcional: imprimir la información del clúster
            info = es_client.info()
            print(f"   Clúster: {info['cluster_name']} | Versión: {info['version']['number']}")
        else:
            print("[STARTUP] No se pudo conectar a Elasticsearch (el ping devolvió False).")
    except Exception as e:
        print(f"[STARTUP] Error crítico al intentar conectar con Elasticsearch: {e}")


def wait_for_elasticsearch_ready(timeout_seconds: int = 60, interval_seconds: int = 2) -> bool:
    """Espera a que Elasticsearch acepte peticiones antes de tocar índices o settings."""
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            if es_client.ping():
                return True
        except Exception as exc:
            last_error = exc

        time.sleep(interval_seconds)

    if last_error is not None:
        print(f"[STARTUP] Elasticsearch no respondió a tiempo: {type(last_error).__name__}: {last_error}")
    else:
        print("[STARTUP] Elasticsearch no respondió a tiempo.")
    return False


def configure_local_elasticsearch() -> None:
    """Relaja restricciones locales para que Elasticsearch sea usable en desarrollo."""
    try:
        if not wait_for_elasticsearch_ready():
            return

        es_client.cluster.put_settings(transient={"cluster.routing.allocation.disk.threshold_enabled": False})

        if not es_client.indices.exists(index=NEWS_INDEX):
            es_client.indices.create(
                index=NEWS_INDEX,
                settings={"index": {"number_of_shards": 1, "number_of_replicas": 0}},
            )
            print(f"[STARTUP] Índice {NEWS_INDEX} creado con replicas=0.")
            return

        es_client.indices.put_settings(
            index=NEWS_INDEX,
            settings={"index": {"number_of_replicas": 0}},
        )
        print(f"[STARTUP] Índice {NEWS_INDEX} ajustado a replicas=0.")
    except Exception as e:
        print(f"[STARTUP] Error ajustando Elasticsearch local: {e}")


def should_configure_local_elasticsearch() -> bool:
    """Habilita ajustes locales de Elasticsearch solo cuando se solicita explícitamente."""
    return os.getenv("NEWSRADAR_CONFIGURE_LOCAL_ELASTICSEARCH", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def normalize_published_at(entry) -> str:
    """Devuelve una fecha ISO-8601 segura para Elasticsearch."""
    published_parsed = entry.get("published_parsed")
    if published_parsed:
        return datetime(*published_parsed[:6], tzinfo=UTC).isoformat()

    return datetime.now(UTC).isoformat()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicializa datos base y arranca servicios auxiliares al levantar la app."""
    create_seed_data()
    if should_configure_local_elasticsearch():
        configure_local_elasticsearch()
    check_elastic_connection()

    motor_thread = threading.Thread(target=rss_fetcher_thread, daemon=True)
    motor_thread.start()

    alert_thread = threading.Thread(target=alert_checker_thread, daemon=True)
    alert_thread.start()

    yield


def rss_fetcher_thread():
    time.sleep(5)
    while True:
        rss_fetcher_engine()
        time.sleep(900)  # 15 minutos


def alert_checker_thread():
    time.sleep(10)  # Desfase para asegurar que haya noticias primero
    while True:
        run_alert_matching()
        time.sleep(900)  # 15 minutos


app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
security = HTTPBearer(auto_error=False)


class Metric(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: float


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)


class Role(RoleBase):
    id: int


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)
    role_ids: list[int] = Field(default_factory=list)
    is_verified: bool = Field(default=False)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=1, max_length=120)
    last_name: str | None = Field(None, min_length=1, max_length=120)
    organization: str | None = Field(None, min_length=1, max_length=180)
    role_ids: list[int] | None = None
    password: str | None = Field(None, min_length=6, max_length=128)


class User(UserBase):
    id: int


class UserInDB(User):
    password: str


class AlertCategoryItem(BaseModel):
    code: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=120)


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    descriptors: list[str] = Field(default_factory=list)
    categories: list[AlertCategoryItem] = Field(default_factory=list)
    rss_channels_ids: list[str] = Field(default_factory=list)
    information_sources_ids: list[str] = Field(default_factory=list)
    cron_expression: str = Field(..., min_length=1, max_length=120)


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    descriptors: list[str] | None = None
    categories: list[AlertCategoryItem] | None = None
    rss_channels_ids: list[str] = Field(default_factory=list)
    information_sources_ids: list[str] = Field(default_factory=list)
    cron_expression: str | None = Field(None, min_length=1, max_length=120)


class Alert(AlertBase):
    id: int
    user_id: int


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(default="IPTC", pattern="^IPTC$")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    source: str | None = Field(None, pattern="^IPTC$")


class Category(CategoryBase):
    id: int


class NotificationBase(BaseModel):
    timestamp: datetime
    metrics: list[Metric] = Field(default_factory=list)
    iptc_category: str  # Agregamos el campo de categoría IPTC para poder mostrarlo en las notificaciones sin necesidad de hacer join con la categoría original. Se llenará al crear la notificación a partir de la alerta y su categoría asociada.


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    timestamp: datetime | None = None
    metrics: list[Metric] | None = None


class Notification(NotificationBase):
    id: int
    alert_id: int


class InformationSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl


class InformationSourceCreate(InformationSourceBase):
    pass


class InformationSourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    url: HttpUrl | None = None


class InformationSource(InformationSourceBase):
    id: int


class RSSChannelBase(BaseModel):
    url: HttpUrl
    category_id: int


class RSSChannelCreate(RSSChannelBase):
    pass


class RSSChannelUpdate(BaseModel):
    url: HttpUrl | None = None
    category_id: int | None = None


class RSSChannel(RSSChannelBase):
    id: int
    information_source_id: int


class StatsBase(BaseModel):
    metrics: list[Metric] = Field(default_factory=list)
    total_news: int


class StatsCreate(StatsBase):
    pass


class StatsUpdate(BaseModel):
    metrics: list[Metric] | None = None


class Stats(StatsBase):
    id: int
    total_news: int = 0
    total_notifications: int = 0


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SynonymResponse(BaseModel):
    term: str
    language: str = DEFAULT_LANGUAGE
    limit: int
    synonyms: list[str] = Field(default_factory=list)


class SynonymWarmupResponse(BaseModel):
    status: str
    detail: str | None = None


def ensure_role_ids_exist(role_ids: list[int], db: Session = Depends(get_db)) -> None:
    """Verifica en PostgreSQL que los IDs de roles proporcionados existen."""
    if not role_ids:
        return

    existing_role_ids = set(db.scalars(select(db_models.Role.id).where(db_models.Role.id.in_(role_ids))))

    # Calculamos cuáles faltan exactamente como hacías en memoria
    missing = [role_id for role_id in role_ids if role_id not in existing_role_ids]

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roles no encontrados: {missing}",
        )


def ensure_user_exists(user_id: int, db: Session = Depends(get_db)) -> None:
    """Lanza 404 si el usuario no existe en la base de datos."""
    if db.get(db_models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


def ensure_alert_for_user(user_id: int, alert_id: int, db: Session = Depends(get_db)):
    """Obtiene una alerta de un usuario o lanza 404 si no corresponde."""
    db_alert = db.scalar(
        select(db_models.Alert).where(db_models.Alert.id == alert_id, db_models.Alert.user_id == user_id)
    )

    if not db_alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada para el usuario")

    return db_alert


def ensure_notification_for_alert(alert_id: int, notification_id: int, db: Session = Depends(get_db)):
    """Obtiene una notificación de una alerta o lanza 404 buscando en PostgreSQL."""
    db_notification = db.scalar(
        select(db_models.Notification).where(
            db_models.Notification.id == notification_id, db_models.Notification.alert_id == alert_id
        )
    )

    if not db_notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada para la alerta")

    return db_notification


def ensure_information_source_exists(source_id: int, db: Session = Depends(get_db)) -> None:
    """Lanza 404 si la fuente de información no existe."""
    if db.get(db_models.InformationSource, source_id) is None:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")


def ensure_category_exists(category_id: int, db: Session = Depends(get_db)) -> None:
    """Lanza 404 si la categoría no existe."""
    if db.get(db_models.Category, category_id) is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


def ensure_rss_for_source(source_id: int, channel_id: int, db: Session = Depends(get_db)) -> RSSChannel:
    """Obtiene un canal RSS de una fuente concreta o lanza 404."""
    db_channel = db.scalar(
        select(db_models.RSSChannel).where(
            db_models.RSSChannel.id == channel_id, db_models.RSSChannel.information_source_id == source_id
        )
    )
    if not db_channel:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")
    return db_channel


def sanitize_user(user_db: db_models.User) -> User:
    """Convierte el modelo SQLAlchemy a tu modelo Pydantic de salida exacto."""
    role_ids = [role.id for role in user_db.roles]

    return User(
        id=user_db.id,
        email=user_db.email,
        first_name=user_db.first_name,
        last_name=user_db.last_name,
        organization=user_db.organization,
        role_ids=role_ids,
        is_verified=user_db.is_verified,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> db_models.User:
    """Autentica el token bearer y devuelve el usuario de PostgreSQL asociado."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token inválido o ausente")

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    email = payload.get("sub")
    if not isinstance(email, str) or not email:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = db.scalar(select(db_models.User).where(db_models.User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inválido")

    return user


def create_seed_data() -> None:
    """Inicializa roles, usuario admin y semilla de fuentes/canales RSS."""
    with SessionLocal() as db:
        try:
            roles_nombres = ["lector", "gestor"]
            for nombre in roles_nombres:
                if db.scalar(select(db_models.Role).where(db_models.Role.name == nombre)) is None:
                    db.add(db_models.Role(name=nombre))
            db.commit()

            admin_email = "admin@newsradar.com"
            if db.scalar(select(db_models.User).where(db_models.User.email == admin_email)) is None:
                gestor_role = db.scalar(select(db_models.Role).where(db_models.Role.name == "gestor"))
                admin_user = db_models.User(
                    email=admin_email,
                    first_name="Admin",
                    last_name="NewsRadar",
                    organization="UC3M",
                    password=get_password_hash("admin123"),
                    is_verified=True,
                    roles=[gestor_role] if gestor_role else [],
                )
                db.add(admin_user)
                db.commit()
                print("[DB] Datos iniciales creados con éxito.")
        except Exception as e:
            db.rollback()
            print(f"[DB] Error en el seeding: {e}")

    # --- 2. CARGA DE FUENTES Y CANALES RSS DESDE EL JSON ---
    base_dir = Path(__file__).resolve().parent
    seed_file = base_dir / "data" / "rss_seed.json"

    if not seed_file.exists():
        print(f"[STARTUP] Archivo JSON no encontrado en: {seed_file}")
        return

    with SessionLocal() as db:
        # Comprobación de seguridad: si ya hay fuentes, no volvemos a inyectar la semilla
        if db.scalar(select(db_models.InformationSource)):
            print("[STARTUP] La base de datos ya contiene datos. Omitiendo la carga del JSON.")
            return

        print("[STARTUP] Base de datos vacía detectada. Cargando semilla de datos...")

        with open(seed_file, encoding="utf-8") as f:
            data = json.load(f)

        for source_data in data:
            # Si el JSON no la tiene, le ponemos una por defecto basada en el nombre.
            fake_url = f"https://www.{source_data['source_name'].lower().replace(' ', '')}.com"
            source_url = source_data.get("url", fake_url)

            # 1. Crear la fuente
            source = db_models.InformationSource(name=source_data["source_name"], url=source_url)
            db.add(source)
            db.flush()  # Genera el source.id en la BD temporalmente sin hacer commit final

            # Recorrer los canales de esta fuente
            for channel_data in source_data.get("channels", []):
                cat_name = channel_data.get("category", "General")

                # 2. Buscar si la categoría ya existe en nuestra base de datos
                category = db.scalar(select(db_models.Category).where(db_models.Category.name == cat_name))

                # Si no existe, la creamos
                if not category:
                    # El esquema pide 'source' por defecto a "IPTC"
                    category = db_models.Category(name=cat_name, source="IPTC")
                    db.add(category)
                    db.flush()  # Genera el category.id

                # 3. Crear el canal vinculándolo a la fuente y a la categoría
                channel = db_models.RSSChannel(
                    information_source_id=source.id, url=channel_data["url"], category_id=category.id
                )
                db.add(channel)

        # Confirmar todos los cambios juntos (transacción segura)
        db.commit()
        print("[STARTUP] Semilla cargada exitosamente en PostgreSQL: Fuentes, Categorías y Canales listos.")


@app.get(f"{API_PREFIX}/health", tags=["system"])
def health() -> dict:
    """Devuelve estado de salud básico del servicio."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@app.post(f"{API_PREFIX}/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica credenciales y emite un JWT de acceso."""
    db_user = db.scalar(select(db_models.User).where(db_models.User.email == payload.email))

    if db_user is None or not verify_password(payload.password, db_user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    roles = [role.name.lower() for role in db_user.roles]
    role = "gestor" if "gestor" in roles else roles[0] if roles else "lector"
    token = create_access_token({"sub": db_user.email, "role": role, "type": "access"})
    return TokenResponse(access_token=token)


@app.post(f"{API_PREFIX}/auth/register", response_model=User, tags=["auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Registra un usuario nuevo y envía email de verificación."""
    if db.scalar(select(db_models.User).where(db_models.User.email == payload.email)):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Validación de roles inyectando la sesión de BD
    ensure_role_ids_exist(payload.role_ids, db)

    db_roles = list(db.scalars(select(db_models.Role).where(db_models.Role.id.in_(payload.role_ids))))

    hashed_pwd = get_password_hash(payload.password)

    new_user = db_models.User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        organization=payload.organization,
        password=hashed_pwd,  # ¡Aquí guardamos el hash seguro!
        is_verified=False,
        roles=db_roles,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, token)

    return sanitize_user(new_user)


@app.get(f"{API_PREFIX}/auth/verify", tags=["auth"])
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verifica un usuario validando el token JWT de verificación."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token de verificación inválido o expirado",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if payload.get("type") != "email_verification" or not isinstance(email, str):
            raise credentials_exception from None
        print(f"[VERIFY] Token decodificado, email: {email}")
    except JWTError as e:
        print(f"[VERIFY] Error decodificando token: {e}")
        raise credentials_exception from None

    db_user = db.scalar(select(db_models.User).where(db_models.User.email == email))

    if db_user is None:
        print(f"[VERIFY] Usuario no encontrado para email: {email}")
        raise credentials_exception from None

    if db_user.is_verified:
        print(f"[VERIFY] Usuario ya verificado: {email}")
        return {"msg": "El usuario ya estaba verificado"}

    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)

    print(f"[VERIFY] Usuario verificado exitosamente: {email}")

    return {"msg": "Cuenta verificada con éxito. Ya puedes iniciar sesión."}


# CRUD USERS


@app.get(f"{API_PREFIX}/users", response_model=list[User], tags=["users"])
def list_users(_: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> list[User]:
    """Lista los usuarios registrados."""
    return [sanitize_user(user) for user in db.scalars(select(db_models.User))]


@app.post(f"{API_PREFIX}/users", response_model=User, status_code=201, tags=["users"])
def create_user(payload: UserCreate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Crea un usuario desde la API protegida."""
    if db.scalar(select(db_models.User).where(db_models.User.email == payload.email)):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    ensure_role_ids_exist(payload.role_ids, db)
    db_roles = list(db.scalars(select(db_models.Role).where(db_models.Role.id.in_(payload.role_ids))))

    hashed_pwd = get_password_hash(payload.password)
    user_data = payload.model_dump(exclude={"role_ids", "password"})
    new_user = db_models.User(**user_data, password=hashed_pwd, roles=db_roles)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return sanitize_user(new_user)


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def get_user(user_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Obtiene un usuario por su identificador."""
    db_user = db.get(db_models.User, user_id)

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return sanitize_user(db_user)


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def update_user(
    user_id: int, payload: UserUpdate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    """Actualiza los campos permitidos de un usuario."""
    db_user = db.get(db_models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = payload.model_dump(exclude_unset=True)

    # Validar email único si se está actualizando
    if "email" in data:
        existing_user = db.scalar(
            select(db_models.User).where(db_models.User.email == data["email"], db_models.User.id != user_id)
        )
        if existing_user:
            raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Validar y actualizar roles si vienen en el payload
    if "role_ids" in data:
        ensure_role_ids_exist(data["role_ids"], db)
        db_roles = list(db.scalars(select(db_models.Role).where(db_models.Role.id.in_(data["role_ids"]))))
        db_user.roles = db_roles
        del data["role_ids"]  # Lo quitamos del dicc para no pisarlo en el bucle de abajo

    # Actualizar dinámicamente el resto de campos permitidos
    for key, value in data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    return sanitize_user(db_user)


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["users"],
)
def delete_user(user_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Elimina un usuario y sus alertas/notificaciones asociadas."""
    db_user = db.get(db_models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # En bases de datos relacionales, al borrar el usuario, el ON DELETE CASCADE
    # configurado en los modelos borra automáticamente sus alertas y notificaciones.
    # Nos ahorramos los bucles `for` que tenías en memoria.
    db.delete(db_user)
    db.commit()


# CRUD ROLES


@app.get(f"{API_PREFIX}/roles", response_model=list[Role], tags=["roles"])
def list_roles(_: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Role]:
    """Lista todos los roles."""
    return list(db.scalars(select(db_models.Role)))


@app.post(f"{API_PREFIX}/roles", response_model=Role, status_code=201, tags=["roles"])
def create_role(payload: RoleCreate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> Role:
    """Crea un rol nuevo."""
    db_role = db_models.Role(**payload.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def get_role(role_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> Role:
    """Obtiene un rol por identificador."""
    db_role = db.get(db_models.Role, role_id)

    if not db_role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    return db_role


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def update_role(
    role_id: int, payload: RoleUpdate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> Role:
    """Actualiza un rol existente."""
    db_role = db.get(db_models.Role, role_id)

    if not db_role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_role, key, value)

    db.commit()
    db.refresh(db_role)
    return db_role


@app.delete(
    f"{API_PREFIX}/roles/{{role_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["roles"],
)
def delete_role(role_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Elimina un rol si no está asignado a usuarios."""
    db_role = db.get(db_models.Role, role_id)

    if not db_role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # [Optimización SQL] Comprobamos si el rol está asignado usando .any() en la relación.
    # Esto le dice a Postgres: "¿Existe algún User tal que en su lista de roles contenga este role_id?"
    user_with_role = db.scalar(select(db_models.User).where(db_models.User.roles.any(id=role_id)))

    if user_with_role:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un rol asignado a usuarios",
        )

    db.delete(db_role)
    db.commit()


# CRUD user alerts


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=list[Alert],
    tags=["alerts"],
)
def list_user_alerts(
    user_id: int, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Alert]:
    """Lista las alertas asociadas a un usuario."""
    ensure_user_exists(user_id, db)

    # En SQLAlchemy podemos filtrar directamente por el user_id
    return list(db.scalars(select(db_models.Alert).where(db_models.Alert.user_id == user_id)))


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=Alert,
    status_code=201,
    tags=["alerts"],
)
def create_user_alert(
    user_id: int,
    payload: AlertCreate,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    """Crea una alerta para el usuario autenticado validando reglas de negocio."""
    ensure_user_exists(user_id, db)

    # Validar que el usuario que crea la alerta es el mismo que está logueado
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para crear alertas para otro usuario."
        )

    # Extraemos los nombres de los roles del current_user (ahora es un objeto SQLAlchemy)
    nombres_roles = [rol.name.lower() for rol in current_user.roles]

    # Adaptado a los roles "lector" y "gestor" de tu BD real
    if "lector" in nombres_roles and "gestor" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )

    # Validar regla: Límite máximo de 20 alertas por usuario
    # En SQL usamos .count() en lugar de traer todos los registros a memoria para contarlos
    user_alerts_count = (
        db.scalar(select(func.count()).select_from(db_models.Alert).where(db_models.Alert.user_id == user_id)) or 0
    )
    if user_alerts_count >= 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Límite máximo de 20 alertas alcanzado.")

    # Validar regla: Entre 3 y 10 descriptores
    if len(payload.descriptors) < 3 or len(payload.descriptors) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La alerta debe tener entre 3 y 10 descriptores (sinónimos).",
        )

    # Validar que los IDs de canales RSS e información existen en la base de datos antes de crear la alerta
    if payload.rss_channels_ids:
        exists_count = db.scalar(select(func.count()).where(db_models.RSSChannel.id.in_(payload.rss_channels_ids)))
        if exists_count != len(payload.rss_channels_ids):
            raise HTTPException(status_code=400, detail="Uno o más rss_channels_ids no son válidos.")

    if payload.information_sources_ids:
        exists_count = db.scalar(
            select(func.count()).where(db_models.InformationSource.id.in_(payload.information_sources_ids))
        )
        if exists_count != len(payload.information_sources_ids):
            raise HTTPException(status_code=400, detail="Uno o más information_sources_ids no son válidos.")

    # Crear la alerta en PostgreSQL
    db_alert = db_models.Alert(user_id=user_id, **payload.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    return db_alert


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def get_user_alert(
    user_id: int, alert_id: int, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Alert:
    """Obtiene una alerta concreta de un usuario."""
    nombres_roles = [rol.name.lower() for rol in current_user.roles]
    if "lector" in nombres_roles and "gestor" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )

    return ensure_alert_for_user(user_id, alert_id, db)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def update_user_alert(
    user_id: int,
    alert_id: int,
    payload: AlertUpdate,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    """Actualiza una alerta de usuario."""
    nombres_roles = [rol.name.lower() for rol in current_user.roles]
    if "lector" in nombres_roles and "gestor" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )

    db_alert = ensure_alert_for_user(user_id, alert_id, db)

    # Validar regla: Entre 3 y 10 descriptores si se están actualizando

    if (payload.descriptors is not None) and (len(payload.descriptors) < 3 or len(payload.descriptors) > 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La alerta debe tener entre 3 y 10 descriptores (sinónimos).",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_alert, key, value)

    db.commit()
    db.refresh(db_alert)
    return db_alert


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["alerts"],
)
def delete_user_alert(
    user_id: int, alert_id: int, current_user: db_models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """Elimina una alerta y sus notificaciones relacionadas."""
    db_alert = ensure_alert_for_user(user_id, alert_id, db)

    nombres_roles = [rol.name.lower() for rol in current_user.roles]
    if "lector" in nombres_roles and "gestor" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )

    # Gracias a SQLAlchemy y el "CASCADE" de la BD, borrar la alerta aquí
    # eliminará automáticamente todas las notificaciones asociadas.
    db.delete(db_alert)
    db.commit()


@app.get(f"{API_PREFIX}/alerts/synonyms", response_model=SynonymResponse, tags=["alerts"])
async def get_alert_synonyms(
    term: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(DEFAULT_SYNONYM_LIMIT, ge=MIN_SYNONYM_LIMIT, le=MAX_SYNONYM_LIMIT),
    _: db_models.User = Depends(get_current_user),
) -> SynonymResponse:
    """Genera sinónimos locales en español para descriptores de alertas."""
    try:
        synonyms = generate_synonyms(term=term, limit=limit, language=DEFAULT_LANGUAGE)
    except SynonymDataNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SynonymResponse(term=term.strip(), language=DEFAULT_LANGUAGE, limit=limit, synonyms=synonyms)


@app.get(f"{API_PREFIX}/alerts/synonyms/warmup", response_model=SynonymWarmupResponse, tags=["alerts"])
async def warmup_alert_synonyms(_: db_models.User = Depends(get_current_user)) -> SynonymWarmupResponse:
    """Precarga recursos de sinónimos para evitar latencia en la primera búsqueda."""
    status, detail = warmup_synonym_resources(language=DEFAULT_LANGUAGE)
    return SynonymWarmupResponse(status=status, detail=detail)


# CRUD alert notifications


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=list[Notification],
    tags=["notifications"],
)
def list_alert_notifications(
    user_id: int,
    alert_id: int,
    current_user: db_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Notification]:
    """Lista notificaciones de una alerta."""
    # Verificamos que la alerta existe y es del usuario
    ensure_alert_for_user(user_id, alert_id, db)

    # Consultamos las notificaciones en PostgreSQL
    return list(db.scalars(select(db_models.Notification).where(db_models.Notification.alert_id == alert_id)))


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=Notification,
    status_code=201,
    tags=["notifications"],
)
def create_alert_notification(
    user_id: int,
    alert_id: int,
    payload: NotificationCreate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    """Crea una notificación para una alerta concreta."""
    ensure_alert_for_user(user_id, alert_id, db)

    # Creamos la entidad en la base de datos (Postgres genera el ID automáticamente)
    db_notification = db_models.Notification(alert_id=alert_id, **payload.model_dump())

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    return db_notification


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=Notification,
    tags=["notifications"],
)
def get_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    """Obtiene una notificación concreta de una alerta."""
    """Obtiene una notificación concreta de una alerta."""
    ensure_alert_for_user(user_id, alert_id, db)
    return ensure_notification_for_alert(alert_id, notification_id, db)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=Notification,
    tags=["notifications"],
)
def update_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    payload: NotificationUpdate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    """Actualiza una notificación de alerta."""
    ensure_alert_for_user(user_id, alert_id, db)
    db_notification = ensure_notification_for_alert(alert_id, notification_id, db)

    # Actualizamos los campos que vengan en el payload
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_notification, key, value)

    db.commit()
    db.refresh(db_notification)

    return db_notification


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["notifications"],
)
def delete_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Elimina una notificación de alerta."""
    ensure_alert_for_user(user_id, alert_id, db)
    db_notification = ensure_notification_for_alert(alert_id, notification_id, db)

    db.delete(db_notification)
    db.commit()


@app.post(f"{API_PREFIX}/alerts/trigger", tags=["alerts"])
def force_alert_matching(background_tasks: BackgroundTasks, current_user: db_models.User = Depends(get_current_user)):
    """Fuerza una batida de comprobación de alertas bajo demanda."""
    background_tasks.add_task(run_alert_matching)

    return {"status": "Procesando", "message": f"Batida de alertas iniciada por {current_user.email}."}


# CRUD categorias


@app.get(f"{API_PREFIX}/categories", response_model=list[Category], tags=["categories"])
def list_categories(_: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Category]:
    """Lista categorías configuradas."""
    return list(db.scalars(select(db_models.Category)))


@app.post(f"{API_PREFIX}/categories", response_model=Category, status_code=201, tags=["categories"])
def create_category(
    payload: CategoryCreate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> Category:
    """Crea una nueva categoría."""
    db_category = db_models.Category(**payload.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def get_category(category_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> Category:
    """Obtiene una categoría por identificador."""
    db_category = db.get(db_models.Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_category


@app.put(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def update_category(
    category_id: int, payload: CategoryUpdate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> Category:
    """Actualiza una categoría existente."""
    db_category = db.get(db_models.Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.delete(
    f"{API_PREFIX}/categories/{{category_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["categories"],
)
def delete_category(category_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Elimina una categoría si no está asociada a canales RSS."""
    db_category = db.get(db_models.Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Comprobamos si hay algún canal RSS asociado a esta categoría
    # (Ajusta 'db_models.RSSChannel' si tu modelo se llama de otra forma)
    associated_channel = db.scalar(select(db_models.RSSChannel).where(db_models.RSSChannel.category_id == category_id))

    if associated_channel:
        raise HTTPException(status_code=409, detail="Categoría asociada a canales RSS")

    db.delete(db_category)
    db.commit()


# CRUD information sources
@app.get(
    f"{API_PREFIX}/information-sources",
    response_model=list[InformationSource],
    tags=["information-sources"],
)
def list_information_sources(
    _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[InformationSource]:
    """Lista fuentes de información."""
    return list(db.scalars(select(db_models.InformationSource)))


@app.post(
    f"{API_PREFIX}/information-sources",
    response_model=InformationSource,
    status_code=201,
    tags=["information-sources"],
)
def create_information_source(
    payload: InformationSourceCreate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InformationSource:
    """Crea una fuente de información."""
    db_source = db_models.InformationSource(**payload.model_dump())

    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return db_source


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSource,
    tags=["information-sources"],
)
def get_information_source(
    source_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> InformationSource:
    """Obtiene una fuente de información por identificador."""
    db_source = db.get(db_models.InformationSource, source_id)

    if not db_source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    return db_source


@app.put(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSource,
    tags=["information-sources"],
)
def update_information_source(
    source_id: int,
    payload: InformationSourceUpdate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InformationSource:
    """Actualiza una fuente de información existente."""
    db_source = db.get(db_models.InformationSource, source_id)

    if not db_source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)

    return db_source


@app.delete(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["information-sources"],
)
def delete_information_source(
    source_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """Elimina una fuente y sus canales RSS asociados."""
    db_source = db.get(db_models.InformationSource, source_id)

    if not db_source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    # Al borrar el objeto de la base de datos, PostgreSQL ejecutará un ON DELETE CASCADE
    # para eliminar automáticamente los registros dependientes en la tabla de canales RSS.
    db.delete(db_source)
    db.commit()


# CRUD source channels


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=list[RSSChannel],
    tags=["rss-channels"],
)
def list_source_channels(
    source_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RSSChannel]:
    """Lista canales RSS de una fuente."""
    ensure_information_source_exists(source_id, db)
    return list(db.scalars(select(db_models.RSSChannel).where(db_models.RSSChannel.information_source_id == source_id)))


@app.post(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=RSSChannel,
    status_code=201,
    tags=["rss-channels"],
)
def create_source_channel(
    source_id: int,
    payload: RSSChannelCreate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    """Crea un canal RSS para una fuente de información."""
    ensure_information_source_exists(source_id, db)
    ensure_category_exists(payload.category_id, db)

    db_channel = db_models.RSSChannel(
        information_source_id=source_id,
        **payload.model_dump(),
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    response_model=RSSChannel,
    tags=["rss-channels"],
)
def get_source_channel(
    source_id: int,
    channel_id: int,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    """Obtiene un canal RSS concreto de una fuente."""
    ensure_information_source_exists(source_id, db)
    return ensure_rss_for_source(source_id, channel_id, db)


@app.put(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    response_model=RSSChannel,
    tags=["rss-channels"],
)
def update_source_channel(
    source_id: int,
    channel_id: int,
    payload: RSSChannelUpdate,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    """Actualiza un canal RSS existente."""
    ensure_information_source_exists(source_id, db)
    db_channel = ensure_rss_for_source(source_id, channel_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        ensure_category_exists(update_data["category_id"], db)

    for key, value in update_data.items():
        setattr(db_channel, key, value)

    db.commit()
    db.refresh(db_channel)
    return db_channel


@app.delete(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["rss-channels"],
)
def delete_source_channel(
    source_id: int,
    channel_id: int,
    _: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Elimina un canal RSS de una fuente."""
    ensure_information_source_exists(source_id, db)
    db_channel = ensure_rss_for_source(source_id, channel_id, db)

    db.delete(db_channel)
    db.commit()


# CRUD stats


@app.get(f"{API_PREFIX}/stats", response_model=list[Stats], tags=["stats"])
def list_stats(_: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Stats]:
    """Lista entradas de estadísticas globales."""
    return list(db.scalars(select(db_models.Stats)))


@app.post(f"{API_PREFIX}/stats", response_model=Stats, status_code=201, tags=["stats"])
def create_stats(payload: StatsCreate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> Stats:
    """Crea una entrada de estadísticas."""
    db_stats = db_models.Stats(**payload.model_dump())
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats


@app.get(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def get_stats(stats_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> Stats:
    """Obtiene estadísticas por identificador."""
    db_stats = db.get(db_models.Stats, stats_id)
    if not db_stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    return db_stats


@app.put(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def update_stats(
    stats_id: int, payload: StatsUpdate, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
) -> Stats:
    """Actualiza una entrada de estadísticas."""
    db_stats = db.get(db_models.Stats, stats_id)
    if not db_stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_stats, key, value)

    db.commit()
    db.refresh(db_stats)
    return db_stats


@app.delete(
    f"{API_PREFIX}/stats/{{stats_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["stats"],
)
def delete_stats(stats_id: int, _: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Elimina una entrada de estadísticas."""
    db_stats = db.get(db_models.Stats, stats_id)
    if not db_stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")

    db.delete(db_stats)
    db.commit()


def update_global_stats(db: Session) -> db_models.Stats:
    """
    Calcula las estadísticas globales consultando la BD.
    Usa el registro con ID=1 como caché global.
    """
    # 1. Contamos las filas de las tablas que sí tienes en PostgreSQL
    t_notifications = db.scalar(select(func.count(db_models.Notification.id))) or 0
    t_users = db.scalar(select(func.count(db_models.User.id))) or 0
    t_alerts = db.scalar(select(func.count(db_models.Alert.id))) or 0
    t_sources = db.scalar(select(func.count(db_models.InformationSource.id))) or 0
    t_channels = db.scalar(select(func.count(db_models.RSSChannel.id))) or 0

    # 2. Estructuramos el JSON de 'metrics' como una lista de diccionarios
    # para respetar tu modelo (default=list)
    current_metrics = [
        {"name": "total_users", "value": float(t_users)},
        {"name": "total_alerts", "value": float(t_alerts)},
        {"name": "total_information_sources", "value": float(t_sources)},
        {"name": "total_rss_channels", "value": float(t_channels)},
    ]

    db_stats = db.get(db_models.Stats, 1)

    if not db_stats:
        # Si la tabla está vacía, creamos el registro base
        db_stats = db_models.Stats(id=1, total_news=0)
        db.add(db_stats)

    # 4. Actualizamos los campos
    db_stats.total_notifications = t_notifications
    db_stats.metrics = current_metrics
    # Nota: total_news no lo tocamos aquí porque ese dato se traerá de Elasticsearch

    # 5. Guardamos en base de datos
    db.commit()
    db.refresh(db_stats)

    return db_stats


def rss_fetcher_engine():
    """Lógica exclusiva de extracción e indexación (Productor)."""
    print("[MOTOR RSS] Iniciando ciclo de extracción...")
    with SessionLocal() as db:
        db_stats = db.scalar(select(db_models.Stats))
        if not db_stats:
            db_stats = db_models.Stats(total_news=0, total_notifications=0)
            db.add(db_stats)
            db.commit()

        canales = list(db.scalars(select(db_models.RSSChannel)))
        for channel in canales:
            try:
                response = requests.get(str(channel.url), timeout=15)
                response.raise_for_status()
                feed = feedparser.parse(response.content)

                nuevas_noticias = 0
                for entry in feed.entries:
                    doc = {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published_at": normalize_published_at(entry),  # Asumo que tienes esta función
                        "channel_id": channel.id,
                        "category_id": channel.category_id,
                    }
                    try:
                        es_client.index(index=NEWS_INDEX, id=doc["link"], document=doc)
                        nuevas_noticias += 1
                    except Exception as e:
                        print(f"[ELASTIC] Error indexando: {e}")

                if nuevas_noticias > 0:
                    print(f"[MOTOR RSS] {nuevas_noticias} noticias de: {channel.url}")
                    db_stats.total_news += nuevas_noticias

            except Exception as e:
                print(f"[MOTOR RSS] Error canal {channel.url}: {e}")

        db.commit()
        update_global_stats(db)  # Asumo que tienes esta función
        print("[MOTOR RSS] Ciclo de extracción finalizado.")


def run_alert_matching():
    """Lógica exclusiva de cruce de alertas (Consumidor)."""
    print("[EL RADAR] Cruzando alertas con las noticias...")
    with SessionLocal() as db:
        alertas = list(db.scalars(select(db_models.Alert)))
        db_stats = db.scalar(select(db_models.Stats))  # Necesario para actualizar Stats aquí también
        for alert in alertas:
            if not alert.descriptors:
                continue
            # 1. Construimos la consulta para Elasticsearch
            # Buscamos en 'title' y 'summary' cualquier coincidencia con los descriptores
            clausulas_busqueda = [
                {"multi_match": {"query": desc, "fields": ["title", "summary"]}} for desc in alert.descriptors
            ]

            # Filtros obligatorios base (siempre miramos los últimos 24 horas)
            filtros = [{"range": {"published_at": {"gte": "now-24h"}}}]
            # Si el usuario especificó categorías, obligamos a Elasticsearch a buscar SOLO en ellas

            # A. Filtrar por Canales específicos
            if alert.rss_channels_ids:
                # Convertimos a int si tus IDs en la tabla son enteros
                ids_int = [int(i) for i in alert.rss_channels_ids]
                filtros.append({"terms": {"channel_id": ids_int}})

            # B. Filtrar por Fuentes de Información (InformationSource)
            if alert.information_sources_ids:
                # Buscamos qué canales pertenecen a esas fuentes
                ids_fuentes_int = [int(i) for i in alert.information_sources_ids]
                canales_de_fuentes = db.scalars(
                    select(db_models.RSSChannel.id).where(
                        db_models.RSSChannel.information_source_id.in_(ids_fuentes_int)
                    )
                ).all()

                if canales_de_fuentes:
                    filtros.append({"terms": {"channel_id": list(canales_de_fuentes)}})
                else:
                    # Si la fuente no tiene canales, bloqueamos para que no devuelva todo
                    filtros.append({"terms": {"channel_id": [-1]}})

            if alert.categories:
                try:
                    # 1. Extraemos los nombres de las categorías con cuidado
                    nombres_categorias = []
                    for cat in alert.categories:
                        if isinstance(cat, dict):  # Si viene como JSON dict de la BD
                            nombres_categorias.append(cat.get("label"))
                        else:  # Si viene como un objeto Pydantic/SQLAlchemy
                            nombres_categorias.append(getattr(cat, "label", getattr(cat, "name", "")))

                    # Limpiamos posibles nulos o vacíos
                    nombres_categorias = [n for n in nombres_categorias if n]

                    # 2. Buscamos en PostgreSQL qué IDs numéricos corresponden a esos nombres
                    categorias_db = list(
                        db.scalars(select(db_models.Category).where(db_models.Category.name.in_(nombres_categorias)))
                    )
                    ids_categorias = [c.id for c in categorias_db]

                    # CHIVATO: Te mostrará en la terminal qué está pasando realmente
                    print(
                        f"[DEBUG] Alerta '{alert.name}' busca: {nombres_categorias}. IDs encontrados en BD: {ids_categorias}"
                    )

                    # 3. Aplicamos el filtro estricto
                    if ids_categorias:
                        filtros.append({"terms": {"category_id": ids_categorias}})
                    else:
                        # FALLO SILENCIOSO EVITADO: Si no encuentra las categorías, le pasamos un ID imposible
                        # para que no devuelva todas las noticias de la base de datos.
                        print(
                            f"[WARNING] Las categorías {nombres_categorias} no coinciden con ninguna de la base de datos."
                        )
                        filtros.append({"terms": {"category_id": [-1]}})

                except Exception as e:
                    print(f"[RADAR] Error procesando categorías para la alerta '{alert.name}': {e}")
                    filtros.append({"terms": {"category_id": [-1]}})  # Bloqueo de seguridad en caso de error

            consulta = {
                "query": {
                    "bool": {
                        "should": clausulas_busqueda,
                        "minimum_should_match": 1,  # Al menos 1 descriptor debe coincidir
                        "filter": filtros,  # Aplicamos la lista de filtros obligatorios
                    }
                }
            }

            try:
                # 2. Disparamos la búsqueda en el índice
                resultados = es_client.search(index=NEWS_INDEX, body=consulta)

                # Elasticsearch devuelve el total de coincidencias en esta ruta
                total_hits = resultados["hits"]["total"]["value"]
                noticias_encontradas = resultados["hits"]["hits"]

                # 3. Si hay coincidencias, creamos la notificación
                if total_hits > 0:
                    print(f"[ALERTA DISPARADA] '{alert.name}' (User {alert.user_id}): {total_hits} coincidencias.")
                    lista_noticias = []

                    # Extraer categoría para la notificación
                    # Dependiendo de cómo guardes categories en SQLAlchemy (JSON o relación), extraemos el label
                    if alert.categories:
                        try:
                            # Si lo tienes como una lista de strings/dicts en un JSON
                            categoria_clasificada = ", ".join(
                                [cat if isinstance(cat, str) else cat.get("label", "") for cat in alert.categories]
                            )
                        except Exception:
                            categoria_clasificada = "General"
                    else:
                        categoria_clasificada = "General"

                    for noticia in noticias_encontradas:
                        datos_rss = noticia["_source"]
                        lista_noticias.append(datos_rss)

                        # Creamos la notificación en BD
                        # Nota: Asumo que "metrics" es un JSON o campo similar en BD
                        nueva_notificacion = db_models.Notification(
                            alert_id=alert.id,
                            timestamp=datetime.now(UTC),
                            metrics=[{"name": "noticias_encontradas", "value": float(total_hits)}],
                            iptc_category=categoria_clasificada,
                        )
                        db.add(nueva_notificacion)
                        if db_stats is not None:
                            db_stats.total_notifications += 1

                    # --- LLAMADA PARA ENVIAR EL EMAIL ---
                    usuario = db.get(db_models.User, alert.user_id)
                    if usuario and usuario.email:
                        send_alert_email(to_email=usuario.email, alert_name=alert.name, news_data=lista_noticias)
                else:
                    print(f"[ALERTA NO DISPARADA] '{alert.name}' (User {alert.user_id}): 0 coincidencias.")
            except Exception as e:
                print(f"[RADAR] Error consultando alerta '{alert.name}': {e}")

        db.commit()
        print("[EL RADAR] Cruce de alertas finalizado.")
