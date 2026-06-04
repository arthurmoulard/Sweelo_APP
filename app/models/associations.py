"""
Sweelo MVP — Associations
=========================
Tables de liaison N-N.
"""

from app.extensions import db

# Likes sur les posts (User ↔ FeedPost)
post_likes = db.Table(
    "post_likes",
    db.Column("post_id", db.String(36), db.ForeignKey("feed_posts.id"), primary_key=True),
    db.Column("user_id", db.String(36), db.ForeignKey("users.id"),      primary_key=True),
)

# Amitiés (User ↔ User)
friendships = db.Table(
    "friendships",
    db.Column("user_id",   db.String(36), db.ForeignKey("users.id"), primary_key=True),
    db.Column("friend_id", db.String(36), db.ForeignKey("users.id"), primary_key=True),
)
