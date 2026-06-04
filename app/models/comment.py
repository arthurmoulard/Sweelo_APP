"""
Sweelo MVP — Comment
====================
"""

from app.extensions import db
from app.models.base_model import BaseModel


class Comment(BaseModel):
    """
    Commentaire sur un FeedPost.
    Passe obligatoirement par ModerationService avant insertion.

    Relations :
        author → User     (N-1, via backref)
        post   → FeedPost (N-1, via backref)
    """

    __tablename__ = "comments"

    post_id = db.Column(db.String(36), db.ForeignKey("feed_posts.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"),      nullable=False)
    content = db.Column(db.Text,       nullable=False)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "post_id": self.post_id,
            "user_id": self.user_id,
            "content": self.content,
        })
        return base
    