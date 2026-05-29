"""
Sweelo MVP — Report
===================
"""

from app.extensions import db
from app.models.base_model import BaseModel


class Report(BaseModel):
    """
    Signalement d'un contenu inapproprié par un utilisateur.
    Traité manuellement par un admin via /admin/reports.

    Statuts :
        pending   → en attente de traitement
        reviewed  → admin a pris une action
        dismissed → admin a rejeté le signalement

    Relations :
        reporter → User (N-1, via backref)
    """

    __tablename__ = "reports"

    TARGET_TYPES = ("post", "comment")
    STATUSES     = ("pending", "reviewed", "dismissed")

    reporter_id = db.Column(db.String(36),  db.ForeignKey("users.id"), nullable=False)
    target_type = db.Column(db.Enum(*TARGET_TYPES, name="report_target_type"), nullable=False)
    target_id   = db.Column(db.String(36),  nullable=False)
    reason      = db.Column(db.String(255), nullable=True)
    status      = db.Column(db.Enum(*STATUSES, name="report_status"), nullable=False, default="pending")

    def mark_reviewed(self) -> None:
        self.status = "reviewed"

    def dismiss(self) -> None:
        self.status = "dismissed"

    def is_pending(self) -> bool:
        return self.status == "pending"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "reporter_id": self.reporter_id,
            "target_type": self.target_type,
            "target_id":   self.target_id,
            "reason":      self.reason,
            "status":      self.status,
        })
        return base
    