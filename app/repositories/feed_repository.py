from app.models.feed_post import FeedPost
from app.models.comment import Comment
from app.models.associations import post_likes
from app.extensions import db
from app.repositories.base_repository import BaseRepository


class FeedRepository(BaseRepository):

    def __init__(self):
        super().__init__(FeedPost)

    def create_post(self, user_id, activity_id):
        post = FeedPost(user_id=user_id, activity_id=activity_id)
        return self.save(post)

    def get_post(self, post_id):
        return self.model.query.get(post_id)

    def get_feed(self, friend_ids, current_user_id, page=1, limit=20):
        ids = friend_ids + [current_user_id]
        return (
            self.model.query
            .filter(FeedPost.user_id.in_(ids))
            .order_by(FeedPost.created_at.desc())
            .paginate(page=page, per_page=limit, error_out=False)
            .items
        )

    def has_liked(self, post_id, user_id):
        row = db.session.execute(
            post_likes.select().where(
                post_likes.c.post_id == post_id,
                post_likes.c.user_id == user_id,
            )
        ).first()
        return row is not None

    def like(self, post, user_id):
        db.session.execute(
            post_likes.insert().values(post_id=post.id, user_id=user_id)
        )
        post.likes_count += 1
        db.session.commit()

    def unlike(self, post, user_id):
        db.session.execute(
            post_likes.delete().where(
                post_likes.c.post_id == post.id,
                post_likes.c.user_id == user_id,
            )
        )
        post.likes_count = max(0, post.likes_count - 1)
        db.session.commit()

    def create_comment(self, post_id, user_id, content):
        comment = Comment(post_id=post_id, user_id=user_id, content=content)
        return self.save(comment)
