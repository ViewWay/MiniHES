"""MongoSessionRepo buffer 解析逻辑测试。

这些测试只验证纯函数解析逻辑（不连接真实 MongoDB），
使用 dict mock 模拟 Mongo 返回的文档结构。
"""

from app.services.mongo_session_repo import MongoSessionRepo

# ─── 测试数据 ───

_MOCK_DAILY_BILLING_DOC = {
    "key_value_pairs": {
        "Daily Billing.E-meter Daily Billing.Buffer": {
            "0": ["2024-06-01 6 00:00:00 00,FF88,80", 120, 50320, 0, 0, 0],
            "1": ["2024-06-02 7 00:00:00 00,FF88,80", 150, 50470, 10, 0, 0],
            "2": ["2024-06-03 1 00:00:00 00,FF88,80", 130, 50600, 0, 5, 0],
        }
    }
}

_MOCK_LOAD_PROFILE_DOC = {
    "key_value_pairs": {
        "Load Profile.Energy Profile.Buffer": {
            "0": ["2024-06-15 6 00:00:00 00,FF88,80", 8, 50000, 0],
            "1": ["2024-06-15 6 00:15:00 00,FF88,80", 8, 50042, 0],
            "2": ["2024-06-15 6 00:30:00 00,FF88,80", 8, 50085, 0],
        }
    }
}

_MOCK_INSTANTANEOUS_DOC = {
    "key_value_pairs": {
        "Instantaneous Data.Instantaneous Voltage L1.Value": 231,
        "Instantaneous Data.Instantaneous Voltage L2.Value": 229,
        "Instantaneous Data.Instantaneous Current L1.Value": 12,
        "Instantaneous Data.Instantaneous active power (+P) Total.Value": 320,
        "Clock.Clock.Time": "2025-11-10 01 15:38:38 00,FFC4,00",  # 非瞬时，应被过滤
    }
}


# ─── _parse_daily_billing_buffer 测试 ───


def test_parse_daily_billing_basic():
    """解析 3 天日线数据，取最近 2 天。"""
    result = MongoSessionRepo._parse_daily_billing_buffer(_MOCK_DAILY_BILLING_DOC, days=2)
    assert len(result) == 2
    # 按最近排序（index 倒序）
    assert result[0]["index"] == 2
    assert result[1]["index"] == 1
    # 验证字段
    assert result[0]["cumulative_energy"] == 50600
    assert result[0]["rate1"] == 0
    assert result[0]["rate2"] == 5


def test_parse_daily_billing_all_days():
    """取全部天数。"""
    result = MongoSessionRepo._parse_daily_billing_buffer(_MOCK_DAILY_BILLING_DOC, days=30)
    assert len(result) == 3


def test_parse_daily_billing_empty():
    """无 Daily Billing buffer 时返回空列表。"""
    result = MongoSessionRepo._parse_daily_billing_buffer({}, days=30)
    assert result == []


def test_parse_daily_billing_no_kvp():
    """key_value_pairs 为空时返回空列表。"""
    result = MongoSessionRepo._parse_daily_billing_buffer({"key_value_pairs": {}}, days=30)
    assert result == []


def test_parse_daily_billing_short_entries():
    """buffer 条目长度不足 3 时跳过。"""
    doc = {
        "key_value_pairs": {
            "Daily Billing.E-meter Daily Billing.Buffer": {
                "0": ["only_timestamp"],  # 长度 1，应跳过
                "1": ["ts", 120, 50000],  # 长度 3，应保留
            }
        }
    }
    result = MongoSessionRepo._parse_daily_billing_buffer(doc, days=10)
    assert len(result) == 1
    assert result[0]["index"] == 1


# ─── _parse_load_profile_buffer 测试 ───


def test_parse_load_profile_basic():
    """解析 3 点负荷曲线。"""
    result = MongoSessionRepo._parse_load_profile_buffer(_MOCK_LOAD_PROFILE_DOC)
    assert len(result) == 3
    # 验证时间槽
    assert result[0]["time_slot"] == "00:00"
    assert result[1]["time_slot"] == "00:15"
    assert result[2]["time_slot"] == "00:30"
    # 验证增量计算
    assert result[0]["interval_delta"] == 0  # 第一个点无前值
    assert result[1]["interval_delta"] == 42  # 50042 - 50000
    assert result[2]["interval_delta"] == 43  # 50085 - 50042


def test_parse_load_profile_empty():
    """无 Load Profile buffer 时返回空列表。"""
    result = MongoSessionRepo._parse_load_profile_buffer({})
    assert result == []


def test_parse_load_profile_sorted_by_index():
    """buffer 按 index 排序输出。"""
    doc = {
        "key_value_pairs": {
            "Load Profile.Energy Profile.Buffer": {
                "2": ["ts2", 8, 200, 0],
                "0": ["ts0", 8, 100, 0],
                "1": ["ts1", 8, 150, 0],
            }
        }
    }
    result = MongoSessionRepo._parse_load_profile_buffer(doc)
    assert len(result) == 3
    assert result[0]["index"] == 0
    assert result[1]["index"] == 1
    assert result[2]["index"] == 2


# ─── _parse_instantaneous 测试 ───


def test_parse_instantaneous_basic():
    """解析瞬时量字典。"""
    result = MongoSessionRepo._parse_instantaneous(_MOCK_INSTANTANEOUS_DOC)
    assert "Instantaneous Voltage L1" in result
    assert result["Instantaneous Voltage L1"] == 231
    assert result["Instantaneous Voltage L2"] == 229
    assert result["Instantaneous Current L1"] == 12
    assert result["Instantaneous active power (+P) Total"] == 320


def test_parse_instantaneous_filters_non_value():
    """非 .Value 结尾的 key 被过滤。"""
    result = MongoSessionRepo._parse_instantaneous(_MOCK_INSTANTANEOUS_DOC)
    # Clock.Clock.Time 不是 Instantaneous Data 且不以 .Value 结尾，不应出现
    assert "Clock.Time" not in result
    assert "Time" not in result


def test_parse_instantaneous_empty():
    """空 key_value_pairs 返回空字典。"""
    assert MongoSessionRepo._parse_instantaneous({}) == {}
    assert MongoSessionRepo._parse_instantaneous({"key_value_pairs": {}}) == {}


# ─── 投影常量测试 ───


def test_projection_constants_exist():
    """验证投影常量定义。"""
    assert "meter_id" in MongoSessionRepo.PROJ_META
    assert "key_value_pairs" in MongoSessionRepo.PROJ_DAILY
    assert "key_value_pairs" in MongoSessionRepo.PROJ_LOAD_PROFILE
    assert "key_value_pairs" in MongoSessionRepo.PROJ_INSTANTANEOUS


def test_collection_name():
    """验证集合名。"""
    assert MongoSessionRepo.COLLECTION == "meter_sessions"
