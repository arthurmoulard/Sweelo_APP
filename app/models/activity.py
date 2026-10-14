from datetime import date
from app.extensions import db
from app.models.base_model import BaseModel


class Activity(BaseModel):

    __tablename__ = "activities"

    ACTIVITY_TYPES = (
        "run", "bike", "swim", "walk",
        "trail", "triathlon", "hyrox",
        "muscu", "basket", "foot", "hand", "volley", "combat",
    )

    # Sports sans distance
    NO_DISTANCE_TYPES = {"muscu", "basket", "foot", "hand", "volley", "combat"}

    # Champs extra attendus par sport (documentation)
    EXTRA_FIELDS = {
        "muscu":  {"weight_kg": "Poids soulevé (kg)", "sets": "Séries", "reps": "Répétitions"},
        "basket": {"score": "Score ex: '84-76'", "points": "Points marqués personnellement"},
        "foot":   {"score": "Score ex: '2-1'", "goals": "Buts marqués"},
        "hand":   {"score": "Score ex: '28-24'", "goals": "Buts marqués"},
        "volley": {"score": "Score ex: '3-1'", "points": "Points marqués"},
        "combat": {"result": "win/loss/draw", "points": "Points / ippon"},
    }

    user_id      = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type         = db.Column(db.Enum(*ACTIVITY_TYPES, name="activity_type"), nullable=False)
    distance_km  = db.Column(db.Float,   nullable=True, default=None)
    duration_min = db.Column(db.Integer, nullable=False, default=0)
    calories     = db.Column(db.Integer, nullable=True)
    date         = db.Column(db.Date,    nullable=False, default=date.today)
    notes        = db.Column(db.Text,    nullable=True)
    extra_data   = db.Column(db.JSON,    nullable=True, default=None)

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
            "extra_data":   self.extra_data,
            # Inclut les données du post de feed associé pour que le frontend gère les photos
            "post_id":      self.feed_post.id       if self.feed_post else None,
            "photo_url":    self.feed_post.photo_url if self.feed_post else None,
        })
        return base
