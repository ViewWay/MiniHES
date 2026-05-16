import pytest
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from starlette.testclient import TestClient

import app.core.database as db_mod
from app.core.config import settings
from main import app


@pytest.fixture(autouse=True)
def _isolate_db():
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    db_mod.engine = engine
    db_mod.AsyncSessionLocal = factory
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "123456"})
    return r.json()["data"]["accessToken"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
