from datetime import datetime
from app.extensions import db


class TokenBlocklist(db.Model):
    """Stocke les JTI des tokens révoqués (logout).
    Le JWTManager vérifie cette table à chaque requête via le blocklist_loader.
    """
    __tablename__ = "token_blocklist"

    id         = db.Column(db.Integer,    primary_key=True)
    jti        = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime,  nullable=False, default=datetime.utcnow)
