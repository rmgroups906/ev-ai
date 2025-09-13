from fastapi.testclient import TestClient
import random
import string
def random_username():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
def test_health_check(client: TestClient):
    """Tests if the health check endpoint is working."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
def test_register_user_success(client: TestClient):
    """Tests successful user registration."""
    username = random_username()
    response = client.post(
        "/auth/register",
        json={"username": username, "password": "a_strong_password"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == username
    assert "role" in response.json()

def test_register_user_already_exists(client: TestClient):
    """Tests that registering a user with an existing username fails."""
    username = random_username()
    user_data = {"username": username, "password": "a_strong_password"}

    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 400 # Bad Request
    assert "already exists" in response2.json()["detail"]

def test_full_auth_flow(client: TestClient, test_user: dict):
    """
    Tests the complete authentication flow using a pre-existing user from a fixture.
    1. Login with username and password.
    2. Receive access and refresh tokens.
    3. Use the access token to access a protected route.
    4. Use the refresh token to get a new access token.
    """
    login_response = client.post(
        "/auth/token",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = client.get("/users/me", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["username"] == test_user["username"]

    refresh_response = client.post(
        "/auth/refresh", 
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != access_token 