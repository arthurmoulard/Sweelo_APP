from sqlalchemy import func
from app.models.activity import Activity
from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):

    def __init__(self):
        super().__init__(Activity)

    # Champs qu'un client a le droit de renseigner : id, user_id, created_at…
    # sont fixés par le serveur et ignorés s'ils arrivent dans le JSON (mass assignment).
    CREATABLE_FIELDS = {"type", "distance_km", "duration_min", "calories", "date", "notes", "extra_data"}

    def create(self, user_id, data):
        safe_data = {k: v for k, v in data.items() if k in self.CREATABLE_FIELDS}
        activity = Activity(user_id=user_id, **safe_data)
        return self.save(activity)

    def get_by_user(self, user_id, page=1, limit=20):
        return (
            self.model.query
            .filter_by(user_id=user_id)
            .order_by(Activity.date.desc())
            .paginate(page=page, per_page=limit, error_out=False)
        )

    def update(self, activity, data):
        allowed = {"distance_km", "duration_min", "date", "notes", "extra_data"}
        for key, value in data.items():
            if key in allowed:
                setattr(activity, key, value)
        from app.extensions import db
        db.session.commit()
        return activity

    def get_stats(self, user_id):
        result = (
            self.model.query
            .with_entities(
                func.coalesce(func.sum(Activity.distance_km), 0),
                func.coalesce(func.sum(Activity.duration_min), 0),
                func.count(Activity.id),
            )
            .filter_by(user_id=user_id)
            .first()
        )
        # MySQL renvoie SUM() sous forme de Decimal, que le JSON ne sait pas
        # sérialiser (SQLite renvoie un float) : on convertit explicitement.
        return {
            "total_km":    round(float(result[0]), 2),
            "total_min":   int(result[1]),
            "total_count": int(result[2]),
        }
