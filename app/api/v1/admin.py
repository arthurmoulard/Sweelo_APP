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
    @ns.response(200, "List of pending reports")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    def get(self):
        admin_required()
        reports = facade.report_repository.get_pending()
        return [r.to_dict() for r in reports], 200


@ns.route("/reports/<string:report_id>")
class ReportDetail(Resource):

    @jwt_required()
    @ns.expect(report_action_model, validate=True)
    @ns.response(200, "Report updated")
    @ns.response(400, "Invalid action or report not found")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    @ns.response(404, "Report not found")
    def put(self, report_id):
        admin_required()
        try:
            report = facade.update_report(report_id, ns.payload["action"])
            return report.to_dict(), 200
        except LookupError as e:
            ns.abort(404, str(e))
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route("/users/<string:user_id>/ban")
class BanUser(Resource):

    @jwt_required()
    @ns.response(200, "User banned")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    @ns.response(404, "User not found")
    def post(self, user_id):
        admin_required()
        try:
            facade.ban_user(user_id)
            return {"message": "User banned"}, 200
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/users/<string:user_id>/unban")
class UnbanUser(Resource):

    @jwt_required()
    @ns.response(200, "User unbanned")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    @ns.response(404, "User not found")
    def post(self, user_id):
        admin_required()
        try:
            facade.unban_user(user_id)
            return {"message": "User unbanned"}, 200
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/posts/<string:post_id>")
class DeletePost(Resource):

    @jwt_required()
    @ns.response(204, "Post deleted")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    @ns.response(404, "Post not found")
    def delete(self, post_id):
        admin_required()
        try:
            facade.delete_post(post_id)
            return "", 204
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/comments/<string:comment_id>")
class DeleteComment(Resource):

    @jwt_required()
    @ns.response(204, "Comment deleted")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Admin access required")
    @ns.response(404, "Comment not found")
    def delete(self, comment_id):
        admin_required()
        from app.models.comment import Comment
        comment = Comment.query.get(comment_id)
        if not comment:
            ns.abort(404, "Comment not found")
        comment.delete()
        return "", 204
