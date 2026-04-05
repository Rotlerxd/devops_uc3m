from __future__ import annotations

import os
from datetime import UTC, datetime
import requests
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy.orm import Session
import json
from app.core.security import (
    create_access_token,
    create_verification_token,
    get_current_admin,
    get_current_user,
    get_password_hash,
    send_verification_email,
    verify_password,
)
from app.db import models
from app.db.database import SessionLocal, engine, get_db

app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS.",
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


class StatsCreate(StatsBase):
    pass


class StatsUpdate(BaseModel):
    metrics: list[Metric] | None = None


class Stats(StatsBase):
    id: int


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
    value = counters[counter_key]
    counters[counter_key] += 1
    return value


def ensure_role_ids_exist(role_ids: list[int]) -> None:
    missing = [role_id for role_id in role_ids if role_id not in roles_store]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roles no encontrados: {missing}",
        )


# def ensure_user_exists(user_id: int) -> None:
#     if user_id not in users_store:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")

def ensure_user_exists(user_id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )
    return user


#def ensure_alert_for_user(user_id: int, alert_id: int) -> Alert:
#    alert = alerts_store.get(alert_id)
#    if not alert or alert.user_id != user_id:
#        raise HTTPException(status_code=404, detail="Alerta no encontrada para el usuario")
#    return alert

def ensure_alert_for_user(user_id: int, alert_id: int, db: Session):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id, models.Alert.user_id == user_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada para el usuario")
    return alert


def ensure_notification_for_alert(alert_id: int, notification_id: int) -> Notification:
    notification = notifications_store.get(notification_id)
    if not notification or notification.alert_id != alert_id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada para la alerta")
    return notification


def ensure_information_source_exists(source_id: int) -> None:
    if source_id not in information_sources_store:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")


def ensure_category_exists(category_id: int) -> None:
    if category_id not in categories_store:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


def ensure_rss_for_source(source_id: int, channel_id: int) -> RSSChannel:
    channel = rss_channels_store.get(channel_id)
    if not channel or channel.information_source_id != source_id:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")
    return channel

# REVISAR RETURS EN CRUD
def sanitize_user(user: UserInDB) -> User:
    return User(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        organization=user.organization,
        role_ids=user.role_ids,
    )


#
# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
# ) -> UserInDB:
#     if credentials is None or credentials.scheme.lower() != "bearer":
#         raise HTTPException(status_code=401, detail="Token inválido o ausente")
#
#     user_id = active_tokens.get(credentials.credentials)
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Token inválido o expirado")
#
#     user = users_store.get(user_id)
#     if not user:
#         raise HTTPException(status_code=401, detail="Usuario inválido")
#
#     return user


def create_seed_data() -> None:
    db = SessionLocal()
    try:
        # Comprobamos si ya existen roles para no duplicarlos
        if not db.query(models.Role).first():
            roles = [models.Role(name="Admin"), models.Role(name="Gestor"), models.Role(name="Lector")]
            db.add_all(roles)
            db.commit()

        # Comprobamos si existe el usuario admin inicial
        admin_user = db.query(models.User).filter(models.User.email == "admin@newsradar.com").first()
        if not admin_user:
            admin_role = db.query(models.Role).filter(models.Role.name == "Admin").first()
            hashed_pwd = get_password_hash("admin123")  # Contraseña por defecto

            new_admin = models.User(
                email="admin@newsradar.com",
                first_name="Admin",
                last_name="NewsRadar",
                organization="NewsRadar",
                hashed_password=hashed_pwd,
                is_verified=True,  # El admin ya nace verificado
            )
            new_admin.roles.append(admin_role)
            db.add(new_admin)
            db.commit()
    finally:
        db.close()
        
def load_seed_data():
    """Lee el JSON e inserta fuentes y canales si no existen."""
    db = SessionLocal()
    try:
        # Solo insertamos si la tabla de fuentes está vacía
        if not db.query(models.Source).first():
            
            base_dir = Path(__file__).resolve().parent
            seed_file = base_dir / "data" / "rss_seed.json"
            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                for source_data in data:
                    new_source = models.Source(
                        name=source_data["source_name"],
                        description=source_data.get("description", "")
                    )
                    db.add(new_source)
                    db.flush() # Para obtener el ID de la fuente inmediatamente
                    
                    for channel_data in source_data["channels"]:
                        new_channel = models.RssChannel(
                            source_id=new_source.id,
                            name=channel_data["name"],
                            url=channel_data["url"],
                            category=channel_data["category"]
                        )
                        db.add(new_channel)
                db.commit()
                print("Semilla de 100 canales cargada correctamente en Postgres.")
    finally:
        db.close()

@app.on_event("startup")
def on_startup() -> None:
    models.Base.metadata.create_all(bind=engine)
    create_seed_data()
    load_seed_data()


@app.get(f"{API_PREFIX}/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@app.post(f"{API_PREFIX}/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    # 3. Verificar si ha activado la cuenta
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Cuenta no verificada. Por favor, revisa tu correo electrónico."
    #     )

    user_roles = [role.name for role in user.roles]

    token_data = {"sub": user.email, "roles": user_roles}
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post(f"{API_PREFIX}/auth/register", response_model=User, status_code=201, tags=["auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    # 1. Comprobar si el email ya existe en PostgreSQL
    db_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if db_user:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # 2. Encriptar la contraseña
    hashed_password = get_password_hash(payload.password)

    # 3. Crear el nuevo usuario (por defecto le damos el rol Lector)
    new_user = models.User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        organization=payload.organization,
        hashed_password=hashed_password,
        is_verified=False,  # Debe verificar su email con Mailtrap
    )

    # Asignar rol "Lector" por defecto
    lector_role = db.query(models.Role).filter(models.Role.name == "Lector").first()
    if lector_role:
        new_user.roles.append(lector_role)

    # 4. Guardar en base de datos
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, token)

    # 5. Mapear al esquema Pydantic de salida
    return new_user


# NUEVO ENDPOINT PARA VERIFICAR CUENTA CON TOKEN
@app.get(f"{API_PREFIX}/auth/verify", tags=["auth"])
def verify_email(token: str, db: Session = Depends(get_db)):
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
    except JWTError:
        raise credentials_exception from None

    # Buscamos al usuario en la BD
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception from None

    if user.is_verified:
        return {"msg": "El usuario ya estaba verificado"}

    # Actualizamos el estado a verificado
    user.is_verified = True
    db.commit()

    return {"msg": "Cuenta verificada con éxito. Ya puedes iniciar sesión."}


# NUEVO ENDPOINT PARA OBTENR DATOS DEL USUARIO LOGUEADO
@app.get(f"{API_PREFIX}/users/me", tags=["users"], response_model=User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Devuelve los datos del usuario logueado."""
    return current_user


# CRUD USUARIOS


@app.get(f"{API_PREFIX}/users", response_model=list[User], tags=["users"])
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),  # Bloqueado solo para Admins
) -> list[User]:
    return db.query(models.User).all()


@app.post(f"{API_PREFIX}/users", response_model=User, status_code=201, tags=["users"])
def create_user(
    payload: UserCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)
) -> User:
    # 1. Verificar colisión de emails
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # 2. Reemplazo de `ensure_role_ids_exist` en BD real
    roles = db.query(models.Role).filter(models.Role.id.in_(payload.role_ids)).all()
    if len(roles) != len(payload.role_ids):
        raise HTTPException(status_code=404, detail="Uno o más roles no existen")

    # 3. Preparar el usuario (Hasheando la contraseña)
    hashed_pwd = get_password_hash(payload.password)
    user_data = payload.model_dump(exclude={"password", "role_ids"})

    user_db = models.User(**user_data, hashed_password=hashed_pwd)
    user_db.roles = roles  # Asignamos la relación many-to-many de roles

    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    return user_db


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)) -> User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def update_user(
    user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)
) -> User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = payload.model_dump(exclude_unset=True)

    # Verificar colisión de email si se intenta cambiar
    if "email" in data:
        email_collision = (
            db.query(models.User).filter(models.User.email == data["email"], models.User.id != user_id).first()
        )
        if email_collision:
            raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Actualizar roles si vienen en el payload
    # if "role_ids" in data:
    #     roles = db.query(models.Role).filter(models.Role.id.in_(data["role_ids"])).all()
    #     if len(roles) != len(data["role_ids"]):
    #          raise HTTPException(status_code=404, detail="Uno o más roles no existen")
    #     user.roles = roles
    #     del data["role_ids"]

    # Actualizar contraseña si viene en el payload
    if "password" in data:
        user.hashed_password = get_password_hash(data["password"])
        del data["password"]

    if "role_ids" in data:
        roles = db.query(models.Role).filter(models.Role.id.in_(data["role_ids"])).all()
        if len(roles) != len(data["role_ids"]):
            raise HTTPException(status_code=404, detail="Uno o más roles no existen")
        user.roles = roles
        data.pop("role_ids", None)

    # Actualizar el resto de campos dinámicamente
    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["users"],
)
def delete_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)) -> None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Nota sobre el borrado en cascada:
    # Al usar PostgreSQL + SQLAlchemy, si tus modelos (Alerts, Notifications)
    # tienen configurado el borrado en cascada (ondelete="CASCADE"),
    # la base de datos se encarga automáticamente de borrar todo lo asociado a este usuario.
    db.delete(user)
    db.commit()


# --- FIN CRUD USUARIOS

# --- CRUD ROLES


@app.get(f"{API_PREFIX}/roles", response_model=list[Role], tags=["roles"])
def list_roles(db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)) -> list[Role]:
    return db.query(models.Role).all()


@app.post(f"{API_PREFIX}/roles", response_model=Role, status_code=201, tags=["roles"])
def create_role(
    payload: RoleCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)
) -> Role:
    # verificar si ya existe un rol con ese nombre para evitar duplicados
    if db.query(models.Role).filter(models.Role.name == payload.name).first():
        raise HTTPException(status_code=409, detail="El rol ya existe")

    new_role = models.Role(**payload.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def get_role(role_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)) -> Role:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def update_role(
    role_id: int, payload: RoleUpdate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)
) -> Role:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return role


@app.delete(
    f"{API_PREFIX}/roles/{{role_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["roles"],
)
def delete_role(role_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)) -> None:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # Respetamos tu lógica de evitar borrar roles en uso.
    # Comprobamos si hay algún usuario que tenga este rol asignado.
    users_with_role = db.query(models.User).filter(models.User.roles.any(id=role_id)).first()
    if users_with_role:
        raise HTTPException(status_code=409, detail="No se puede eliminar un rol asignado a usuarios")

    db.delete(role)
    db.commit()


# --- FIN CRUD ROLES
# --- CRUD USER ALERTS

@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=list[Alert],
    tags=["alerts"],
)
def list_user_alerts(user_id: int, db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)) -> list[Alert]:
    ensure_user_exists(user_id, db)

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para ver las alertas de otro usuario."
        )

    # Buscamos en PostgreSQL todas las alertas de este usuario
    alerts = db.query(models.Alert).filter(models.Alert.user_id == user_id).all()
    return alerts


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts",
    response_model=Alert,
    status_code=201,
    tags=["alerts"],
)
def create_user_alert(
        user_id: int, payload: AlertCreate, current_user: UserInDB = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Alert:
    ensure_user_exists(user_id, db)

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para crear alertas para otro usuario."
        )

    # Validar límite de 20 alertas
    current_alerts_count = db.query(models.Alert).filter(models.Alert.user_id == user_id).count()
    if current_alerts_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Límite máximo de 20 alertas alcanzado."
        )

    # Validar regla de negocio: entre 3 y 10 descriptores (vienen del payload)
    if len(payload.descriptors) < 3 or len(payload.descriptors) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La alerta debe tener entre 3 y 10 descriptores (sinónimos)."
        )

    # Creación en PostgreSQL asumiendo que models.Alert tiene columnas JSON 
    # para descriptors y categories
    new_alert = models.Alert(
        user_id=user_id,
        name=payload.name,
        cron_expression=payload.cron_expression,
        descriptors=payload.descriptors,
        categories=[cat.model_dump() for cat in payload.categories] # Si categories es una lista de Pydantic models
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return new_alert


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def get_user_alert(
    user_id: int, alert_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> Alert:
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    ) -> Alert:
    ensure_user_exists(user_id, db)
    
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    alert = db.query(models.Alert).filter(models.Alert.id == alert_id, models.Alert.user_id == user_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada.")

    # Actualizamos dinámicamente los campos que vengan en el payload
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alert, key, value)

    db.commit()
    db.refresh(alert)
    return alert


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["alerts"],
)
def delete_user_alert(user_id: int, alert_id: int, db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)) -> None:
    ensure_user_exists(user_id, db)
    
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    alert = db.query(models.Alert).filter(models.Alert.id == alert_id, models.Alert.user_id == user_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada.")

    # Al borrar la alerta en BD, si las notificaciones tienen ON DELETE CASCADE, se borrarán solas.
    # Si no, tendrías que borrarlas manualmente aquí antes de borrar la alerta.
    db.delete(alert)
    db.commit()
    
# --- CRUD USER ALERTS
# --- CRUD USER ALERTS NOTIFICATIONS

@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=list[Notification],
    tags=["notifications"],
)
def list_alert_notifications(
    user_id: int,
    alert_id: int,
    _: UserInDB = Depends(get_current_user),
) -> list[Notification]:
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
    ensure_alert_for_user(user_id, alert_id)
    ensure_notification_for_alert(alert_id, notification_id)
    notifications_store.pop(notification_id, None)
# --- FIN CRUD USER ALERTS NOTIFICATIONS
# --- CRUD CATEGORIES

@app.get(f"{API_PREFIX}/categories", response_model=list[Category], tags=["categories"])
def list_categories(_: UserInDB = Depends(get_current_user)) -> list[Category]:
    return list(categories_store.values())


@app.post(f"{API_PREFIX}/categories", response_model=Category, status_code=201, tags=["categories"])
def create_category(payload: CategoryCreate, _: UserInDB = Depends(get_current_user)) -> Category:
    category_id = next_id("categories")
    category = Category(id=category_id, **payload.model_dump())
    categories_store[category_id] = category
    return category


@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def get_category(category_id: int, _: UserInDB = Depends(get_current_user)) -> Category:
    category = categories_store.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@app.put(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def update_category(category_id: int, payload: CategoryUpdate, _: UserInDB = Depends(get_current_user)) -> Category:
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
    if category_id not in categories_store:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for channel in rss_channels_store.values():
        if channel.category_id == category_id:
            raise HTTPException(status_code=409, detail="Categoría asociada a canales RSS")

    categories_store.pop(category_id, None)
# --- FIN CRUD CATEGORIES
# --- CRUD INFORMATION SOURCES Y RSS CHANNELS

@app.get(
    f"{API_PREFIX}/information-sources",
    response_model=list[InformationSource],
    tags=["information-sources"],
)
def list_information_sources(_: UserInDB = Depends(get_current_user)) -> list[InformationSource]:
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
    if source_id not in information_sources_store:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel_ids = [channel.id for channel in rss_channels_store.values() if channel.information_source_id == source_id]
    for channel_id in channel_ids:
        rss_channels_store.pop(channel_id, None)

    information_sources_store.pop(source_id, None)
# --- FIN CRUD INFORMATION SOURCES
# --- CRUD RSS CHANNELS

@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=list[RSSChannel],
    tags=["rss-channels"],
)
def list_source_channels(source_id: int, _: UserInDB = Depends(get_current_user)) -> list[RSSChannel]:
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
    ensure_information_source_exists(source_id)
    ensure_rss_for_source(source_id, channel_id)
    rss_channels_store.pop(channel_id, None)
# --- FIN CRUD RSS CHANNELS
# --- CRUD STATS


@app.get(f"{API_PREFIX}/stats", response_model=list[Stats], tags=["stats"])
def list_stats(_: UserInDB = Depends(get_current_user)) -> list[Stats]:
    return list(stats_store.values())


@app.post(f"{API_PREFIX}/stats", response_model=Stats, status_code=201, tags=["stats"])
def create_stats(payload: StatsCreate, _: UserInDB = Depends(get_current_user)) -> Stats:
    stats_id = next_id("stats")
    stats = Stats(id=stats_id, **payload.model_dump())
    stats_store[stats_id] = stats
    return stats


@app.get(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def get_stats(stats_id: int, _: UserInDB = Depends(get_current_user)) -> Stats:
    stats = stats_store.get(stats_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    return stats


@app.put(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def update_stats(stats_id: int, payload: StatsUpdate, _: UserInDB = Depends(get_current_user)) -> Stats:
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
    if stats_id not in stats_store:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    stats_store.pop(stats_id, None)
# --- FIN CRUD STATS