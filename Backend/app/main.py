from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.alerts import router as alerts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.sources import router as sources_router
from app.api.v1.users import router as users_router
from app.core.database import Base, engine, es_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Lógica de STARTUP (antes del yield) ---
    print("Iniciando pruebas de conexión a bases de datos...")

    # 1. Probar conexión a PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

            print("Verificando y creando tablas en PostgreSQL...")
            await conn.run_sync(Base.metadata.create_all)

        print("Conexión a PostgreSQL exitosa")
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")

    # 2. Probar conexión a Elasticsearch
    try:
        info = await es_client.info()
        print(f"Conexión a Elasticsearch exitosa. Versión del cluster: {info['version']['number']}")
    except Exception as e:
        print(f"Error conectando a Elasticsearch: {e}")

    yield  # Aquí es donde FastAPI se queda corriendo y sirviendo peticiones

    # --- Lógica de SHUTDOWN (después del yield) ---
    print("Apagando servidor: Cerrando conexiones a bases de datos...")
    await engine.dispose()
    await es_client.close()


app = FastAPI(
    title="NEWSRADAR API",
    description="API REST para el sistema de monitorización de noticias NEWSRADAR",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Incluimos los routers de los diferentes módulos
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(sources_router, prefix="/api/v1/sources", tags=["sources"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "NEWSRADAR Backend is running"}


# docker build -t fastapi-backend .
# docker run -p 8000:8000 fastapi-backend

# python -m uvicorn app.main:app --reload
# en \Backend (root)


@app.get("/")
async def root():
    return {"message": "NEWSRADAR Backend is running and connected to databases"}
