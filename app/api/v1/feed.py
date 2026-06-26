import os
import uuid
from flask import request as flask_request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import facade

# Dossier de stockage local des photos (servi par le frontend HTTP server)
UPLOAD_DIR   = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'frontend', 'uploads')
FRONTEND_URL = 'http://localhost:8080'
ALLOWED_EXT  = {'jpg', 'jpeg', 'png', 'webp', 'gif'}

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
    @ns.response(200, "Paginated feed")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        from flask import request
        user_id = get_jwt_identity()
        page = int(request.args.get("page", 1))
        return facade.get_feed(user_id, page=page), 200


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
    @ns.response(200, "List of comments")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Post not found")
    def get(self, post_id):
        from flask import request as req
        page = int(req.args.get("page", 1))
        try:
            return facade.get_post_comments(post_id, page), 200
        except LookupError as e:
            ns.abort(404, str(e))

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


@ns.route("/comments/<string:comment_id>")
class CommentDetail(Resource):

    @jwt_required()
    @ns.response(204, "Comment deleted")
    @ns.response(401, "Missing or invalid token")
    @ns.response(403, "Not your comment")
    @ns.response(404, "Comment not found")
    def delete(self, comment_id):
        """Supprime son propre commentaire."""
        user_id = get_jwt_identity()
        try:
            facade.delete_comment(comment_id, user_id)
            return "", 204
        except LookupError as e:
            ns.abort(404, str(e))
        except PermissionError as e:
            ns.abort(403, str(e))


@ns.route("/<string:post_id>/report")
class ReportPost(Resource):

    @jwt_required()
    @ns.expect(report_model, validate=True)
    @ns.response(200, "Report submitted")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Post not found")
    def post(self, post_id):
        from app.models.feed_post import FeedPost
        user_id = get_jwt_identity()
        if not FeedPost.query.get(post_id):
            ns.abort(404, "Post not found")
        facade.report_content(
            reporter_id=user_id,
            target_type="post",
            target_id=post_id,
            reason=(ns.payload or {}).get("reason", ""),
        )
        return {"message": "Report submitted"}, 200


@ns.route("/<string:post_id>/photo")
class PostPhoto(Resource):

    @jwt_required()
    @ns.response(200, "Photo uploaded")
    @ns.response(400, "Invalid file")
    @ns.response(403, "Not your post")
    @ns.response(404, "Post not found")
    def post(self, post_id):
        """Upload ou remplace la photo d'un post (multipart/form-data, champ 'photo')."""
        user_id = get_jwt_identity()
        post = facade.feed_repository.get_post(post_id)
        if not post:
            ns.abort(404, "Post not found")
        if post.user_id != user_id:
            ns.abort(403, "Not your post")

        file = flask_request.files.get('photo')
        if not file or not file.filename:
            ns.abort(400, "No file provided")

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXT:
            ns.abort(400, f"File type not allowed. Use: {', '.join(ALLOWED_EXT)}")

        # Supprime l'ancienne photo si elle existe
        if post.photo_url:
            old_name = post.photo_url.split('/uploads/')[-1]
            old_path = os.path.join(UPLOAD_DIR, old_name)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Sauvegarde la nouvelle photo avec un nom unique
        filename = f"{uuid.uuid4().hex}.{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file.save(os.path.join(UPLOAD_DIR, filename))

        post.photo_url = f"{FRONTEND_URL}/uploads/{filename}"
        post.photo_public_id = filename
        facade.feed_repository.save(post)

        return {"photo_url": post.photo_url}, 200

    @jwt_required()
    @ns.response(204, "Photo deleted")
    @ns.response(403, "Not your post")
    @ns.response(404, "Post not found")
    def delete(self, post_id):
        """Supprime la photo d'un post."""
        user_id = get_jwt_identity()
        post = facade.feed_repository.get_post(post_id)
        if not post:
            ns.abort(404, "Post not found")
        if post.user_id != user_id:
            ns.abort(403, "Not your post")

        if post.photo_url:
            filename = post.photo_url.split('/uploads/')[-1]
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(path):
                os.remove(path)
            post.photo_url       = None
            post.photo_public_id = None
            facade.feed_repository.save(post)

        return "", 204


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
