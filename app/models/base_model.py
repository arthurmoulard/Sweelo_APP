"""
Sweelo MVP — BaseModel
======================
Classe abstraite partagée par tous les modèles.
"""

import uuid
from datetime import datetime, timezone

from app.extensions import db


def _utcnow():
    """UTC courant sans fuseau (remplace datetime.utcnow, déprécié en Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel(db.Model):
    __abstract__ = True

    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime,  nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime,  nullable=False, default=_utcnow, onupdate=_utcnow)

    def save(self) -> "BaseModel":
        """INSERT ou UPDATE en BDD. Retourne self pour le chaînage."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Supprime l'objet de la BDD."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
