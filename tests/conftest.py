import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.services.moderation_service import ModerationService  # noqa: E402

DEFAULT_PASSWORD = "Sup3rSecret1"


@pytest.fixture()
def app(monkeypatch):
    """App Flask configurée pour les tests, DB SQLite en mémoire réinitialisée à chaque test.

    La modération OpenAI est neutralisée (toujours "safe") pour ne jamais
    appeler la vraie API pendant les tests — voir test_moderation_service.py
    pour les tests dédiés au comportement réel de ModerationService.
    """
    monkeypatch.setattr(ModerationService, "check", lambda self, content: (True, ""))

    application = create_app("testing")
    yield application

    with application.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register(client, email="alice@sweelo.io", username="alice", password=DEFAULT_PASSWORD):
    return client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": password,
    })


@pytest.fixture()
def auth_user(client):
    """Inscrit l'utilisateur par défaut et retourne (headers, user_id)."""
    resp = _register(client)
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["id"]


@pytest.fixture()
def auth_headers(auth_user):
    headers, _ = auth_user
    return headers


@pytest.fixture()
def second_user(client):
    """Inscrit un second utilisateur ('bob') et retourne (headers, user_id)."""
    resp = _register(client, email="bob@sweelo.io", username="bob")
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["id"]
