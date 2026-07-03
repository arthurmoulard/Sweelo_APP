from app.models.user import User


class TestUserPassword:

    def test_set_password_hashes_value(self, app):
        with app.app_context():
            user = User(email="a@a.com", username="alice")
            user.set_password("Sup3rSecret1")
            assert user.password_hash != "Sup3rSecret1"

    def test_check_password_accepts_correct_password(self, app):
        with app.app_context():
            user = User(email="a@a.com", username="alice")
            user.set_password("Sup3rSecret1")
            assert user.check_password("Sup3rSecret1") is True

    def test_check_password_rejects_wrong_password(self, app):
        with app.app_context():
            user = User(email="a@a.com", username="alice")
            user.set_password("Sup3rSecret1")
            assert user.check_password("wrong-password") is False


class TestUserToDict:

    def test_to_dict_exposes_public_fields_only(self, app):
        with app.app_context():
            user = User(email="a@a.com", username="alice")
            user.set_password("Sup3rSecret1")
            user.save()

            data = user.to_dict()

            assert data["email"] == "a@a.com"
            assert data["username"] == "alice"
            assert data["is_admin"] is False
            assert data["is_banned"] is False
            assert "password_hash" not in data
