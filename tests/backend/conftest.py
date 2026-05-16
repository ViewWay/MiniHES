import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.core.database import Base

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    from app.core.database import get_db
    from main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client, db_session):
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        username="testadmin",
        name="测试管理员",
        password_hash=get_password_hash("Test123456!"),
        status="active",
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "Test123456!",
    })
    token = resp.json()["data"]["accessToken"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
