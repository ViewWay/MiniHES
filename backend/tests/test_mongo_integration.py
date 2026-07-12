"""MongoDB 集成测试。

需要真实 MongoDB 实例运行。默认跳过，通过环境变量 ``MONGODB_TEST_URL`` 启用：

    MONGODB_TEST_URL=mongodb://localhost:27017 uv run pytest tests/test_mongo_integration.py
"""

import os

import pytest

# 如果没有设置 MONGODB_TEST_URL，跳过所有测试
_MONGO_TEST_URL = os.environ.get("MONGODB_TEST_URL", "")
pytest.importorskip("motor")

pytestmark = pytest.mark.skipif(
    not _MONGO_TEST_URL,
    reason="未设置 MONGODB_TEST_URL 环境变量，跳过 MongoDB 集成测试",
)


@pytest.fixture
async def mongo_repo():
    """创建连接到测试 MongoDB 的 MongoSessionRepo。"""
    from motor.motor_asyncio import AsyncIOMotorClient

    from app.services.mongo_session_repo import MongoSessionRepo

    client = AsyncIOMotorClient(_MONGO_TEST_URL)
    db = client["minihes_test"]

    # 清理测试集合
    await db["meter_sessions"].delete_many({})

    yield MongoSessionRepo(db)

    # 清理
    await db["meter_sessions"].delete_many({})
    client.close()


_TEST_DOC = {
    "meter_id": 999,
    "meter_serial": "TEST_METER_001",
    "project_id": 1,
    "collected_at": "2025-01-01T00:00:00",
    "sheets": {
        "Daily Billing": {
            "objects": [
                {
                    "key": "Daily Billing.E-meter Daily Billing.Buffer",
                    "attributeName": "Buffer",
                    "value": {
                        "0": ["2025-01-01 3 00:00:00 00,FF88,80", 100, 50000, 0, 0, 0],
                    },
                }
            ]
        }
    },
    "key_value_pairs": {
        "Daily Billing.E-meter Daily Billing.Buffer": {
            "0": ["2025-01-01 3 00:00:00 00,FF88,80", 100, 50000, 0, 0, 0],
        },
        "Energy.Cumulative A Positive.Value": 50000,
    },
    "summary": {"total_read": 1, "total_success": 1, "total_failed": 0},
    "schema_version": 1,
}


@pytest.mark.asyncio
async def test_insert_and_retrieve(mongo_repo):
    """测试插入文档并按 doc_id 查回。"""
    doc_id = await mongo_repo.insert_session(_TEST_DOC.copy())
    assert doc_id is not None

    retrieved = await mongo_repo.get_by_doc_id(doc_id)
    assert retrieved is not None
    assert retrieved["meter_id"] == 999


@pytest.mark.asyncio
async def test_get_latest_by_meter(mongo_repo):
    """测试按 meter_id 查最新文档。"""
    await mongo_repo.insert_session(_TEST_DOC.copy())

    latest = await mongo_repo.get_latest_by_meter(999)
    assert latest is not None
    assert latest["meter_id"] == 999


@pytest.mark.asyncio
async def test_get_energy(mongo_repo):
    """测试从 key_value_pairs 提取累计电能。"""
    await mongo_repo.insert_session(_TEST_DOC.copy())

    energy = await mongo_repo.get_energy(999)
    assert energy["cumulative_positive"] == 50000


@pytest.mark.asyncio
async def test_get_daily_billing(mongo_repo):
    """测试提取 Daily Billing buffer。"""
    await mongo_repo.insert_session(_TEST_DOC.copy())

    billing = await mongo_repo.get_daily_billing(999, days=7)
    assert len(billing) == 1
    assert billing[0]["cumulative_energy"] == 50000
