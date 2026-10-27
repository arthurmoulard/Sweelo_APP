"""Tests du stockage des images (app/storage.py) et de l'URL MySQL (app/config.py)."""
import io
import sys
import types

import pytest
from werkzeug.datastructures import FileStorage

from app import storage
from app.config import _database_url

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def _file():
    return FileStorage(stream=io.BytesIO(PNG), filename="photo.png")


def test_local_save_then_delete(tmp_path, monkeypatch):
    """Sans jeton Vercel Blob, l'image va sur le disque puis peut être supprimée."""
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    monkeypatch.delenv("BLOB_STORE_ID", raising=False)
    monkeypatch.setattr(storage, "UPLOAD_DIR", str(tmp_path))

    url = storage.save_image(_file(), "posts", "png")
    assert url.startswith("/uploads/posts/") and url.endswith(".png")
    path = tmp_path / "posts" / url.rsplit("/", 1)[-1]
    assert path.read_bytes() == PNG

    storage.delete_image(url)
    assert not path.exists()


def test_local_delete_refuses_path_traversal(tmp_path, monkeypatch):
    """Une URL forgée (« ../ ») ne doit jamais supprimer un fichier hors de uploads/."""
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    monkeypatch.delenv("BLOB_STORE_ID", raising=False)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    victim = tmp_path / "config.py"
    victim.write_text("secret")
    monkeypatch.setattr(storage, "UPLOAD_DIR", str(uploads))

    storage.delete_image("/uploads/../config.py")
    assert victim.exists()


@pytest.mark.parametrize("env_var", ["BLOB_STORE_ID", "BLOB_READ_WRITE_TOKEN"])
def test_blob_save_and_delete(monkeypatch, env_var):
    """Store Blob relié (OIDC) ou jeton : l'image est envoyée au SDK et l'URL publique renvoyée."""
    calls = {}

    def put_blob(pathname, body, *, access, content_type):
        calls["put"] = (pathname, body, access, content_type)
        return types.SimpleNamespace(url=f"https://store.public.blob.vercel-storage.com/{pathname}")

    def delete_blob(url):
        calls["delete"] = url

    fake_sync = types.SimpleNamespace(put_blob=put_blob, delete_blob=delete_blob)
    fake_blob = types.ModuleType("vercel.blob")
    fake_blob.sync = fake_sync
    monkeypatch.setitem(sys.modules, "vercel.blob", fake_blob)
    monkeypatch.delenv("BLOB_STORE_ID", raising=False)
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    monkeypatch.setenv(env_var, "test-value")

    url = storage.save_image(_file(), "avatars", "png")
    pathname, body, access, content_type = calls["put"]
    assert pathname.startswith("avatars/") and body == PNG
    assert access == "public" and content_type == "image/png"
    assert url.startswith("https://")

    storage.delete_image(url)
    assert calls["delete"] == url


def test_database_url_aiven(monkeypatch):
    """L'URL fournie par Aiven est convertie pour PyMySQL (driver + ssl-mode retiré)."""
    monkeypatch.setenv("DATABASE_URL", "mysql://avnadmin:pw@host.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED")
    assert _database_url("") == "mysql+pymysql://avnadmin:pw@host.aivencloud.com:12345/defaultdb"


@pytest.mark.parametrize("url", [
    "sqlite:///sweelo_dev.db",
    "sqlite:////home/user/sweelo.db",
    "mysql+pymysql://user:pw@localhost/sweelo",
])
def test_database_url_unchanged_without_ssl_mode(monkeypatch, url):
    """Sans ssl-mode, l'URL n'est pas modifiée (chemins SQLite absolus compris)."""
    monkeypatch.setenv("DATABASE_URL", url)
    assert _database_url("") == url
