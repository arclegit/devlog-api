def register_and_login(client, email="test@example.com"):
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_session_rejects_invalid_timestamps(client):
    headers = register_and_login(client)

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
            "ended_at": "2026-09-16T14:00:00",
        },
    )

    assert response.status_code == 422


def test_create_active_session_with_no_end_time(client):
    headers = register_and_login(client)

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
            "ended_at": None,
        },
    )

    assert response.status_code == 201
    assert response.json()["ended_at"] is None


def test_update_session_rejects_invalid_end_time(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.patch(
        f"/sessions/{session_id}",
        headers=headers,
        json={
            "ended_at": "2026-09-16T14:00:00",
        },
    )

    assert response.status_code == 422


def test_update_session_rejects_started_time_after_existing_end_time(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
            "ended_at": "2026-09-16T16:00:00",
        },
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.patch(
        f"/sessions/{session_id}",
        headers=headers,
        json={
            "started_at": "2026-09-16T17:00:00",
        },
    )

    assert response.status_code == 422


def test_update_session_accepts_valid_end_time(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.patch(
        f"/sessions/{session_id}",
        headers=headers,
        json={
            "ended_at": "2026-09-16T16:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["ended_at"] is not None

def test_create_session_rejects_empty_project_name(client):
    headers = register_and_login(client, "empty-project@example.com")

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422


def test_create_session_rejects_whitespace_project_name(client):
    headers = register_and_login(client, "whitespace-project@example.com")

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "   ",
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422


def test_create_session_rejects_missing_required_field(client):
    headers = register_and_login(client, "missing-field@example.com")

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422


def test_create_session_rejects_invalid_timestamp_format(client):
    headers = register_and_login(client, "invalid-timestamp@example.com")

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
            "started_at": "not-a-timestamp",
        },
    )

    assert response.status_code == 422

def test_get_nonexistent_session_returns_404(client):
    headers = register_and_login(
        client,
        "nonexistent-session@example.com",
    )

    response = client.get(
        "/sessions/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_nonexistent_session_returns_404(client):
    headers = register_and_login(
        client,
        "update-nonexistent@example.com",
    )

    response = client.patch(
        "/sessions/999999999",
        headers=headers,
        json={
            "description": "Updated",
        },
    )

    assert response.status_code == 404


def test_delete_nonexistent_session_returns_404(client):
    headers = register_and_login(
        client,
        "delete-nonexistent@example.com",
    )

    response = client.delete(
        "/sessions/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_sessions_requires_authentication(client):
    response = client.get("/sessions/")

    assert response.status_code == 401


def test_sessions_rejects_invalid_token(client):
    response = client.get(
        "/sessions/",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_sessions_rejects_negative_skip(client):
    headers = register_and_login(
        client,
        "negative-skip@example.com",
    )

    response = client.get(
        "/sessions/?skip=-1",
        headers=headers,
    )

    assert response.status_code == 422


def test_sessions_rejects_zero_limit(client):
    headers = register_and_login(
        client,
        "zero-limit@example.com",
    )

    response = client.get(
        "/sessions/?limit=0",
        headers=headers,
    )

    assert response.status_code == 422


def test_sessions_rejects_limit_above_100(client):
    headers = register_and_login(
        client,
        "large-limit@example.com",
    )

    response = client.get(
        "/sessions/?limit=101",
        headers=headers,
    )

    assert response.status_code == 422

def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "short-password@example.com",
            "password": "1234567",
        },
    )

    assert response.status_code == 422


def test_register_rejects_missing_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "missing-password@example.com",
        },
    )

    assert response.status_code == 422

def test_register_duplicate_email_returns_409(client):
    email = "duplicate@example.com"

    first_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert second_response.status_code == 409

def test_create_session_rejects_empty_language(client):
    headers = register_and_login(
        client,
        "empty-language@example.com",
    )

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422

def test_create_session_rejects_whitespace_language(client):
    headers = register_and_login(
        client,
        "whitespace-language@example.com",
    )

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "   ",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422

def test_create_session_rejects_missing_project_name(client):
    headers = register_and_login(
        client,
        "missing-project@example.com",
    )

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "language": "Python",
            "started_at": "2026-09-16T15:00:00",
        },
    )

    assert response.status_code == 422

def test_create_session_rejects_missing_started_at(client):
    headers = register_and_login(
        client,
        "missing-started-at@example.com",
    )

    response = client.post(
        "/sessions/",
        headers=headers,
        json={
            "project_name": "DevLog",
            "language": "Python",
        },
    )

    assert response.status_code == 422

def test_auth_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401

def test_auth_me_rejects_empty_bearer_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer ",
        },
    )

    assert response.status_code == 401

def test_auth_me_rejects_invalid_authorization_scheme(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Token invalid-token",
        },
    )

    assert response.status_code == 401