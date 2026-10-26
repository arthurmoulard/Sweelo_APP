"""
Sweelo — Stockage des images (photos des posts, avatars)
========================================================
Deux modes, choisis automatiquement :

- Vercel Blob (production) : quand Vercel a relié un store Blob au projet
  (variable BLOB_STORE_ID, connexion OIDC) ou qu'un jeton BLOB_READ_WRITE_TOKEN existe.
  Sur Vercel, le disque est en lecture seule et effacé à chaque déploiement :
  les images sont donc envoyées dans le stockage Vercel Blob, qui renvoie une
  URL publique (https://….public.blob.vercel-storage.com/…).
- Disque local (développement, tests) : les images vont dans frontend/uploads/
  et sont servies par Flask sous /uploads/….
"""
import os
import uuid

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'uploads'))

CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}


def _blob_enabled():
    return bool(os.getenv("BLOB_STORE_ID") or os.getenv("BLOB_READ_WRITE_TOKEN"))


def _blob_client():
    """Renvoie le client Vercel Blob, prêt à s'authentifier.

    Avec OIDC, Vercel transmet un jeton temporaire dans l'en-tête de chaque
    requête (x-vercel-oidc-token) : on donne les en-têtes de la requête en
    cours au SDK pour qu'il puisse le lire.
    """
    from flask import has_request_context, request
    from vercel.blob import sync as blob
    from vercel.headers import set_headers

    if has_request_context():
        set_headers(dict(request.headers))
    return blob


def save_image(file_storage, folder, ext):
    """Enregistre l'image et renvoie son URL publique.

    folder : sous-dossier logique (« posts » ou « avatars »).
    ext    : extension déjà validée par is_valid_image().
    """
    filename = f"{uuid.uuid4().hex}.{ext}"

    if _blob_enabled():
        blob = _blob_client()
        result = blob.put_blob(
            f"{folder}/{filename}",
            file_storage.read(),
            access="public",
            content_type=CONTENT_TYPES.get(ext, "application/octet-stream"),
        )
        return result.url

    target_dir = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)
    file_storage.save(os.path.join(target_dir, filename))
    return f"/uploads/{folder}/{filename}"


def delete_image(url):
    """Supprime une image enregistrée par save_image() (ne fait rien si elle n'existe plus)."""
    if not url:
        return

    if url.startswith("https://"):
        if _blob_enabled():
            _blob_client().delete_blob(url)
        return

    if "/uploads/" in url:
        rel = url.split("/uploads/", 1)[-1]
        path = os.path.abspath(os.path.join(UPLOAD_DIR, rel))
        # Garde-fou : on ne supprime jamais en dehors de frontend/uploads/
        if path.startswith(UPLOAD_DIR + os.sep) and os.path.isfile(path):
            os.remove(path)
