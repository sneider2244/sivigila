"""Fixtures compartidas: base de datos de prueba dedicada y cliente HTTP async."""

import asyncio
from collections.abc import AsyncGenerator

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.usuario import RolEnum, Usuario

TEST_DB_URL = "postgresql+asyncpg://sivigila:sivigila@localhost:5432/sivigila_test"

TEST_USERNAME = "docente"
TEST_PASSWORD = "docente123"

test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_db() -> AsyncGenerator:
    async with TestSessionFactory() as session:
        yield session


async def _setup_database() -> None:
    conn = await asyncpg.connect(
        user="sivigila",
        password="sivigila",
        host="localhost",
        port=5432,
        database="sivigila",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'sivigila_test'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE sivigila_test")
    finally:
        await conn.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        session.add(
            Usuario(
                username=TEST_USERNAME,
                hashed_password=get_password_hash(TEST_PASSWORD),
                nombre_completo="Usuario Docente",
                rol=RolEnum.DOCENTE,
                activo=True,
            )
        )
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
def _db_setup() -> None:
    asyncio.run(_setup_database())
    yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


app.dependency_overrides[get_db] = _override_get_db
