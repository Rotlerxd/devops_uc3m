import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Si estás en Docker, usa 'db' como host. Si pruebas en local, usa 'localhost'
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://newsradar_user:newsradar_password@localhost:5432/newsradar_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
