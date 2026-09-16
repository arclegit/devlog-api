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

    assert response.status_code == 201

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
    
def test_analytics_summary_with_no_sessions(client):
    email = "analytics-empty@example.com"

    register_user(client, email)

    token = login_user(client, email)

    response = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_sessions"] == 0
    assert data["total_coding_seconds"] == 0
    assert data["average_session_seconds"] == 0

def test_analytics_summary_calculates_aggregates(client):
    email = "analytics-test@example.com"

    register_user(client, email)

    token = login_user(client, email)

    create_session(
        client,
        token,
        project_name="Project A",
    )

    create_session(
        client,
        token,
        project_name="Project B",
    )

    response = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_sessions"] == 2
    assert data["total_coding_seconds"] == 7200
    assert data["average_session_seconds"] == 3600

def test_analytics_summary_only_includes_current_users_sessions(client):
    user_a = "analytics-usera@example.com"
    user_b = "analytics-userb@example.com"

    register_user(client, user_a)
    register_user(client, user_b)

    token_a = login_user(client, user_a)
    token_b = login_user(client, user_b)

    create_session(
        client,
        token_a,
        project_name="User A Project",
    )

    create_session(
        client,
        token_a,
        project_name="User A Project 2",
    )

    create_session(
        client,
        token_b,
        project_name="User B Project",
    )

    response_a = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token_a}",
        },
    )

    assert response_a.status_code == 200

    data_a = response_a.json()

    assert data_a["total_sessions"] == 2
    assert data_a["total_coding_seconds"] == 7200
    assert data_a["average_session_seconds"] == 3600

    response_b = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token_b}",
        },
    )

    assert response_b.status_code == 200

    data_b = response_b.json()

    assert data_b["total_sessions"] == 1
    assert data_b["total_coding_seconds"] == 3600
    assert data_b["average_session_seconds"] == 3600

def test_language_analytics(client):
    email = "language-analytics@example.com"

    register_user(client, email)
    token = login_user(client, email)

    create_session(client, token, project_name="Python Project")

    response = client.post(
        "/sessions/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "project_name": "JavaScript Project",
            "language": "JavaScript",
            "started_at": "2026-09-16T11:00:00Z",
            "ended_at": "2026-09-16T12:00:00Z",
            "description": "JavaScript session",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/analytics/languages",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    languages = {
        item["language"]: item
        for item in data
    }

    assert languages["Python"]["total_sessions"] == 1
    assert languages["Python"]["total_coding_seconds"] == 3600

    assert languages["JavaScript"]["total_sessions"] == 1
    assert languages["JavaScript"]["total_coding_seconds"] == 3600

def test_project_analytics(client):
    email = "project-analytics@example.com"

    register_user(client, email)
    token = login_user(client, email)

    create_session(
        client,
        token,
        project_name="Project A",
    )

    create_session(
        client,
        token,
        project_name="Project A",
    )

    response = client.get(
        "/analytics/projects",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["project_name"] == "Project A"
    assert data[0]["total_sessions"] == 2
    assert data[0]["total_coding_seconds"] == 7200

def test_daily_analytics(client):
    email = "daily-analytics@example.com"

    register_user(client, email)
    token = login_user(client, email)

    create_session(client, token)

    response = client.get(
        "/analytics/daily",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["date"] == "2026-09-16"
    assert data[0]["total_sessions"] == 1
    assert data[0]["total_coding_seconds"] == 3600

def test_weekly_analytics(client):
    email = "weekly-analytics@example.com"

    register_user(client, email)
    token = login_user(client, email)

    create_session(client, token)

    response = client.get(
        "/analytics/weekly",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["total_sessions"] == 1
    assert data[0]["total_coding_seconds"] == 3600

def test_analytics_requires_authentication(client):
    endpoints = [
        "/analytics/summary",
        "/analytics/languages",
        "/analytics/projects",
        "/analytics/daily",
        "/analytics/weekly",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 401


def test_analytics_invalid_token_returns_401(client):
    headers = {
        "Authorization": "Bearer invalid-token",
    }

    endpoints = [
        "/analytics/summary",
        "/analytics/languages",
        "/analytics/projects",
        "/analytics/daily",
        "/analytics/weekly",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers=headers,
        )

        assert response.status_code == 401


def test_analytics_only_includes_current_users_sessions(client):
    user_a = "analytics-user-a@example.com"
    user_b = "analytics-user-b@example.com"

    register_user(client, user_a)
    register_user(client, user_b)

    token_a = login_user(client, user_a)
    token_b = login_user(client, user_b)

    create_session(
        client,
        token_a,
        project_name="User A Project",
    )

    create_session(
        client,
        token_b,
        project_name="User B Project",
    )

    response = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token_a}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_sessions"] == 1
    assert data["total_coding_seconds"] == 3600

    response = client.get(
        "/analytics/languages",
        headers={
            "Authorization": f"Bearer {token_a}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["language"] == "Python"
    assert data[0]["total_sessions"] == 1

    response = client.get(
        "/analytics/projects",
        headers={
            "Authorization": f"Bearer {token_a}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["project_name"] == "User A Project"

def test_analytics_excludes_active_sessions(client):
    email = "active-analytics@example.com"

    register_user(client, email)
    token = login_user(client, email)

    response = client.post(
        "/sessions/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "project_name": "Active Project",
            "language": "Python",
            "started_at": "2026-09-16T09:00:00Z",
            "ended_at": None,
            "description": "Active session",
        },
    )

    assert response.status_code == 201

    create_session(
        client,
        token,
        project_name="Completed Project",
    )

    response = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_sessions"] == 1
    assert data["total_coding_seconds"] == 3600

def test_analytics_for_user_with_no_sessions(client):
    email = "no-sessions@example.com"

    register_user(client, email)
    token = login_user(client, email)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/analytics/summary",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_sessions"] == 0
    assert data["total_coding_seconds"] == 0
    assert data["average_session_seconds"] == 0

    response = client.get(
        "/analytics/languages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []

    response = client.get(
        "/analytics/projects",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []

    response = client.get(
        "/analytics/daily",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []

    response = client.get(
        "/analytics/weekly",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []