from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- ЗМІНА: Використовуємо SQLite (файл contracts.db створиться сам) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./contracts.db"

# connect_args={"check_same_thread": False} - це обов'язково для SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()