from app.models.user import User
from app.models.associations import friendships
from app.extensions import db
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email):
        return self.model.query.filter_by(email=email).first()

    def get_by_username(self, username):
        return self.model.query.filter_by(username=username).first()

    def create(self, email, username, password):
        user = User(email=email, username=username)
        user.set_password(password)
        return self.save(user)

    def get_friend_ids(self, user_id):
        rows = db.session.execute(
            friendships.select().where(friendships.c.user_id == user_id)
        ).fetchall()
        return [row.friend_id for row in rows]

    def add_friend(self, user_id, friend_id):
        db.session.execute(
            friendships.insert().values(user_id=user_id, friend_id=friend_id)
        )
        db.session.commit()
