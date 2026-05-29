from app.extensions import db
from app.models.base_model import BaseModel
from app.models.associations import post_likes, friendships
import bcrypt


class User(BaseModel):
    """
    Athlète inscrit sur Sweelo.

    Relations :
        activities  → list[Activity]  (1-N)
        feed_posts  → list[FeedPost]  (1-N)
        comments    → list[Comment]   (1-N)
        reports     → list[Report]    (1-N, signalements soumis)
        liked_posts → list[FeedPost]  (N-N via post_likes)
        friends     → list[User]      (N-N via friendships)
    """

    __tablename__ = "users"

    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    is_admin      = db.Column(db.Boolean,     nullable=False, default=False)
    is_banned     = db.Column(db.Boolean,     nullable=False, default=False)

    # ── Relations ──────────────────────────────────────────────────────────────
    activities = db.relationship("Activity", backref="owner",    lazy="dynamic", cascade="all, delete-orphan")
    feed_posts = db.relationship("FeedPost", backref="author",   lazy="dynamic", cascade="all, delete-orphan")
    comments   = db.relationship("Comment",  backref="author",   lazy="dynamic", cascade="all, delete-orphan")
    reports    = db.relationship("Report",   backref="reporter", lazy="dynamic", cascade="all, delete-orphan")

    liked_posts = db.relationship(
        "FeedPost",
        secondary=post_likes,
        backref=db.backref("liked_by", lazy="dynamic"),
        lazy="dynamic",
    )
    friends = db.relationship(
        "User",
        secondary=friendships,
        primaryjoin=lambda: User.id == friendships.c.user_id,
        secondaryjoin=lambda: User.id == friendships.c.friend_id,
        lazy="dynamic",
    )

    # ── Méthodes ───────────────────────────────────────────────────────────────

    def set_password(self, plain_password: str) -> None:
        """Hash le mot de passe avec bcrypt."""
        self.password_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        """Vérifie le mot de passe contre le hash stocké."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "email":    self.email,
            "username": self.username,
            "is_admin": self.is_admin,
            "is_banned": self.is_banned,
        })
        return base
    