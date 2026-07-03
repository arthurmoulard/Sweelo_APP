from datetime import date

import pytest

from app.models.user import User


@pytest.fixture()
def admin_headers(client, app):
    """Inscrit un utilisateur puis le promeut admin directement en base,
    car il n'existe pas d'endpoint pour le faire via l'API."""
    client.post("/api/v1/auth/register", json={
        "email": "admin@sweelo.io", "username": "admin", "password": "Sup3rSecret1",
    })
    with app.app_context():
        user = User.query.filter_by(email="admin@sweelo.io").first()
        user.is_admin = True
        user.save()

    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@sweelo.io", "password": "Sup3rSecret1",
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_activity(client, headers):
    resp = client.post("/api/v1/activities/", json={
        "type": "run", "distance_km": 5, "duration_min": 30,
        "date": date.today().isoformat(),
    }, headers=headers)
    return resp.get_json()


class TestAdminAccess:

    def test_admin_route_requires_auth(self, client):
        resp = client.get("/api/v1/admin/users")

        assert resp.status_code == 401

    def test_admin_route_rejects_non_admin(self, client, auth_headers):
        resp = client.get("/api/v1/admin/users", headers=auth_headers)

        assert resp.status_code == 403

    def test_admin_route_allows_admin(self, client, admin_headers):
        resp = client.get("/api/v1/admin/users", headers=admin_headers)

        assert resp.status_code == 200


class TestBanUser:

    def test_ban_prevents_login(self, client, admin_headers, auth_headers):
        me = client.get("/api/v1/users/me", headers=auth_headers).get_json()

        resp = client.post(f"/api/v1/admin/users/{me['id']}/ban", headers=admin_headers)
        assert resp.status_code == 200

        resp = client.post("/api/v1/auth/login", json={
            "email": "alice@sweelo.io", "password": "Sup3rSecret1",
        })
        assert resp.status_code == 401

    def test_unban_allows_login_again(self, client, admin_headers, auth_headers):
        me = client.get("/api/v1/users/me", headers=auth_headers).get_json()
        client.post(f"/api/v1/admin/users/{me['id']}/ban", headers=admin_headers)

        resp = client.post(f"/api/v1/admin/users/{me['id']}/unban", headers=admin_headers)
        assert resp.status_code == 200

        resp = client.post("/api/v1/auth/login", json={
            "email": "alice@sweelo.io", "password": "Sup3rSecret1",
        })
        assert resp.status_code == 200

    def test_ban_unknown_user_returns_404(self, client, admin_headers):
        resp = client.post("/api/v1/admin/users/does-not-exist/ban", headers=admin_headers)

        assert resp.status_code == 404


class TestReportsModeration:

    def test_report_workflow(self, client, admin_headers, auth_headers, second_user):
        activity = _create_activity(client, auth_headers)
        other_headers, _ = second_user
        client.post(f"/api/v1/feed/{activity['post_id']}/report", json={
            "reason": "spam",
        }, headers=other_headers)

        resp = client.get("/api/v1/admin/reports", headers=admin_headers)
        assert resp.status_code == 200
        reports = resp.get_json()
        assert len(reports) == 1

        report_id = reports[0]["id"]
        resp = client.put(f"/api/v1/admin/reports/{report_id}", json={
            "action": "reviewed",
        }, headers=admin_headers)

        assert resp.status_code == 200
        assert resp.get_json()["status"] == "reviewed"


class TestAdminDeletePost:

    def test_delete_post_removes_it_from_feed(self, client, admin_headers, auth_headers):
        activity = _create_activity(client, auth_headers)

        resp = client.delete(f"/api/v1/admin/posts/{activity['post_id']}", headers=admin_headers)
        assert resp.status_code == 204

        resp = client.get("/api/v1/feed/", headers=auth_headers)
        assert resp.get_json()["items"] == []

    def test_delete_unknown_post_returns_404(self, client, admin_headers):
        resp = client.delete("/api/v1/admin/posts/does-not-exist", headers=admin_headers)

        assert resp.status_code == 404
