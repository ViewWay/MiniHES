from starlette.testclient import TestClient


def test_list_tasks(client: TestClient, auth_headers):
    r = client.get("/api/v1/tasks", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()["data"]
    assert "items" in body
    assert "total" in body
    assert "running_count" in body


def test_create_task(client: TestClient, auth_headers):
    r = client.post("/api/v1/tasks", json={
        "task_name": "测试采集任务",
        "task_type": "cron",
        "schedule_config": {"cron": "0 8 * * *"},
        "execution_content": {"meter_ids": [1], "obis_codes": ["1.0.0.0.0.255"]},
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_get_task(client: TestClient, auth_headers):
    r = client.get("/api/v1/tasks/1", headers=auth_headers)
    assert r.status_code == 200


def test_update_task(client: TestClient, auth_headers):
    r = client.put("/api/v1/tasks/1", json={"task_name": "更新任务名"}, headers=auth_headers)
    assert r.status_code == 200


def test_toggle_task(client: TestClient, auth_headers):
    r = client.patch("/api/v1/tasks/1/toggle", json={"is_enabled": False}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["is_enabled"] is False
    r2 = client.patch("/api/v1/tasks/1/toggle", json={"is_enabled": True}, headers=auth_headers)
    assert r2.status_code == 200


def test_execute_task(client: TestClient, auth_headers):
    r = client.post("/api/v1/tasks/1/execute", headers=auth_headers)
    assert r.status_code == 200


def test_get_task_logs(client: TestClient, auth_headers):
    client.post("/api/v1/tasks/1/execute", headers=auth_headers)
    r = client.get("/api/v1/tasks/1/logs", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()["data"]


def test_task_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/tasks", json={}, headers=auth_headers)
    assert r.status_code == 422


def test_delete_task(client: TestClient, auth_headers):
    cr = client.post("/api/v1/tasks", json={
        "task_name": "待删除任务",
        "task_type": "once",
    }, headers=auth_headers)
    task_id = cr.json()["data"]["id"]
    r = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert r.status_code == 200
