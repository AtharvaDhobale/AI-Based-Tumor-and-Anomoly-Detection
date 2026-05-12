from __future__ import annotations

from conftest import auth_header


def _register_token(client) -> str:
    reg = client.post(
        "/api/auth/register",
        json={"email": "doc2@example.com", "full_name": "Dr. Two", "password": "pass1234"},
    )
    assert reg.status_code == 200
    return reg.json()["access_token"]


def test_dashboard_and_assistant_empty(client):
    token = _register_token(client)
    dash = client.get("/api/mri/dashboard/P001", headers=auth_header(token))
    assert dash.status_code == 200
    data = dash.json()
    assert data["patient_id"] == "P001"
    assert data["upload_count"] == 0

    summary = client.get("/api/mri/assistant-summary/P001", headers=auth_header(token))
    assert summary.status_code == 200
    s = summary.json()
    assert "summary_text" in s
    assert "risk_level" in s

