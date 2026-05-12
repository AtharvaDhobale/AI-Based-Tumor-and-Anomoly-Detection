from __future__ import annotations


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True


def test_register_and_login(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "doc@example.com", "full_name": "Dr. Test", "password": "pass1234"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    assert isinstance(token, str) and token

    login = client.post("/api/auth/login", json={"email": "doc@example.com", "password": "pass1234"})
    assert login.status_code == 200
    token2 = login.json()["access_token"]
    assert isinstance(token2, str) and token2

