"""
Sweelo MVP — BaseModel
======================
Classe abstraite partagée par tous les modèles.
"""

import uuid
from datetime import datetime
from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime,  nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,  nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    