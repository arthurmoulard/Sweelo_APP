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
    # use_cookies=False : les tests font coexister plusieurs identités (alice,
    # bob, un admin...) sur le même client. Avec la cookie-jar automatique du
    # client de test, la dernière connexion effectuée écraserait les cookies
    # des autres utilisateurs. On gère donc les cookies nous-mêmes, un par un,
    # via l'en-tête "Cookie" explicite renvoyé par chaque fixture d'identité.
    return app.test_client(use_cookies=False)


def _register(client, email="alice@sweelo.io", username="alice", password=DEFAULT_PASSWORD):
    return client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": password,
    })


def _cookie_value(resp, name):
    """Extrait la valeur d'un cookie posé par le serveur via Set-Cookie."""
    for raw in resp.headers.get_all("Set-Cookie"):
        if raw.startswith(f"{name}="):
            return raw.split(";", 1)[0].split("=", 1)[1]
    return None


def _auth_headers_from(resp):
    """Construit les en-têtes identifiant un utilisateur à partir de la réponse
    de login/register : le JWT (cookie httpOnly) en en-tête Cookie explicite,
    et le jeton CSRF associé en en-tête X-CSRF-TOKEN."""
    access_cookie = _cookie_value(resp, "access_token_cookie")
    csrf = _cookie_value(resp, "csrf_access_token")
    return {"Cookie": f"access_token_cookie={access_cookie}", "X-CSRF-TOKEN": csrf}


@pytest.fixture()
def auth_headers_from():
    """Expose _auth_headers_from aux autres fichiers de test (ex: admin_headers
    dans test_admin_endpoints.py) sans import inter-modules fragile."""
    return _auth_headers_from


@pytest.fixture()
def auth_user(client):
    """Inscrit l'utilisateur par défaut et retourne (headers, user_id)."""
    resp = _register(client)
    data = resp.get_json()
    return _auth_headers_from(resp), data["id"]


@pytest.fixture()
def auth_headers(auth_user):
    headers, _ = auth_user
    return headers


@pytest.fixture()
def second_user(client):
    """Inscrit un second utilisateur ('bob') et retourne (headers, user_id)."""
    resp = _register(client, email="bob@sweelo.io", username="bob")
    data = resp.get_json()
    return _auth_headers_from(resp), data["id"]
