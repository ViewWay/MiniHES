"""alarm_engine 纯函数测试。

测试 _eval_threshold 阈值评估逻辑，不连接数据库。
"""

from app.services.alarm_engine import _eval_threshold

# ─── 阈值评估 ───


def test_threshold_gt_triggered():
    """大于阈值触发。"""
    triggered, val, msg = _eval_threshold(250.0, {"operator": "gt", "value": 240.0}, "电压告警")
    assert triggered is True
    assert val == 240.0
    assert "250.00" in msg
    assert "240.00" in msg
    assert ">" in msg


def test_threshold_gt_not_triggered():
    """未超阈值不触发。"""
    triggered, val, msg = _eval_threshold(230.0, {"operator": "gt", "value": 240.0}, "电压告警")
    assert triggered is False


def test_threshold_lt_triggered():
    """小于阈值触发。"""
    triggered, val, msg = _eval_threshold(180.0, {"operator": "lt", "value": 200.0}, "低压告警")
    assert triggered is True
    assert "180.00" in msg
    assert "200.00" in msg
    assert "<" in msg


def test_threshold_gte_triggered():
    """大于等于触发（边界值）。"""
    triggered, _, _ = _eval_threshold(240.0, {"operator": "gte", "value": 240.0}, "电压告警")
    assert triggered is True


def test_threshold_lte_triggered():
    """小于等于触发（边界值）。"""
    triggered, _, _ = _eval_threshold(200.0, {"operator": "lte", "value": 200.0}, "电压告警")
    assert triggered is True


def test_threshold_eq_triggered():
    """等于触发。"""
    triggered, _, _ = _eval_threshold(100.0, {"operator": "eq", "value": 100.0}, "精确告警")
    assert triggered is True


def test_threshold_no_value():
    """config 无 value 字段时不触发。"""
    triggered, val, msg = _eval_threshold(250.0, {"operator": "gt"}, "电压告警")
    assert triggered is False
    assert val is None


def test_threshold_empty_config():
    """空 config 不触发。"""
    triggered, val, msg = _eval_threshold(250.0, {}, "电压告警")
    assert triggered is False


def test_threshold_message_format():
    """告警消息格式正确。"""
    triggered, val, msg = _eval_threshold(250.5, {"operator": "gt", "value": 240.0}, "电压越限")
    assert "电压越限" in msg
    assert "250.50" in msg
    assert "240.00" in msg
