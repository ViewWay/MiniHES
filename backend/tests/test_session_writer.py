"""session_writer 纯函数测试。

测试 _derive_status、_map_status、_parse_timestamp 等纯函数，
不连接真实 MongoDB 或 PostgreSQL。
"""

import datetime

from app.services.collector.session_writer import (
    _derive_status,
    _map_status,
    _parse_timestamp,
)

# ─── _derive_status 测试 ───


def test_derive_status_all_success():
    """全部成功 → success。"""
    assert _derive_status(total_read=796, total_failed=0) == "success"


def test_derive_status_partial():
    """部分失败 → partial。"""
    assert _derive_status(total_read=796, total_failed=2) == "partial"


def test_derive_status_all_failed():
    """全部失败 → failed。"""
    assert _derive_status(total_read=796, total_failed=796) == "failed"


def test_derive_status_zero_read():
    """无读数 → failed。"""
    assert _derive_status(total_read=0, total_failed=0) == "failed"


# ─── _map_status 测试 ───


def test_map_status_success_to_completed():
    """Mongo success → PG completed。"""
    assert _map_status("success") == "completed"


def test_map_status_partial_to_completed():
    """Mongo partial → PG completed。"""
    assert _map_status("partial") == "completed"


def test_map_status_failed_to_failed():
    """Mongo failed → PG failed。"""
    assert _map_status("failed") == "failed"


# ─── _parse_timestamp 测试 ───


def test_parse_timestamp_valid():
    """有效 ISO 时间戳。"""
    ts = "2025-11-01T09:33:56.512413"
    result = _parse_timestamp(ts)
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 1


def test_parse_timestamp_none():
    """None 输入返回当前时间（不 crash）。"""
    result = _parse_timestamp(None)
    assert isinstance(result, datetime.datetime)


def test_parse_timestamp_empty():
    """空字符串返回当前时间。"""
    result = _parse_timestamp("")
    assert isinstance(result, datetime.datetime)


def test_parse_timestamp_invalid():
    """无效字符串返回当前时间。"""
    result = _parse_timestamp("not-a-timestamp")
    assert isinstance(result, datetime.datetime)


def test_parse_timestamp_with_timezone():
    """带时区的 ISO 时间戳。"""
    ts = "2025-11-01T09:33:56+00:00"
    result = _parse_timestamp(ts)
    assert result.year == 2025
    assert result.month == 11
