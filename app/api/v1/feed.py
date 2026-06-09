from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import facade

ns = Namespace("feed", description="Feed social et interactions")

comment_model = ns.model("Comment", {
    "content": fields.String(required=True, min_length=1, max_length=500),
})

report_model = ns.model("Report", {
    "reason": fields.String(max_length=255),
})


@ns.route("/")
class Feed(Resource):

    @jwt_required()
    @ns.response(200, "List of posts")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        from flask import request
        user_id = get_jwt_identity()
        page = int(request.args.get("page", 1))
        posts = facade.get_feed(user_id, page=page)
        return [p.to_dict(current_user_id=user_id) for p in posts], 200


@ns.route("/<string:post_id>/like")
class Like(Resource):

    @jwt_required()
    @ns.response(200, "Like toggled (liked or unliked)")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Post not found")
    def post(self, post_id):
        user_id = get_jwt_identity()
        try:
            result = facade.like_post(post_id, user_id)
            return result, 200
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/<string:post_id>/comments")
class Comments(Resource):

    @jwt_required()
    @ns.expect(comment_model, validate=True)
    @ns.response(201, "Comment created")
    @ns.response(400, "Content rejected by moderation")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Post not found")
    def post(self, post_id):
        user_id = get_jwt_identity()
        try:
            comment = facade.create_comment(post_id, user_id, ns.payload["content"])
            return comment.to_dict(), 201
        except LookupError as e:
            ns.abort(404, str(e))
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route("/<string:post_id>/report")
class ReportPost(Resource):

    @jwt_required()
    @ns.expect(report_model, validate=True)
    @ns.response(200, "Report submitted")
    @ns.response(400, "Validation error")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Post not found")
    def post(self, post_id):
        user_id = get_jwt_identity()
        facade.report_content(
            reporter_id=user_id,
            target_type="post",
            target_id=post_id,
            reason=(ns.payload or {}).get("reason", ""),
        )
        return {"message": "Report submitted"}, 200


@ns.route("/comments/<string:comment_id>/report")
class ReportComment(Resource):

    @jwt_required()
    @ns.expect(report_model, validate=True)
    @ns.response(200, "Report submitted")
    @ns.response(400, "Validation error")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Comment not found")
    def post(self, comment_id):
        from app.models.comment import Comment
        user_id = get_jwt_identity()
        if not Comment.query.get(comment_id):
            ns.abort(404, "Comment not found")
        facade.report_content(
            reporter_id=user_id,
            target_type="comment",
            target_id=comment_id,
            reason=(ns.payload or {}).get("reason", ""),
        )
        return {"message": "Report submitted"}, 200
