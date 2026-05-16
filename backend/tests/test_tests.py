from starlette.testclient import TestClient


def test_list_tests(client: TestClient, auth_headers):
    r = client.get("/api/v1/tests", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()["data"]


def test_create_test(client: TestClient, auth_headers):
    r = client.post(
        "/api/v1/tests",
        json={
            "test_name": "接口自动化测试",
            "test_type": "function",
            "project_id": 1,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_get_test(client: TestClient, auth_headers):
    r = client.get("/api/v1/tests/1", headers=auth_headers)
    assert r.status_code == 200


def test_get_test_report(client: TestClient, auth_headers):
    r = client.get("/api/v1/tests/1/report", headers=auth_headers)
    assert r.status_code == 200


def test_test_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/tests", json={}, headers=auth_headers)
    assert r.status_code == 422


def test_list_defects(client: TestClient, auth_headers):
    r = client.get("/api/v1/defects", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()["data"]


def test_create_and_update_defect(client: TestClient, auth_headers):
    cr = client.post(
        "/api/v1/tests/1/defects",
        json={
            "title": "接口测试缺陷",
            "severity": "minor",
        },
        headers=auth_headers,
    )
    assert cr.status_code == 200
    defect_id = cr.json()["data"]["id"]

    r = client.put(f"/api/v1/defects/{defect_id}", json={"status": "resolved"}, headers=auth_headers)
    assert r.status_code == 200
