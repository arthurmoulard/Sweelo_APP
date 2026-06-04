from app.models.report import Report
from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):

    def __init__(self):
        super().__init__(Report)

    def create(self, reporter_id, target_type, target_id, reason):
        report = Report(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
        )
        return self.save(report)

    def get_pending(self):
        return self.model.query.filter_by(status="pending").all()
