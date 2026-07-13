from starlette.testclient import TestClient


def test_list_meters(client: TestClient, auth_headers):
    r = client.get("/api/v1/meters", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()["data"]
    assert "items" in body
    assert "total" in body


def test_get_meter(client: TestClient, auth_headers):
    r = client.get("/api/v1/meters/1", headers=auth_headers)
    assert r.status_code == 200


def test_list_meters_with_filters(client: TestClient, auth_headers):
    r = client.get(
        "/api/v1/meters?status=in_use&page=1&page_size=5",
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_create_and_delete_meter(client: TestClient, auth_headers):
    meter_id = None
    try:
        cr = client.post(
            "/api/v1/meters",
            json={
                "serial_number": "TEST-METER-DELETE",
                "meter_name": "测试删除仪表",
            },
            headers=auth_headers,
        )
        assert cr.status_code == 200
        meter_id = cr.json()["data"]["id"]

        dr = client.delete(f"/api/v1/meters/{meter_id}", headers=auth_headers)
        assert dr.status_code == 200
        meter_id = None
    except Exception:
        if meter_id is not None:
            try:
                client.delete(f"/api/v1/meters/{meter_id}", headers=auth_headers)
            except Exception:
                pass
        raise


def test_meter_detail_has_snapshot(client: TestClient, auth_headers):
    r = client.get("/api/v1/meters/1", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()["data"]
    assert "snapshot" in body
