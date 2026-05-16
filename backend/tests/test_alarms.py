from starlette.testclient import TestClient


def test_alarm_stats(client: TestClient):
    r = client.get("/api/v1/alarms/stats")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total" in data
    assert "unhandled_count" in data
    assert data["total"] >= 0


def test_list_alarms(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarms", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body["data"]
    assert "total" in body["data"]


def test_list_alarms_with_filters(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarms?severity=critical&page=1&page_size=5", headers=auth_headers)
    assert r.status_code == 200


def test_get_alarm(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarms/1", headers=auth_headers)
    assert r.status_code == 200


def test_get_alarm_not_found(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarms/999999", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"] is None


def test_handle_alarm(client: TestClient, auth_headers):
    r = client.post("/api/v1/alarms/1/handle", json={"handled_by": 1}, headers=auth_headers)
    assert r.status_code == 200


def test_export_alarms(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarms/export", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"


def test_list_alarm_rules(client: TestClient, auth_headers):
    r = client.get("/api/v1/alarm-rules", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()["data"]


def test_create_alarm_rule(client: TestClient, auth_headers):
    r = client.post(
        "/api/v1/alarm-rules",
        json={
            "rule_name": "测试规则",
            "rule_type": "threshold",
            "severity": "warning",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_update_alarm_rule(client: TestClient, auth_headers):
    r = client.put("/api/v1/alarm-rules/1", json={"rule_name": "更新规则"}, headers=auth_headers)
    assert r.status_code == 200


def test_delete_alarm_rule(client: TestClient, auth_headers):
    cr = client.post(
        "/api/v1/alarm-rules",
        json={
            "rule_name": "待删除",
            "rule_type": "communication",
            "severity": "info",
        },
        headers=auth_headers,
    )
    rule_id = cr.json()["data"]["id"]
    r = client.delete(f"/api/v1/alarm-rules/{rule_id}", headers=auth_headers)
    assert r.status_code == 200


def test_alarm_rule_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/alarm-rules", json={}, headers=auth_headers)
    assert r.status_code == 422
