def register_and_login(client, email="v1@example.com", timezone="UTC"):
    response = client.post("/auth/register", json={"email": email, "password": "password123", "timezone": timezone})
    assert response.status_code == 201
    login = client.post("/auth/login", data={"username": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health_and_ready_include_operational_status(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200


def test_errors_have_a_consistent_envelope_and_request_id(client):
    response = client.get("/sessions/")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "401"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_account_password_change_and_soft_delete(client):
    headers = register_and_login(client, "lifecycle@example.com", "Asia/Kolkata")
    assert client.get("/auth/me", headers=headers).json()["timezone"] == "Asia/Kolkata"
    assert client.post("/auth/change-password", headers=headers, json={"current_password": "password123", "new_password": "changed-password"}).status_code == 204
    assert client.request("DELETE", "/auth/me", headers=headers, json={"password": "changed-password"}).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_analytics_date_range_filters_completed_sessions(client):
    headers = register_and_login(client, "ranges@example.com")
    for started_at in ("2026-01-01T10:00:00Z", "2026-02-01T10:00:00Z"):
        response = client.post("/sessions/", headers=headers, json={"project_name": "DevLog", "language": "Python", "started_at": started_at, "ended_at": started_at.replace("10:00", "11:00")})
        assert response.status_code == 201
    summary = client.get("/analytics/summary?from=2026-02-01T00:00:00Z&to=2026-02-28T23:59:59Z", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["total_sessions"] == 1
