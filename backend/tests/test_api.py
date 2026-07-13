import uuid

from starlette.testclient import TestClient


def _unique_sn() -> str:
    """Generate a unique serial number for test isolation."""
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


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


def test_system_health(client: TestClient, auth_headers):
    r = client.get("/api/v1/system/health", headers=auth_headers)
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


# ============================================================
# Meter Management Tests
# ============================================================


class TestMeters:
    """Tests for the meter management module."""

    def test_list_meters(self, client: TestClient, auth_headers):
        r = client.get("/api/v1/meters", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert "items" in body["data"]
        assert "total" in body["data"]

    def test_list_meters_with_filters(self, client: TestClient, auth_headers):
        r = client.get(
            "/api/v1/meters?page=1&page_size=5&keyword=test",
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["total"] >= 0

    def test_create_meter(self, client: TestClient, auth_headers):
        sn = _unique_sn()
        payload = {
            "serial_number": sn,
            "meter_name": "Test Meter",
            "protocol": "DLMS",
            "manufacturer": "TestMfg",
        }
        r = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["serial_number"] == sn
        assert body["data"]["id"] is not None

    def test_create_duplicate_meter_rejected(self, client: TestClient, auth_headers):
        sn = _unique_sn()
        payload = {"serial_number": sn, "meter_name": "Dup Meter"}
        r1 = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        assert r1.status_code == 200
        r2 = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        assert r2.status_code == 409

    def test_get_meter(self, client: TestClient, auth_headers):
        sn = _unique_sn()
        payload = {"serial_number": sn, "meter_name": "Get Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.get(f"/api/v1/meters/{meter_id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["serial_number"] == sn
        assert body["data"]["comm"] is not None

    def test_update_meter(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Before"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.put(
            f"/api/v1/meters/{meter_id}",
            json={"meter_name": "After"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["meter_name"] == "After"

    def test_change_status_valid(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Status Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.post(
            f"/api/v1/meters/{meter_id}/status",
            json={"status": "in_use", "reason": "testing"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["new_status"] == "in_use"

    def test_change_status_invalid_transition(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Status Meter 2"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        client.post(
            f"/api/v1/meters/{meter_id}/status",
            json={"status": "scrapped", "reason": "done"},
            headers=auth_headers,
        )
        r = client.post(
            f"/api/v1/meters/{meter_id}/status",
            json={"status": "in_stock", "reason": "undo"},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_get_status_history(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Hist Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        client.post(
            f"/api/v1/meters/{meter_id}/status",
            json={"status": "in_use", "reason": "deploy"},
            headers=auth_headers,
        )
        r = client.get(
            f"/api/v1/meters/{meter_id}/status-history",
            headers=auth_headers,
        )
        assert r.status_code == 200
        items = r.json()["data"]
        assert len(items) >= 1
        assert items[0]["new_status"] == "in_use"

    def test_export_csv(self, client: TestClient, auth_headers):
        r = client.get("/api/v1/meters/export", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/csv; charset=utf-8"

    def test_update_communication(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Comm Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.put(
            f"/api/v1/meters/{meter_id}/communication",
            json={"host": "192.168.1.100", "port": 4059},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["host"] == "192.168.1.100"

    def test_create_borrow(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Borrow Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.post(
            "/api/v1/meters/borrows",
            json={
                "meter_id": meter_id,
                "borrow_reason": "testing",
                "expected_return_date": "2026-12-31",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["approval_status"] == "pending_department"

    def test_borrow_approval_flow(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Approve Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        br = client.post(
            "/api/v1/meters/borrows",
            json={"meter_id": meter_id, "borrow_reason": "approval test"},
            headers=auth_headers,
        )
        borrow_id = br.json()["data"]["id"]
        r1 = client.post(
            f"/api/v1/borrows/{borrow_id}/approve",
            json={"approved": True},
            headers=auth_headers,
        )
        assert r1.status_code == 200
        assert r1.json()["data"]["approval_status"] == "pending_lab"
        r2 = client.post(
            f"/api/v1/borrows/{borrow_id}/approve",
            json={"approved": True},
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["data"]["approval_status"] == "approved"

    def test_return_borrow(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Return Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        br = client.post(
            "/api/v1/meters/borrows",
            json={"meter_id": meter_id, "borrow_reason": "return test"},
            headers=auth_headers,
        )
        borrow_id = br.json()["data"]["id"]
        client.post(
            f"/api/v1/borrows/{borrow_id}/approve",
            json={"approved": True},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/borrows/{borrow_id}/approve",
            json={"approved": True},
            headers=auth_headers,
        )
        r = client.post(
            f"/api/v1/borrows/{borrow_id}/return",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["approval_status"] == "returned"

    def test_create_repair(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Repair Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.post(
            "/api/v1/meters/repairs",
            json={"meter_id": meter_id, "description": "fix display", "cost": 5000},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "in_progress"

    def test_update_repair(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Repair Meter 2"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        rr = client.post(
            "/api/v1/meters/repairs",
            json={"meter_id": meter_id, "description": "fix board"},
            headers=auth_headers,
        )
        repair_id = rr.json()["data"]["id"]
        r = client.put(
            f"/api/v1/meters/repairs/{repair_id}",
            json={"status": "completed", "cost": 3000},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "completed"
        assert r.json()["data"]["cost"] == 3000

    def test_upload_and_list_attachments(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Attach Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        ur = client.post(
            f"/api/v1/meters/{meter_id}/attachments",
            json={
                "filename": "report.pdf",
                "file_path": "/uploads/report.pdf",
                "size": 1024,
            },
            headers=auth_headers,
        )
        assert ur.status_code == 200
        assert ur.json()["data"]["filename"] == "report.pdf"
        lr = client.get(
            f"/api/v1/meters/{meter_id}/attachments",
            headers=auth_headers,
        )
        assert lr.status_code == 200
        assert len(lr.json()["data"]) >= 1

    def test_upload_invalid_extension(self, client: TestClient, auth_headers):
        payload = {"serial_number": _unique_sn(), "meter_name": "Invalid Meter"}
        cr = client.post("/api/v1/meters", json=payload, headers=auth_headers)
        meter_id = cr.json()["data"]["id"]
        r = client.post(
            f"/api/v1/meters/{meter_id}/attachments",
            json={
                "filename": "malware.exe",
                "file_path": "/uploads/malware.exe",
                "size": 1024,
            },
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_meter_not_found(self, client: TestClient, auth_headers):
        r = client.get("/api/v1/meters/999999", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["data"] is None

    def test_update_nonexistent_meter(self, client: TestClient, auth_headers):
        r = client.put(
            "/api/v1/meters/999999",
            json={"meter_name": "ghost"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_unauthorized_access(self, client: TestClient):
        """RBAC 生效后，无 token 的 GET 和 POST 都应返回 403。"""
        r = client.get("/api/v1/meters")
        assert r.status_code == 403  # GET 需 devices 权限
        r2 = client.post("/api/v1/meters", json={"serial_number": "X", "meter_name": "Y"})
        assert r2.status_code == 403  # POST 同样需要权限
