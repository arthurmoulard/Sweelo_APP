from datetime import date, timedelta

import pytest

import app.extensions as ext


class TestRegisterLogin:

    def test_register_creates_user(self, app):
        with app.app_context():
            user = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            assert user.id is not None
            assert user.check_password("Sup3rSecret1")

    def test_register_rejects_duplicate_email(self, app):
        with app.app_context():
            ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            with pytest.raises(ValueError):
                ext.facade.register(email="a@a.com", username="alice2", password="Sup3rSecret1")

    def test_register_rejects_duplicate_username(self, app):
        with app.app_context():
            ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            with pytest.raises(ValueError):
                ext.facade.register(email="b@b.com", username="alice", password="Sup3rSecret1")

    def test_login_rejects_wrong_password(self, app):
        with app.app_context():
            ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            with pytest.raises(ValueError):
                ext.facade.login(email="a@a.com", password="wrong-password")

    def test_login_rejects_banned_user(self, app):
        with app.app_context():
            user = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            user.is_banned = True
            user.save()
            with pytest.raises(PermissionError):
                ext.facade.login(email="a@a.com", password="Sup3rSecret1")


class TestActivities:

    def test_create_activity_rejects_future_date(self, app):
        with app.app_context():
            user = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            future = (date.today() + timedelta(days=1)).isoformat()
            with pytest.raises(ValueError):
                ext.facade.create_activity(user.id, {
                    "type": "run", "distance_km": 5, "duration_min": 30, "date": future,
                })

    def test_create_activity_also_creates_feed_post(self, app):
        with app.app_context():
            user = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            activity = ext.facade.create_activity(user.id, {
                "type": "run", "distance_km": 5, "duration_min": 30,
                "date": date.today().isoformat(),
            })
            assert activity.feed_post is not None

    def test_get_activity_denies_other_users(self, app):
        with app.app_context():
            owner = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            other = ext.facade.register(email="b@b.com", username="bob", password="Sup3rSecret1")
            activity = ext.facade.create_activity(owner.id, {
                "type": "run", "distance_km": 5, "duration_min": 30,
                "date": date.today().isoformat(),
            })
            with pytest.raises(PermissionError):
                ext.facade.get_activity(activity.id, other.id)

    def test_get_activity_raises_for_unknown_id(self, app):
        with app.app_context():
            user = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            with pytest.raises(LookupError):
                ext.facade.get_activity("does-not-exist", user.id)


class TestFriends:

    def test_add_friend_is_bidirectional(self, app):
        with app.app_context():
            alice = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            bob = ext.facade.register(email="b@b.com", username="bob", password="Sup3rSecret1")
            ext.facade.add_friend(alice.id, bob.id)
            assert ext.facade.user_repository.is_friend(alice.id, bob.id)
            assert ext.facade.user_repository.is_friend(bob.id, alice.id)

    def test_add_friend_rejects_self(self, app):
        with app.app_context():
            alice = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            with pytest.raises(ValueError):
                ext.facade.add_friend(alice.id, alice.id)

    def test_add_friend_rejects_duplicate(self, app):
        with app.app_context():
            alice = ext.facade.register(email="a@a.com", username="alice", password="Sup3rSecret1")
            bob = ext.facade.register(email="b@b.com", username="bob", password="Sup3rSecret1")
            ext.facade.add_friend(alice.id, bob.id)
            with pytest.raises(ValueError):
                ext.facade.add_friend(alice.id, bob.id)
