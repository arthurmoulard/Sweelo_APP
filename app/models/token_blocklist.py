from datetime import datetime, timezone

from app.extensions import db


def _utcnow():
    """UTC courant sans fuseau (remplace datetime.utcnow, déprécié en Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TokenBlocklist(db.Model):
    """Stocke les JTI des tokens révoqués (logout).
    Le JWTManager vérifie cette table à chaque requête via le blocklist_loader.
    """
    __tablename__ = "token_blocklist"

    id         = db.Column(db.Integer,    primary_key=True)
    jti        = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime,  nullable=False, default=_utcnow)
