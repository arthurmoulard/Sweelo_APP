from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import facade

ns = Namespace("feed", description="Feed social et interactions")

comment_model = ns.model("Comment", {
    "content": fields.String(required=True),
})

report_model = ns.model("Report", {
    "target_type": fields.String(required=True, enum=["post", "comment"]),
    "reason":      fields.String(),
})


@ns.route("/")
class Feed(Resource):

    @jwt_required()
    def get(self):
        from flask import request
        user_id = get_jwt_identity()
        page = int(request.args.get("page", 1))
        posts = facade.get_feed(user_id, page=page)
        return [p.to_dict(current_user_id=user_id) for p in posts], 200


@ns.route("/<string:post_id>/like")
class Like(Resource):

    @jwt_required()
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
    @ns.expect(comment_model)
    @ns.response(201, "Comment created")
    @ns.response(400, "Content rejected by moderation")
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
    @ns.expect(report_model)
    def post(self, post_id):
        user_id = get_jwt_identity()
        facade.report_content(
            reporter_id=user_id,
            target_type=ns.payload.get("target_type", "post"),
            target_id=post_id,
            reason=ns.payload.get("reason", ""),
        )
        return {"message": "Report submitted"}, 200
