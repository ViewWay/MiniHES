import json

from app.core.response import ok, created, fail


def test_ok_response():
    resp = ok(data={"id": 1}, message="success")
    body = json.loads(resp.body)
    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["data"]["id"] == 1


def test_created_response():
    resp = created(data={"id": 2})
    body = json.loads(resp.body)
    assert resp.status_code == 201
    assert body["code"] == 201


def test_fail_response():
    resp = fail(code=10002, message="设备状态不允许此操作", status=400)
    body = json.loads(resp.body)
    assert resp.status_code == 400
    assert body["code"] == 10002
    assert "设备状态不允许此操作" in body["message"]
