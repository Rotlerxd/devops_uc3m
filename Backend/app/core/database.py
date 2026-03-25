import os
from typing import Any

from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Configuración de PostgreSQL (Entidades)
# Usamos asyncpg que es el driver asíncrono recomendado para FastAPI
POSTGRES_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://newsradar_admin:super_secret_password@localhost:5432/newsradar_db"
)

engine = create_async_engine(POSTGRES_URL, echo=True)
AsyncSessionLocal: Any = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[assignment]
Base = declarative_base()


# Dependencia para inyectar la sesión de Postgres en los endpoints
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# 2. Configuración de Elasticsearch (Noticias y Analítica)
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
es_client = AsyncElasticsearch(ELASTIC_URL)


async def get_elastic():
    yield es_client
