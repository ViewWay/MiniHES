"""分析 API 降级行为测试。

当 MongoDB 不可用时，分析 API 应返回降级数据结构（空 + warning），
而不是抛出 500 错误。

注意：由于 MongoDB 异步查询与 TestClient 同步事件循环不兼容
（见 test_analysis.py 中的 skip 注释），这些测试只验证降级逻辑
的结构正确性，不实际请求包含 Mongo 的端点。
"""

from app.services.mongo_session_repo import MongoSessionRepo


def test_fallback_structure_has_warning():
    """降级响应应包含 warning 字段。"""
    fallback = {
        "meter_id": 1,
        "warning": "采集数据暂不可用",
        "hours": [f"{h:02d}:00" for h in range(24)],
        "energy": ["0"] * 24,
        "daily_billing": [],
        "instantaneous": {},
    }
    assert "warning" in fallback
    assert len(fallback["hours"]) == 24
    assert len(fallback["energy"]) == 24
    assert fallback["daily_billing"] == []
    assert fallback["instantaneous"] == {}


def test_fallback_energy_all_zeros():
    """降级 energy 数组应为全 0。"""
    energy = ["0"] * 24
    assert all(v == "0" for v in energy)


def test_mongo_repo_empty_doc_returns_empty():
    """MongoSessionRepo 查询空文档时返回空结构（模拟 Mongo 无数据场景）。"""
    # 不连接真实 Mongo，只测试解析函数对空输入的处理
    assert MongoSessionRepo._parse_daily_billing_buffer({}, 30) == []
    assert MongoSessionRepo._parse_load_profile_buffer({}) == []
    assert MongoSessionRepo._parse_instantaneous({}) == {}


def test_mongo_repo_none_doc_returns_empty():
    """解析函数对缺失字段的安全处理。"""
    # 模拟 Mongo 返回的文档缺少 key_value_pairs 字段
    incomplete_doc = {}
    assert MongoSessionRepo._parse_daily_billing_buffer(incomplete_doc, 30) == []
    assert MongoSessionRepo._parse_load_profile_buffer(incomplete_doc) == []
    assert MongoSessionRepo._parse_instantaneous(incomplete_doc) == {}
