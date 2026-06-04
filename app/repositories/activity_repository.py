from sqlalchemy import func
from app.models.activity import Activity
from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository):

    def __init__(self):
        super().__init__(Activity)

    def create(self, user_id, **data):
        activity = Activity(user_id=user_id, **data)
        return self.save(activity)

    def get_by_user(self, user_id, page=1, limit=20):
        return (
            self.model.query
            .filter_by(user_id=user_id)
            .order_by(Activity.date.desc())
            .paginate(page=page, per_page=limit, error_out=False)
            .items
        )

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
        return {
            "total_km":    round(result[0], 2),
            "total_min":   result[1],
            "total_count": result[2],
        }
