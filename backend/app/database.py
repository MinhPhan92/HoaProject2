import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# Nạp biến môi trường từ .env nếu có
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Mặc định: Postgres local; cập nhật trong .env nếu khác
    "postgresql+psycopg2://postgres:Phan-MinH:9zZ@localhost:5432/Car_rental",
)


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


