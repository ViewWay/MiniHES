from app.core.response import success, error, ok, created, fail


def test_success_format():
    result = success({"id": 1})
    assert result["code"] == 0
    assert result["data"]["id"] == 1
    assert result["message"] == "ok"


def test_error_format():
    result = error("not found")
    assert result["code"] == -1
    assert result["error"] == "not found"


def test_ok_response():
    resp = ok(data={"id": 1}, message="success")
    body = resp.body
    assert resp.status_code == 200
    assert b'"code":200' in body
    assert b'"id":1' in body


def test_created_response():
    resp = created(data={"id": 2})
    assert resp.status_code == 201


def test_fail_response():
    resp = fail(code=10002, message="error", status=400)
    assert resp.status_code == 400
