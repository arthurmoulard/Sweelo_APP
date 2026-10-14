class TestRegister:

    def test_register_returns_user_and_sets_cookies(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["email"] == "alice@sweelo.io"
        # Les tokens ne doivent plus jamais apparaître dans le corps JSON
        # (sinon un script XSS pourrait les y lire, comme avec localStorage).
        assert "access_token" not in data
        assert "refresh_token" not in data
        set_cookie = " ".join(resp.headers.get_all("Set-Cookie"))
        assert "access_token_cookie=" in set_cookie
        assert "refresh_token_cookie=" in set_cookie
        assert "HttpOnly" in set_cookie

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

    def test_login_with_valid_credentials_sets_cookies(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "alice@sweelo.io", "username": "alice", "password": "Sup3rSecret1",
        })

        resp = client.post("/api/v1/auth/login", json={
            "email": "alice@sweelo.io", "password": "Sup3rSecret1",
        })

        assert resp.status_code == 200
        assert "access_token" not in resp.get_json()
        set_cookie = " ".join(resp.headers.get_all("Set-Cookie"))
        assert "access_token_cookie=" in set_cookie

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
        # auth_headers ne porte que le cookie d'access token ; on le réinjecte
        # sous le nom du cookie de refresh pour vérifier qu'un token du mauvais
        # type (access, pas refresh) est bien rejeté par /auth/refresh.
        access_token = auth_headers["Cookie"].split("=", 1)[1]
        resp = client.post("/api/v1/auth/refresh", headers={
            "Cookie": f"refresh_token_cookie={access_token}",
            "X-CSRF-TOKEN": auth_headers["X-CSRF-TOKEN"],
        })

        assert resp.status_code == 422
