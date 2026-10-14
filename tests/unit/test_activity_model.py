from datetime import date

from app.models.activity import Activity
from app.models.user import User


def _make_user():
    user = User(email="runner@sweelo.io", username="runner")
    user.set_password("Sup3rSecret1")
    return user.save()


class TestActivityToDict:

    def test_to_dict_includes_core_fields(self, app):
        with app.app_context():
            user = _make_user()
            activity = Activity(
                user_id=user.id, type="run", distance_km=10.5,
                duration_min=60, date=date(2026, 5, 1), notes="Bon rythme",
            ).save()

            data = activity.to_dict()

            assert data["type"] == "run"
            assert data["distance_km"] == 10.5
            assert data["duration_min"] == 60
            assert data["date"] == "2026-05-01"
            assert data["notes"] == "Bon rythme"
            assert data["post_id"] is None

    def test_no_distance_type_allows_null_distance(self, app):
        with app.app_context():
            user = _make_user()
            activity = Activity(
                user_id=user.id, type="muscu", distance_km=None,
                duration_min=45, date=date.today(),
            ).save()

            assert activity.distance_km is None


class TestActivityTypes:

    def test_no_distance_types_are_a_subset_of_activity_types(self):
        assert Activity.NO_DISTANCE_TYPES.issubset(set(Activity.ACTIVITY_TYPES))

    def test_run_requires_distance(self):
        assert "run" not in Activity.NO_DISTANCE_TYPES

    def test_muscu_does_not_require_distance(self):
        assert "muscu" in Activity.NO_DISTANCE_TYPES
