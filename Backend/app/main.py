"""API backend de NewsRadar con modelos, endpoints y motor RSS en memoria."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import feedparser
from elasticsearch import Elasticsearch
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.core.security import (
    create_verification_token,
    send_alert_email,
    send_verification_email,
)

ELASTICSEARCH_URL = "http://localhost:9200"

# 2. Instanciar el cliente global
es_client = Elasticsearch(ELASTICSEARCH_URL)


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


app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS.",
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
    cron_expression: str = Field(..., min_length=1, max_length=120)


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    descriptors: list[str] | None = None
    categories: list[AlertCategoryItem] | None = None
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


roles_store: dict[int, Role] = {}
users_store: dict[int, UserInDB] = {}
alerts_store: dict[int, Alert] = {}
categories_store: dict[int, Category] = {}
notifications_store: dict[int, Notification] = {}
information_sources_store: dict[int, InformationSource] = {}
rss_channels_store: dict[int, RSSChannel] = {}
stats_store: dict[int, Stats] = {}

active_tokens: dict[str, int] = {}

counters = {
    "roles": 1,
    "users": 1,
    "alerts": 1,
    "categories": 1,
    "notifications": 1,
    "information_sources": 1,
    "rss_channels": 1,
    "stats": 1,
}


def next_id(counter_key: str) -> int:
    """Devuelve el siguiente identificador autoincremental para una entidad."""
    value = counters[counter_key]
    counters[counter_key] += 1
    return value


def ensure_role_ids_exist(role_ids: list[int]) -> None:
    """Valida que todos los IDs de rol existen en memoria."""
    missing = [role_id for role_id in role_ids if role_id not in roles_store]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roles no encontrados: {missing}",
        )


def ensure_user_exists(user_id: int) -> None:
    """Lanza 404 si el usuario no existe."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


def ensure_alert_for_user(user_id: int, alert_id: int) -> Alert:
    """Obtiene una alerta de un usuario o lanza 404 si no corresponde."""
    alert = alerts_store.get(alert_id)
    if not alert or alert.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada para el usuario")
    return alert


def ensure_notification_for_alert(alert_id: int, notification_id: int) -> Notification:
    """Obtiene una notificación de una alerta o lanza 404."""
    notification = notifications_store.get(notification_id)
    if not notification or notification.alert_id != alert_id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada para la alerta")
    return notification


def ensure_information_source_exists(source_id: int) -> None:
    """Lanza 404 si la fuente de información no existe."""
    if source_id not in information_sources_store:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")


def ensure_category_exists(category_id: int) -> None:
    """Lanza 404 si la categoría no existe."""
    if category_id not in categories_store:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


def ensure_rss_for_source(source_id: int, channel_id: int) -> RSSChannel:
    """Obtiene un canal RSS de una fuente concreta o lanza 404."""
    channel = rss_channels_store.get(channel_id)
    if not channel or channel.information_source_id != source_id:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")
    return channel


def sanitize_user(user: UserInDB) -> User:
    """Devuelve la representación pública de usuario sin contraseña."""
    return User(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        organization=user.organization,
        role_ids=user.role_ids,
        is_verified=user.is_verified,  # Este campo se incluye para que el cliente sepa si el usuario está verificado o no
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    """Autentica el token bearer y devuelve el usuario asociado."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token inválido o ausente")

    user_id = active_tokens.get(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = users_store.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inválido")

    return user


def create_seed_data() -> None:
    """Inicializa roles, usuario admin y semilla de fuentes/canales RSS."""
    if roles_store:
        return

    admin_role_id = next_id("roles")
    roles_store[admin_role_id] = Role(id=admin_role_id, name="admin")

    user_role_id = next_id("roles")
    roles_store[user_role_id] = Role(id=user_role_id, name="user")

    admin_user_id = next_id("users")
    users_store[admin_user_id] = UserInDB(
        id=admin_user_id,
        email="admin@newsradar.com",
        first_name="Admin",
        last_name="NewsRadar",
        organization="NewsRadar",
        role_ids=[admin_role_id],
        password="admin123",
        is_verified=True,
    )

    stats_store[1] = Stats(id=1, total_news=0, total_notifications=0)

    # --- 2. CARGA DE FUENTES Y CANALES RSS DESDE EL JSON ---
    base_dir = Path(__file__).resolve().parent
    seed_file = base_dir / "data" / "rss_seed.json"

    if seed_file.exists():
        with open(seed_file, encoding="utf-8") as f:
            data = json.load(f)

        for source_data in data:
            # Si el JSON no la tiene, le ponemos una por defecto basada en el nombre.
            fake_url = f"https://www.{source_data['source_name'].lower().replace(' ', '')}.com"
            source_url = source_data.get("url", fake_url)

            # Crear la fuente
            source_id = next_id("information_sources")
            source = InformationSource(id=source_id, name=source_data["source_name"], url=source_url)
            information_sources_store[source_id] = source

            # Recorrer los canales de esta fuente
            for channel_data in source_data.get("channels", []):
                cat_name = channel_data.get("category", "General")

                # Buscar si la categoría ya existe en nuestro diccionario
                category = next((c for c in categories_store.values() if c.name == cat_name), None)

                # Si no existe, la creamos y la guardamos en el diccionario
                if not category:
                    cat_id = next_id("categories")
                    # El esquema pide 'source' por defecto a "IPTC"
                    category = Category(id=cat_id, name=cat_name, source="IPTC")
                    categories_store[cat_id] = category

                # Crear el canal (Fíjate que el modelo actual no usa 'name', solo URL y Category)
                channel_id = next_id("rss_channels")
                channel = RSSChannel(
                    id=channel_id, information_source_id=source_id, url=channel_data["url"], category_id=category.id
                )
                rss_channels_store[channel_id] = channel

        print("[STARTUP] Semilla cargada: Usuarios, Fuentes, Categorías y Canales en memoria.")
    else:
        print(f"[STARTUP] Archivo JSON no encontrado en: {seed_file}")


@app.on_event("startup")
def on_startup() -> None:
    """Ejecuta inicialización de datos y arranca el motor RSS."""
    create_seed_data()
    check_elastic_connection()
    _ = asyncio.create_task(rss_fetcher_engine())


@app.get(f"{API_PREFIX}/health", tags=["system"])
def health() -> dict:
    """Devuelve estado de salud básico del servicio."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@app.post(f"{API_PREFIX}/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest) -> TokenResponse:
    """Autentica credenciales y emite token de sesión en memoria."""
    user = next((u for u in users_store.values() if u.email == payload.email), None)
    if user is None or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = str(uuid4())
    active_tokens[token] = user.id
    return TokenResponse(access_token=token)


@app.post(f"{API_PREFIX}/auth/register", response_model=User, tags=["auth"])
def register(payload: UserCreate) -> User:
    """Registra un usuario nuevo y envía email de verificación."""
    if any(user.email == payload.email for user in users_store.values()):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    ensure_role_ids_exist(payload.role_ids)

    user_id = next_id("users")
    user_db = UserInDB(id=user_id, **payload.model_dump())
    users_store[user_id] = user_db
    # verificacion de Email
    token = create_verification_token(user_db.email)
    send_verification_email(user_db.email, token)

    return sanitize_user(user_db)


@app.get(f"{API_PREFIX}/auth/verify", tags=["auth"])
def verify_email(token: str):
    """Verifica un usuario validando el token JWT de verificación."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token de verificación inválido o expirado",
    )
    try:
        # Decodificamos el token (fallará automáticamente si pasaron 24h)
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "newsradar_secret_key_temporal"), algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception from None
        print(f"[VERIFY] Token decodificado, email: {email}")
    except JWTError as e:
        print(f"[VERIFY] Error decodificando token: {e}")
        raise credentials_exception from None

    # Buscamos al usuario en la BD
    user = None
    for u in users_store.values():
        if u.email == email:
            user = u
            break

    if user is None:
        print(f"[VERIFY] Usuario no encontrado para email: {email}")
        raise credentials_exception from None

    if user.is_verified:
        print(f"[VERIFY] Usuario ya verificado: {email}")
        return {"msg": "El usuario ya estaba verificado"}
    usuario_actualizado = user.model_copy(update={"is_verified": True})
    users_store[user.id] = usuario_actualizado
    print(f"[VERIFY] Usuario verificado exitosamente: {email}")
    user = users_store.get(2)
    # print(f"[VERIFY] Usuario actualizado en store: {user.email}, is_verified={user.is_verified}")

    return {"msg": "Cuenta verificada con éxito. Ya puedes iniciar sesión."}


@app.get(f"{API_PREFIX}/users", response_model=list[User], tags=["users"])
def list_users(_: UserInDB = Depends(get_current_user)) -> list[User]:
    """Lista los usuarios registrados."""
    return [sanitize_user(user) for user in users_store.values()]


@app.post(f"{API_PREFIX}/users", response_model=User, status_code=201, tags=["users"])
def create_user(payload: UserCreate, _: UserInDB = Depends(get_current_user)) -> User:
    """Crea un usuario desde la API protegida."""
    if any(user.email == payload.email for user in users_store.values()):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    ensure_role_ids_exist(payload.role_ids)
    user_id = next_id("users")
    user_db = UserInDB(id=user_id, **payload.model_dump())
    users_store[user_id] = user_db
    return sanitize_user(user_db)


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def get_user(user_id: int, _: UserInDB = Depends(get_current_user)) -> User:
    """Obtiene un usuario por su identificador."""
    user = users_store.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return sanitize_user(user)


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def update_user(user_id: int, payload: UserUpdate, _: UserInDB = Depends(get_current_user)) -> User:
    """Actualiza los campos permitidos de un usuario."""
    user = users_store.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and any(u.email == data["email"] and u.id != user_id for u in users_store.values()):
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    if "role_ids" in data:
        ensure_role_ids_exist(data["role_ids"])

    updated = user.model_copy(update=data)
    users_store[user_id] = updated
    return sanitize_user(updated)


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["users"],
)
def delete_user(user_id: int, _: UserInDB = Depends(get_current_user)) -> None:
    """Elimina un usuario y sus alertas/notificaciones asociadas."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    alert_ids = [alert.id for alert in alerts_store.values() if alert.user_id == user_id]
    for alert_id in alert_ids:
        notification_ids = [n.id for n in notifications_store.values() if n.alert_id == alert_id]
        for notification_id in notification_ids:
            notifications_store.pop(notification_id, None)
        alerts_store.pop(alert_id, None)

    users_store.pop(user_id, None)


@app.get(f"{API_PREFIX}/roles", response_model=list[Role], tags=["roles"])
def list_roles(_: UserInDB = Depends(get_current_user)) -> list[Role]:
    """Lista todos los roles."""
    return list(roles_store.values())


@app.post(f"{API_PREFIX}/roles", response_model=Role, status_code=201, tags=["roles"])
def create_role(payload: RoleCreate, _: UserInDB = Depends(get_current_user)) -> Role:
    """Crea un rol nuevo."""
    role_id = next_id("roles")
    role = Role(id=role_id, **payload.model_dump())
    roles_store[role_id] = role
    return role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def get_role(role_id: int, _: UserInDB = Depends(get_current_user)) -> Role:
    """Obtiene un rol por identificador."""
    role = roles_store.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def update_role(role_id: int, payload: RoleUpdate, _: UserInDB = Depends(get_current_user)) -> Role:
    """Actualiza un rol existente."""
    role = roles_store.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    updated = role.model_copy(update=payload.model_dump(exclude_unset=True))
    roles_store[role_id] = updated
    return updated


@app.delete(
    f"{API_PREFIX}/roles/{{role_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["roles"],
)
def delete_role(role_id: int, _: UserInDB = Depends(get_current_user)) -> None:
    """Elimina un rol si no está asignado a usuarios."""
    if role_id not in roles_store:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    for user in users_store.values():
        if role_id in user.role_ids:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar un rol asignado a usuarios",
            )

    roles_store.pop(role_id, None)


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=list[Alert],
    tags=["alerts"],
)
def list_user_alerts(user_id: int, current_user: UserInDB = Depends(get_current_user)) -> list[Alert]:
    """Lista las alertas asociadas a un usuario."""
    ensure_user_exists(user_id)

    return [alert for alert in alerts_store.values() if alert.user_id == user_id]


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=Alert,
    status_code=201,
    tags=["alerts"],
)
def create_user_alert(user_id: int, payload: AlertCreate, current_user: UserInDB = Depends(get_current_user)) -> Alert:
    """Crea una alerta para el usuario autenticado validando reglas de negocio."""
    ensure_user_exists(user_id)

    # Validar que el usuario que crea la alerta es el mismo que está logueado
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para crear alertas para otro usuario."
        )
    nombres_roles = [roles_store[rol_id].name.lower() for rol_id in current_user.role_ids if rol_id in roles_store]
    if "user" in nombres_roles and "admin" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )
    # Validar regla: Límite máximo de 20 alertas por usuario
    user_alerts_count = sum(1 for a in alerts_store.values() if a.user_id == user_id)
    if user_alerts_count >= 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Límite máximo de 20 alertas alcanzado.")

    # Validar regla: Entre 3 y 10 descriptores
    if len(payload.descriptors) < 3 or len(payload.descriptors) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La alerta debe tener entre 3 y 10 descriptores (sinónimos).",
        )

    alert_id = next_id("alerts")
    alert = Alert(id=alert_id, user_id=user_id, **payload.model_dump())
    alerts_store[alert_id] = alert
    return alert


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def get_user_alert(user_id: int, alert_id: int, current_user: UserInDB = Depends(get_current_user)) -> Alert:
    """Obtiene una alerta concreta de un usuario."""
    nombres_roles = [roles_store[rol_id].name.lower() for rol_id in current_user.role_ids if rol_id in roles_store]
    if "user" in nombres_roles and "admin" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )
    return ensure_alert_for_user(user_id, alert_id)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def update_user_alert(
    user_id: int,
    alert_id: int,
    payload: AlertUpdate,
    current_user: UserInDB = Depends(get_current_user),
) -> Alert:
    """Actualiza una alerta de usuario."""
    nombres_roles = [roles_store[rol_id].name.lower() for rol_id in current_user.role_ids if rol_id in roles_store]

    if "user" in nombres_roles and "admin" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )
    alert = ensure_alert_for_user(user_id, alert_id)
    updated = alert.model_copy(update=payload.model_dump(exclude_unset=True))
    alerts_store[alert_id] = updated
    return updated


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["alerts"],
)
def delete_user_alert(user_id: int, alert_id: int, current_user: UserInDB = Depends(get_current_user)) -> None:
    """Elimina una alerta y sus notificaciones relacionadas."""
    ensure_alert_for_user(user_id, alert_id)
    nombres_roles = [roles_store[rol_id].name.lower() for rol_id in current_user.role_ids if rol_id in roles_store]
    if "user" in nombres_roles and "admin" not in nombres_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los lectores no tienen permisos para crear ni gestionar alertas.",
        )
    notification_ids = [n.id for n in notifications_store.values() if n.alert_id == alert_id]
    for notification_id in notification_ids:
        notifications_store.pop(notification_id, None)
    alerts_store.pop(alert_id, None)


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=list[Notification],
    tags=["notifications"],
)
def list_alert_notifications(
    user_id: int,
    alert_id: int,
    current_user: UserInDB = Depends(get_current_user),
) -> list[Notification]:
    """Lista notificaciones de una alerta."""
    ensure_alert_for_user(user_id, alert_id)
    return [item for item in notifications_store.values() if item.alert_id == alert_id]


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
) -> Notification:
    """Crea una notificación para una alerta concreta."""
    ensure_alert_for_user(user_id, alert_id)
    notification_id = next_id("notifications")
    notification = Notification(id=notification_id, alert_id=alert_id, **payload.model_dump())
    notifications_store[notification_id] = notification
    return notification


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
) -> Notification:
    """Obtiene una notificación concreta de una alerta."""
    ensure_alert_for_user(user_id, alert_id)
    return ensure_notification_for_alert(alert_id, notification_id)


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
) -> Notification:
    """Actualiza una notificación de alerta."""
    ensure_alert_for_user(user_id, alert_id)
    notification = ensure_notification_for_alert(alert_id, notification_id)
    updated = notification.model_copy(update=payload.model_dump(exclude_unset=True))
    notifications_store[notification_id] = updated
    return updated


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
) -> None:
    """Elimina una notificación de alerta."""
    ensure_alert_for_user(user_id, alert_id)
    ensure_notification_for_alert(alert_id, notification_id)
    notifications_store.pop(notification_id, None)


@app.get(f"{API_PREFIX}/categories", response_model=list[Category], tags=["categories"])
def list_categories(_: UserInDB = Depends(get_current_user)) -> list[Category]:
    """Lista categorías configuradas."""
    return list(categories_store.values())


@app.post(f"{API_PREFIX}/categories", response_model=Category, status_code=201, tags=["categories"])
def create_category(payload: CategoryCreate, _: UserInDB = Depends(get_current_user)) -> Category:
    """Crea una nueva categoría."""
    category_id = next_id("categories")
    category = Category(id=category_id, **payload.model_dump())
    categories_store[category_id] = category
    return category


@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def get_category(category_id: int, _: UserInDB = Depends(get_current_user)) -> Category:
    """Obtiene una categoría por identificador."""
    category = categories_store.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@app.put(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def update_category(category_id: int, payload: CategoryUpdate, _: UserInDB = Depends(get_current_user)) -> Category:
    """Actualiza una categoría existente."""
    category = categories_store.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    updated = category.model_copy(update=payload.model_dump(exclude_unset=True))
    categories_store[category_id] = updated
    return updated


@app.delete(
    f"{API_PREFIX}/categories/{{category_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["categories"],
)
def delete_category(category_id: int, _: UserInDB = Depends(get_current_user)) -> None:
    """Elimina una categoría si no está asociada a canales RSS."""
    if category_id not in categories_store:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for channel in rss_channels_store.values():
        if channel.category_id == category_id:
            raise HTTPException(status_code=409, detail="Categoría asociada a canales RSS")

    categories_store.pop(category_id, None)


@app.get(
    f"{API_PREFIX}/information-sources",
    response_model=list[InformationSource],
    tags=["information-sources"],
)
def list_information_sources(_: UserInDB = Depends(get_current_user)) -> list[InformationSource]:
    """Lista fuentes de información."""
    return list(information_sources_store.values())


@app.post(
    f"{API_PREFIX}/information-sources",
    response_model=InformationSource,
    status_code=201,
    tags=["information-sources"],
)
def create_information_source(
    payload: InformationSourceCreate,
    _: UserInDB = Depends(get_current_user),
) -> InformationSource:
    """Crea una fuente de información."""
    source_id = next_id("information_sources")
    source = InformationSource(id=source_id, **payload.model_dump())
    information_sources_store[source_id] = source
    return source


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSource,
    tags=["information-sources"],
)
def get_information_source(source_id: int, _: UserInDB = Depends(get_current_user)) -> InformationSource:
    """Obtiene una fuente de información por identificador."""
    source = information_sources_store.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    return source


@app.put(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSource,
    tags=["information-sources"],
)
def update_information_source(
    source_id: int,
    payload: InformationSourceUpdate,
    _: UserInDB = Depends(get_current_user),
) -> InformationSource:
    """Actualiza una fuente de información existente."""
    source = information_sources_store.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    updated = source.model_copy(update=payload.model_dump(exclude_unset=True))
    information_sources_store[source_id] = updated
    return updated


@app.delete(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["information-sources"],
)
def delete_information_source(source_id: int, _: UserInDB = Depends(get_current_user)) -> None:
    """Elimina una fuente y sus canales RSS asociados."""
    if source_id not in information_sources_store:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel_ids = [channel.id for channel in rss_channels_store.values() if channel.information_source_id == source_id]
    for channel_id in channel_ids:
        rss_channels_store.pop(channel_id, None)

    information_sources_store.pop(source_id, None)


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=list[RSSChannel],
    tags=["rss-channels"],
)
def list_source_channels(source_id: int, _: UserInDB = Depends(get_current_user)) -> list[RSSChannel]:
    """Lista canales RSS de una fuente."""
    ensure_information_source_exists(source_id)
    return [channel for channel in rss_channels_store.values() if channel.information_source_id == source_id]


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
) -> RSSChannel:
    """Crea un canal RSS para una fuente de información."""
    ensure_information_source_exists(source_id)
    ensure_category_exists(payload.category_id)

    channel_id = next_id("rss_channels")
    channel = RSSChannel(
        id=channel_id,
        information_source_id=source_id,
        **payload.model_dump(),
    )
    rss_channels_store[channel_id] = channel
    return channel


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    response_model=RSSChannel,
    tags=["rss-channels"],
)
def get_source_channel(
    source_id: int,
    channel_id: int,
    _: UserInDB = Depends(get_current_user),
) -> RSSChannel:
    """Obtiene un canal RSS concreto de una fuente."""
    ensure_information_source_exists(source_id)
    return ensure_rss_for_source(source_id, channel_id)


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
) -> RSSChannel:
    """Actualiza un canal RSS existente."""
    ensure_information_source_exists(source_id)
    channel = ensure_rss_for_source(source_id, channel_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        ensure_category_exists(update_data["category_id"])

    updated = channel.model_copy(update=update_data)
    rss_channels_store[channel_id] = updated
    return updated


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
) -> None:
    """Elimina un canal RSS de una fuente."""
    ensure_information_source_exists(source_id)
    ensure_rss_for_source(source_id, channel_id)
    rss_channels_store.pop(channel_id, None)


@app.get(f"{API_PREFIX}/stats", response_model=list[Stats], tags=["stats"])
def list_stats(_: UserInDB = Depends(get_current_user)) -> list[Stats]:
    """Lista entradas de estadísticas globales."""
    return list(stats_store.values())


@app.post(f"{API_PREFIX}/stats", response_model=Stats, status_code=201, tags=["stats"])
def create_stats(payload: StatsCreate, _: UserInDB = Depends(get_current_user)) -> Stats:
    """Crea una entrada de estadísticas."""
    stats_id = next_id("stats")
    stats = Stats(id=stats_id, **payload.model_dump())
    stats_store[stats_id] = stats
    return stats


@app.get(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def get_stats(stats_id: int, _: UserInDB = Depends(get_current_user)) -> Stats:
    """Obtiene estadísticas por identificador."""
    stats = stats_store.get(stats_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    return stats


@app.put(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def update_stats(stats_id: int, payload: StatsUpdate, _: UserInDB = Depends(get_current_user)) -> Stats:
    """Actualiza una entrada de estadísticas."""
    stats = stats_store.get(stats_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")

    updated = stats.model_copy(update=payload.model_dump(exclude_unset=True))
    stats_store[stats_id] = updated
    return updated


@app.delete(
    f"{API_PREFIX}/stats/{{stats_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["stats"],
)
def delete_stats(stats_id: int, _: UserInDB = Depends(get_current_user)) -> None:
    """Elimina una entrada de estadísticas."""
    if stats_id not in stats_store:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    stats_store.pop(stats_id, None)


async def rss_fetcher_engine():
    """Ejecuta en bucle la captura RSS, indexación y generación de notificaciones."""
    # Esperamos un poco antes de arrancar la primera vez para dar tiempo a que cargue la semilla
    await asyncio.sleep(5)

    while True:
        print("[MOTOR RSS] Iniciando ciclo de extracción...")

        # Iteramos sobre todos los canales guardados en memoria
        for channel_id, channel in rss_channels_store.items():
            try:
                # Descargamos y parseamos el XML
                feed = feedparser.parse(str(channel.url))

                nuevas_noticias = 0
                for entry in feed.entries:
                    # Preparamos el documento
                    doc = {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published_at": entry.get("published", datetime.now(UTC).isoformat()),
                        "channel_id": channel_id,
                        "category_id": channel.category_id,
                    }

                    # Lo mandamos a Elasticsearch (al índice 'newsradar_articles')
                    # Usamos el link como ID en Elastic para evitar duplicados si la noticia ya se bajó
                    es_client.index(index="newsradar_articles", id=doc["link"], document=doc)
                    nuevas_noticias += 1

                if nuevas_noticias > 0:
                    print(f"[MOTOR RSS] {nuevas_noticias} noticias indexadas de: {channel.url}")
                    stats_store[1].total_news += nuevas_noticias

            except Exception as e:
                print(f"[MOTOR RSS] Error procesando canal {channel.url}: {e}")

        print("[EL RADAR] Cruzando alertas con las nuevas noticias...")

        # Iteramos sobre todas las alertas que han creado los usuarios
        for alert_id, alert in alerts_store.items():
            if not alert.descriptors:
                continue

            # 1. Construimos la consulta para Elasticsearch
            # Buscamos en 'title' y 'summary' cualquier coincidencia con los descriptores
            clausulas_busqueda = [
                {"multi_match": {"query": desc, "fields": ["title", "summary"]}} for desc in alert.descriptors
            ]

            consulta = {
                "query": {
                    "bool": {
                        "should": clausulas_busqueda,
                        "minimum_should_match": 1,  # Al menos 1 descriptor debe coincidir
                        "filter": {
                            "range": {
                                # Importante: Solo miramos noticias de los últimos 15 min
                                # para no notificar lo mismo una y otra vez
                                "published_at": {"gte": "now-15m"}
                            }
                        },
                    }
                }
            }

            try:
                # 2. Disparamos la búsqueda en el índice
                resultados = es_client.search(index="newsradar_articles", body=consulta)

                # Elasticsearch devuelve el total de coincidencias en esta ruta
                total_hits = resultados["hits"]["total"]["value"]
                noticias_encontradas = resultados["hits"]["hits"]

                # 3. Si hay coincidencias, creamos la notificación
                if total_hits > 0:
                    print(f"[ALERTA DISPARADA] '{alert.name}' (User {alert.user_id}): {total_hits} coincidencias.")
                    lista_noticias = []
                    if alert.categories:
                        # Si son diccionarios, sacamos el 'label' (ej: "Tecnología")
                        # Si prefieres el código (ej: "TECH"), cambia cat.get('label') por cat.get('code')
                        try:
                            # Asumiendo que es un diccionario
                            # categoria_clasificada = ", ".join([cat.get('label', '') for cat in alert.categories])
                            if alert.categories:
                                categoria_clasificada = ", ".join([cat.label for cat in alert.categories])
                            else:
                                categoria_clasificada = "General"
                        except AttributeError:
                            # Por si resulta ser un objeto Pydantic y no un diccionario
                            categoria_clasificada = ", ".join([cat.label for cat in alert.categories])
                    else:
                        categoria_clasificada = "General"

                    for noticia in noticias_encontradas:
                        datos_rss = noticia["_source"]  # Aquí dentro están el título, resumen, etc.
                        lista_noticias.append(datos_rss)
                        notif_id = next_id("notifications")

                        # Creamos la notificación en el buzón
                        nueva_notificacion = Notification(
                            id=notif_id,
                            alert_id=alert_id,
                            timestamp=datetime.now(UTC),
                            metrics=[Metric(name="noticias_encontradas", value=float(total_hits))],
                            iptc_category=categoria_clasificada,
                        )
                        notifications_store[notif_id] = nueva_notificacion
                        stats_store[1].total_notifications += 1
                    # --- AQUÍ IRÁ LA LLAMADA PARA ENVIAR EL EMAIL ---
                    usuario = users_store.get(alert.user_id)
                    if usuario and usuario.email:
                        send_alert_email(to_email=usuario.email, alert_name=alert.name, news_data=lista_noticias)
            except Exception as e:
                print(f"[RADAR] Error consultando alerta '{alert.name}': {e}")
        print("[MOTOR RSS] Ciclo completado. Durmiendo 15 minutos...")
        # Esperamos 15 minutos (900 segundos) hasta la próxima batida
        # await asyncio.sleep(900)
        await asyncio.sleep(30)  # Para pruebas, lo dejamos en 1 minuto
