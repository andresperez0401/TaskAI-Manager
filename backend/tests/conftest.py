import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test settings BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["AI_ENABLED"] = "false"
os.environ["AI_PROVIDER"] = "noop"

from app.db import Base, get_db_session
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///./test.db", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(test_engine):
    maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        yield db


@pytest.fixture
def client(session: AsyncSession):
    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
