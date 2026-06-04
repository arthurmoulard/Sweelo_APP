"""
Sweelo MVP — app/models/__init__.py
====================================
Importe tous les modèles MVP pour que SQLAlchemy
les connaisse au moment du db.create_all().
"""

from app.models.base_model import BaseModel
from app.models.associations import post_likes, friendships
from app.models.user import User
from app.models.activity import Activity
from app.models.feed_post import FeedPost
from app.models.comment import Comment
from app.models.report import Report

__all__ = [
    "BaseModel",
    "post_likes",
    "friendships",
    "User",
    "Activity",
    "FeedPost",
    "Comment",
    "Report",
]
