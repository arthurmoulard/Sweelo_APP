class TestRegister:

    def test_register_returns_tokens_and_user(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["email"] == "alice@sweelo.io"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_rejects_duplicate_email(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        resp = client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice2", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 409

    def test_register_rejects_duplicate_username(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        resp = client.post("/api/v1/auth/register", json={
            "email": "alice2@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 409

    def test_register_rejects_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "short",
        })

        assert resp.status_code == 400

    def test_register_rejects_invalid_email(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email", "username": "alice", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 400


class TestLogin:

    def test_login_with_valid_credentials_returns_tokens(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        resp = client.post("/api/v1/auth/login", json={
            "email": "alice@sweelo.io", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_login_with_wrong_password_fails(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        resp = client.post("/api/v1/auth/login", json={
            "email": "alice@sweelo.io", "password": "wrong-password",
        })

        assert resp.status_code == 401

    def test_login_with_unknown_email_fails(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@sweelo.io", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 401


class TestSessionLifecycle:

    def test_me_requires_authentication(self, client):
        resp = client.get("/api/v1/users/me")

        assert resp.status_code == 401

    def test_me_returns_current_user(self, client, auth_headers):
        resp = client.get("/api/v1/users/me", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.get_json()["username"] == "alice"

    def test_logout_revokes_token(self, client, auth_headers):
        resp = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 200

        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 401

    def test_refresh_requires_refresh_token(self, client, auth_headers):
        resp = client.post("/api/v1/auth/refresh", headers=auth_headers)

        assert resp.status_code == 422
