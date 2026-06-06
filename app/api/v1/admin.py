from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import facade

ns = Namespace("admin", description="Administration et modération")

report_action_model = ns.model("ReportAction", {
    "action": fields.String(required=True, enum=["reviewed", "dismissed"]),
})


def admin_required():
    claims = get_jwt()
    if not claims.get("is_admin"):
        ns.abort(403, "Admin access required")


@ns.route("/reports")
class Reports(Resource):

    @jwt_required()
    def get(self):
        admin_required()
        reports = facade.report_repository.get_pending()
        return [r.to_dict() for r in reports], 200


@ns.route("/reports/<string:report_id>")
class ReportDetail(Resource):

    @jwt_required()
    @ns.expect(report_action_model)
    def put(self, report_id):
        admin_required()
        try:
            report = facade.update_report(report_id, ns.payload["action"])
            return report.to_dict(), 200
        except (LookupError, ValueError) as e:
            ns.abort(400, str(e))


@ns.route("/users/<string:user_id>/ban")
class BanUser(Resource):

    @jwt_required()
    def post(self, user_id):
        admin_required()
        try:
            facade.ban_user(user_id)
            return {"message": "User banned"}, 200
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/comments/<string:comment_id>")
class DeleteComment(Resource):

    @jwt_required()
    def delete(self, comment_id):
        admin_required()
        from app.models.comment import Comment
        comment = Comment.query.get(comment_id)
        if not comment:
            ns.abort(404, "Comment not found")
        comment.delete()
        return "", 204
