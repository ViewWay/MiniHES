import uuid
from starlette.testclient import TestClient


def _unique_code() -> str:
    return f"test_{uuid.uuid4().hex[:6]}"


def test_list_roles(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/role/list", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert data["total"] >= 1


def test_create_role_with_schema(client: TestClient, auth_headers):
    r = client.post("/api/v1/system/roles", json={
        "name": "测试角色",
        "code": _unique_code(),
        "description": "schema验证",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_create_role_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/system/roles", json={}, headers=auth_headers)
    assert r.status_code == 422


def test_update_role_with_schema(client: TestClient, auth_headers):
    cr = client.post("/api/v1/system/roles", json={
        "name": "待更新角色", "code": _unique_code(),
    }, headers=auth_headers)
    assert cr.status_code == 200
    rid = cr.json()["data"]["id"]
    r = client.put(f"/api/v1/system/roles/{rid}", json={"name": "已更新角色"}, headers=auth_headers)
    assert r.status_code == 200


def test_delete_role(client: TestClient, auth_headers):
    cr = client.post("/api/v1/system/roles", json={
        "name": "待删除角色", "code": _unique_code(),
    }, headers=auth_headers)
    assert cr.status_code == 200
    rid = cr.json()["data"]["id"]
    r = client.delete(f"/api/v1/system/roles/{rid}", headers=auth_headers)
    assert r.status_code == 200
