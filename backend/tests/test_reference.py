import uuid

from starlette.testclient import TestClient


def test_list_meter_types(client: TestClient):
    r = client.get("/api/v1/meter-types")
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 3


def test_list_wire_types(client: TestClient):
    r = client.get("/api/v1/wire-types")
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 3


def test_list_meter_points(client: TestClient):
    r = client.get("/api/v1/meter-points")
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 0  # may be empty depending on seed


def test_create_meter_point(client: TestClient, auth_headers):
    r = client.post(
        "/api/v1/meter-points",
        json={
            "meter_id": 1,
            "obis_code": f"1.0.99.1.{uuid.uuid4().hex[:4]}",
            "point_name": "测试采集点",
            "point_type": "register",
            "unit": "kWh",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_update_meter_point(client: TestClient, auth_headers):
    cr = client.post(
        "/api/v1/meter-points",
        json={
            "meter_id": 1,
            "obis_code": f"UPD-{uuid.uuid4().hex[:6]}",
            "point_name": "更新前",
        },
        headers=auth_headers,
    )
    point_id = cr.json()["data"]["id"]
    r = client.put(f"/api/v1/meter-points/{point_id}", json={"point_name": "更新后"}, headers=auth_headers)
    assert r.status_code == 200


def test_delete_meter_point(client: TestClient, auth_headers):
    cr = client.post(
        "/api/v1/meter-points",
        json={
            "meter_id": 1,
            "obis_code": f"DEL-{uuid.uuid4().hex[:6]}",
            "point_name": "待删除",
        },
        headers=auth_headers,
    )
    point_id = cr.json()["data"]["id"]
    r = client.delete(f"/api/v1/meter-points/{point_id}", headers=auth_headers)
    assert r.status_code == 200


def test_get_menus(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/menu/list", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 1
    assert "sortOrder" in items[0]


def test_get_user_menus(client: TestClient, auth_headers):
    r = client.get("/api/v1/menu/all", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) >= 1


def test_menu_name_exists(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/menu/name-exists?name=仪表盘", headers=auth_headers)
    assert r.status_code == 200


def test_create_project_with_schema(client: TestClient, auth_headers):
    r = client.post(
        "/api/v1/projects",
        json={
            "name": f"Schema测试项目-{uuid.uuid4().hex[:6]}",
            "description": "验证schema",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["data"]["id"] is not None


def test_create_project_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/projects", json={}, headers=auth_headers)
    assert r.status_code == 422


def test_update_project(client: TestClient, auth_headers):
    r = client.put("/api/v1/projects/1", json={"name": "已更新项目"}, headers=auth_headers)
    assert r.status_code == 200


def test_create_department_with_schema(client: TestClient, auth_headers):
    r = client.post(
        "/api/v1/system/dept",
        json={
            "name": "测试部门",
            "code": f"test-dept-{uuid.uuid4().hex[:6]}",
            "sort_order": 10,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_create_department_validation(client: TestClient, auth_headers):
    r = client.post("/api/v1/system/dept", json={}, headers=auth_headers)
    assert r.status_code == 422
