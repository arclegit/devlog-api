def register_user(client, email, password="password123"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(client, email, password="password123"):
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_session(client, token, project_name="Test Project"):
    response = client.post(
        "/sessions/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "project_name": project_name,
            "language": "Python",
            "started_at": "2026-09-16T09:00:00Z",
            "ended_at": "2026-09-16T10:00:00Z",
            "description": "Test session",
        },
    )

    assert response.status_code == 200

    return response.json()


def test_register_login_and_protected_route(client):
    email = "test@example.com"

    register_user(client, email)

    token = login_user(client, email)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_invalid_token_returns_401(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_user_cannot_access_another_users_session(client):
    user_a = "usera@example.com"
    user_b = "userb@example.com"

    register_user(client, user_a)
    register_user(client, user_b)

    token_a = login_user(client, user_a)
    token_b = login_user(client, user_b)

    session_a = create_session(
        client,
        token_a,
        project_name="User A Project",
    )

    session_id = session_a["id"]

    response = client.get(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {token_b}",
        },
    )

    assert response.status_code == 404

    response = client.patch(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {token_b}",
        },
        json={
            "description": "Unauthorized modification",
        },
    )

    assert response.status_code == 404

    response = client.delete(
        f"/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {token_b}",
        },
    )

    assert response.status_code == 404


def test_user_only_sees_own_sessions(client):
    user_a = "listusera@example.com"
    user_b = "listuserb@example.com"

    register_user(client, user_a)
    register_user(client, user_b)

    token_a = login_user(client, user_a)
    token_b = login_user(client, user_b)

    create_session(
        client,
        token_a,
        project_name="A Project",
    )

    create_session(
        client,
        token_b,
        project_name="B Project",
    )

    response = client.get(
        "/sessions/",
        headers={
            "Authorization": f"Bearer {token_a}",
        },
    )

    assert response.status_code == 200

    sessions = response.json()

    assert len(sessions) == 1
    assert sessions[0]["project_name"] == "A Project"

def test_sessions_pagination(client):
    email = "pagination@example.com"

    register_user(client, email)
    token = login_user(client, email)

    create_session(client, token, "Project 1")
    create_session(client, token, "Project 2")
    create_session(client, token, "Project 3")

    response = client.get(
        "/sessions/?skip=0&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    sessions = response.json()

    assert len(sessions) == 2