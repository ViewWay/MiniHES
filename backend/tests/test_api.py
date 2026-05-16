from starlette.testclient import TestClient


def test_login_success(client: TestClient):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "123456"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["username"] == "admin"
    assert "accessToken" in data


def test_login_wrong_password(client: TestClient):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_login_validation(client: TestClient):
    r = client.post("/api/v1/auth/login", json={"username": "", "password": ""})
    assert r.status_code == 422


def test_unauthorized_access(client: TestClient):
    r = client.get("/api/v1/auth/codes")
    assert r.status_code == 403


def test_get_codes(client: TestClient, auth_headers):
    r = client.get("/api/v1/auth/codes", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_list_users(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/users", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1


def test_list_roles(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/roles", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1


def test_list_departments(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/dept/list", headers=auth_headers)
    assert r.status_code == 200


def test_list_audit_logs(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/audit-logs", headers=auth_headers)
    assert r.status_code == 200


def test_system_health(client: TestClient):
    r = client.get("/api/v1/system/health")
    assert r.status_code == 200


def test_list_projects(client: TestClient, auth_headers):
    r = client.get("/api/v1/projects", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1


def test_get_project(client: TestClient, auth_headers):
    r = client.get("/api/v1/projects/1", headers=auth_headers)
    assert r.status_code == 200


def test_404_json_format(client: TestClient):
    r = client.get("/api/v1/nonexistent")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == 404
    assert body["data"] is None
