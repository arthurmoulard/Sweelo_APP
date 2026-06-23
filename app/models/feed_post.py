"""
Sweelo MVP — FeedPost
=====================
"""

from app.extensions import db
from app.models.base_model import BaseModel


class FeedPost(BaseModel):
    """
    Publication automatique d'une activité dans le feed social.
    Créé automatiquement par la Façade lors d'un POST /activities.
    Supporte une photo optionnelle stockée sur Cloudinary.

    Relations :
        author   → User          (N-1, via backref)
        activity → Activity      (1-1, via backref)
        comments → list[Comment] (1-N)
        liked_by → list[User]    (N-N via post_likes, via backref)
    """

    __tablename__ = "feed_posts"

    activity_id     = db.Column(db.String(36), db.ForeignKey("activities.id"), nullable=False, unique=True)
    user_id         = db.Column(db.String(36), db.ForeignKey("users.id"),      nullable=False)
    likes_count     = db.Column(db.Integer,    nullable=False, default=0)

    # Photo optionnelle (Cloudinary)
    photo_url       = db.Column(db.String(500), nullable=True)
    photo_public_id = db.Column(db.String(200), nullable=True)

    # ── Relations ──────────────────────────────────────────────────────────────
    comments = db.relationship("Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan")

    # ── Méthodes ───────────────────────────────────────────────────────────────

    def has_photo(self) -> bool:
        return self.photo_url is not None

    def to_dict(self, current_user_id: str = None) -> dict:
        base = super().to_dict()
        base.update({
            "activity_id":    self.activity_id,
            "user_id":        self.user_id,
            "username":       self.author.username if self.author else None,
            "likes_count":    self.likes_count,
            "photo_url":      self.photo_url,
            "comments_count": self.comments.count(),
            "activity": {
                "type":         self.activity.type,
                "distance_km":  self.activity.distance_km,
                "duration_min": self.activity.duration_min,
                "date":         self.activity.date.isoformat(),
                "notes":        self.activity.notes,
            } if self.activity else None,
        })
        if current_user_id:
            base["user_has_liked"] = self.liked_by.filter_by(id=current_user_id).count() > 0
        return base
    