"""RBAC 接口级权限强制测试。

测试矩阵：
  - admin（super+admin 角色）：所有受保护接口 200（super 豁免）
  - engineer（admin 角色，全部菜单权限）：受保护接口 200
  - tester（user 角色，仅 dashboard+devices）：devices 接口 200，tasks 接口 403
  - 无 token：受保护接口 403
"""

import pytest
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures：tester 用户 token（低权限，仅 dashboard+devices）
# ---------------------------------------------------------------------------


@pytest.fixture
def tester_token(client: TestClient) -> str:
    r = client.post("/api/v1/auth/login", json={"username": "tester", "password": "123456"})
    assert r.status_code == 200
    return r.json()["data"]["accessToken"]


@pytest.fixture
def tester_headers(tester_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {tester_token}"}


@pytest.fixture
def engineer_token(client: TestClient) -> str:
    r = client.post("/api/v1/auth/login", json={"username": "engineer", "password": "123456"})
    assert r.status_code == 200
    return r.json()["data"]["accessToken"]


@pytest.fixture
def engineer_headers(engineer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {engineer_token}"}


# ---------------------------------------------------------------------------
# 测试 1：admin（super 角色）可访问 devices 接口
# ---------------------------------------------------------------------------


def test_admin_can_access_devices(client: TestClient, auth_headers):
    """admin 有 super 角色，应豁免权限检查。"""
    r = client.get("/api/v1/meters", headers=auth_headers)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# 测试 2：engineer（admin 角色，全部菜单权限）可访问 tasks 接口
# ---------------------------------------------------------------------------


def test_engineer_can_access_tasks(client: TestClient, engineer_headers):
    """engineer 有 admin 角色（全部菜单权限），应能访问 tasks。"""
    r = client.get("/api/v1/tasks", headers=engineer_headers)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# 测试 3：tester（user 角色，无 tasks 权限）访问 tasks 返回 403
# ---------------------------------------------------------------------------


def test_tester_denied_tasks(client: TestClient, tester_headers):
    """tester 仅有 dashboard+devices 权限，访问 tasks 应 403。"""
    r = client.get("/api/v1/tasks", headers=tester_headers)
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == 403


# ---------------------------------------------------------------------------
# 测试 4：tester 有 devices 权限，可访问 meters 接口
# ---------------------------------------------------------------------------


def test_tester_can_access_devices(client: TestClient, tester_headers):
    """tester 有 devices 权限，应能访问 meters。"""
    r = client.get("/api/v1/meters", headers=tester_headers)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# 测试 5：tester 无 system 权限，访问 system 接口返回 403
# ---------------------------------------------------------------------------


def test_tester_denied_system(client: TestClient, tester_headers):
    """tester 无 system 权限，访问 system 接口应 403。"""
    r = client.get("/api/v1/system/users", headers=tester_headers)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# 测试 6：无 token 访问受保护接口返回 403
# ---------------------------------------------------------------------------


def test_no_token_denied(client: TestClient):
    """无 token 访问受保护接口应 403（HTTPBearer auto_error）。"""
    r = client.get("/api/v1/meters")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# 测试 7：公开接口不需要 token（health）
# ---------------------------------------------------------------------------


def test_public_endpoints_no_token_ok(client: TestClient):
    """health 是公开接口，无 token 也应可访问。"""
    r = client.get("/api/v1/health")
    assert r.status_code == 200
