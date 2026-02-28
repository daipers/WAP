import os
from typing import Any, Optional

from sqlalchemy import Column, String, func, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


# Database configuration from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
)
DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY", "dev-encryption-key-must-be-changed")

# SQLAlchemy async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class PGcryptoString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for transparent PII handling using pgcrypto.
    Uses pgp_sym_encrypt and pgp_sym_decrypt for symmetric encryption in PostgreSQL.
    """

    impl = String
    cache_ok = False

    def bind_expression(self, bindvalue: Any) -> Any:
        """
        Wrap the value in pgp_sym_encrypt when inserting or updating.
        """
        return func.pgp_sym_encrypt(bindvalue, DB_ENCRYPTION_KEY)

    def column_expression(self, col: Any) -> Any:
        """
        Wrap the column in pgp_sym_decrypt when selecting.
        """
        return func.pgp_sym_decrypt(col, DB_ENCRYPTION_KEY)


async def get_db():
    """Dependency for getting an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
