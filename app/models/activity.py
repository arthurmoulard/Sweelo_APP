from datetime import date
from app.extensions import db
from app.models.base_model import BaseModel


class Activity(BaseModel):
    """
    Entraînement enregistré par un athlète.

    À la création (géré par la Façade) :
        → génère automatiquement un FeedPost

    Relations :
        owner     → User     (N-1, via backref)
        feed_post → FeedPost (1-1)
    """

    __tablename__ = "activities"

    ACTIVITY_TYPES = ("run", "bike", "swim", "walk")

    user_id      = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type         = db.Column(db.Enum(*ACTIVITY_TYPES, name="activity_type"), nullable=False)
    distance_km  = db.Column(db.Float,   nullable=False, default=0.0)
    duration_min = db.Column(db.Integer, nullable=False, default=0)
    calories     = db.Column(db.Integer, nullable=True)
    date         = db.Column(db.Date,    nullable=False, default=date.today)
    notes        = db.Column(db.Text,    nullable=True)

    # ── Relations ──────────────────────────────────────────────────────────────
    feed_post = db.relationship("FeedPost", backref="activity", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "user_id":      self.user_id,
            "type":         self.type,
            "distance_km":  self.distance_km,
            "duration_min": self.duration_min,
            "date":         self.date.isoformat(),
            "notes":        self.notes,
        })
        return base