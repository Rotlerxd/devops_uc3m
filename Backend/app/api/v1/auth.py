from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_gestor, get_current_user
from app.core.database import get_db
from app.core.email import create_verification_token, send_verification_email
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, create_access_token, verify_password
from app.crud.usuario import create_user, get_all_users, get_user_by_email
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

# Creamos el router agrupar estas rutas en la documentación
router = APIRouter()

# Security scheme
security = HTTPBearer()


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Inicia sesión y devuelve un token JWT."""
    # OAuth2PasswordRequestForm usa 'username' por defecto, nosotros le pasaremos el email ahí
    user = await get_user_by_email(db, email=form_data.username)

    # Si el usuario no existe o la contraseña no coincide con el hash... ¡Puerta!
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Si todo es correcto, generamos su pase VIP (Token JWT)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Guardamos en el token su email y su rol para saber quién es en futuras peticiones
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol.value}, expires_delta=access_token_expires
    )

    # Devolvemos el token en el formato estándar que espera FastAPI y los Frontends
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UsuarioCreate,
    background_tasks: BackgroundTasks,  # <-- 1. Lo inyectamos aquí
    db: AsyncSession = Depends(get_db),
):
    """Registra un nuevo usuario y envía el email de verificación."""

    # Comprobamos si el usuario ya existe (esto ya lo tenías)
    user_exists = await get_user_by_email(db, email=user_in.email)
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    # Creamos el usuario en la base de datos
    new_user = await create_user(db, user=user_in)

    # 2. MAGIA: Generamos el token y mandamos la tarea al fondo
    token = create_verification_token(new_user.email)
    background_tasks.add_task(send_verification_email, new_user.email, token)

    return new_user


@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """Devuelve los datos del usuario que está logueado actualmente."""
    return current_user


@router.get("/usuarios", response_model=list[UsuarioResponse])
async def read_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_gestor),  # <-- El muro de seguridad
):
    """
    Endpoint administrativo: Devuelve todos los usuarios del sistema.
    Requiere token JWT válido y rol de GESTOR.
    """
    users = await get_all_users(db)
    return users


@router.get("/verify/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verifica el email de un usuario a partir del token recibido por correo."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace de verificación inválido o caducado"
    )

    try:
        # 1. Desencriptamos el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        # 2. Comprobamos que sea un token de correo y no otra cosa
        if email is None or token_type != "email_verification":
            raise credentials_exception

    except JWTError:
        raise credentials_exception from None

    # 3. Buscamos al usuario
    user = await get_user_by_email(db, email=email)
    if not user:
        raise credentials_exception

    if user.is_verified:
        return {"message": "Tu cuenta ya estaba verificada. ¡Puedes iniciar sesión!"}

    # 4. ¡Actualizamos la base de datos!
    user.is_verified = True
    await db.commit()

    return {"message": "¡Cuenta verificada con éxito! Ya puedes iniciar sesión en NewsRadar."}
