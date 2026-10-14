"""
Sweelo — Utilitaires partagés
=============================
"""

_SIGNATURES = {
    "jpg":  (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png":  (b"\x89PNG\r\n\x1a\n",),
    "gif":  (b"GIF87a", b"GIF89a"),
}


def is_valid_image(file_storage, ext: str) -> bool:
    """Vérifie que le contenu réel du fichier correspond à son extension déclarée
    (empêche l'upload d'un fichier malveillant simplement renommé en .jpg/.png/...)."""
    header = file_storage.stream.read(16)
    file_storage.stream.seek(0)

    if ext == "webp":
        valid = header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    else:
        signatures = _SIGNATURES.get(ext)
        valid = signatures is not None and any(header.startswith(sig) for sig in signatures)

    return valid
