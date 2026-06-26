import os
import uuid
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, request as flask_request
from app.extensions import facade

UPLOAD_DIR   = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'frontend', 'uploads')
FRONTEND_URL = 'http://localhost:8080'
ALLOWED_EXT  = {'jpg', 'jpeg', 'png', 'webp', 'gif'}

ns = Namespace("users", description="Profil et amis")

update_profile_model = ns.model("UpdateProfile", {
    "username": fields.String(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_-]+$"),
    "email":    fields.String(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "password": fields.String(min_length=8),
})


@ns.route("/me")
class Me(Resource):

    @jwt_required()
    @ns.response(200, "User profile")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "User not found")
    def get(self):
        user_id = get_jwt_identity()
        user = facade.user_repository.get_by_id(user_id)
        if not user:
            ns.abort(404, "User not found")
        data = user.to_dict()
        data["friends_count"]    = user.friends.count()
        data["activities_count"] = user.activities.count()
        return data, 200

    @jwt_required()
    @ns.expect(update_profile_model, validate=True)
    @ns.response(200, "Profile updated")
    @ns.response(400, "Validation error")
    @ns.response(401, "Missing or invalid token")
    @ns.response(409, "Email or username already used")
    def put(self):
        """Met à jour le profil de l'utilisateur connecté."""
        user_id = get_jwt_identity()
        try:
            user = facade.update_profile(user_id, ns.payload)
            return user.to_dict(), 200
        except ValueError as e:
            ns.abort(409, str(e))


@ns.route("/me/avatar")
class MyAvatar(Resource):

    @jwt_required()
    @ns.response(200, "Avatar uploaded")
    @ns.response(400, "Invalid file")
    @ns.response(401, "Missing or invalid token")
    def post(self):
        """Upload ou remplace la photo de profil (multipart/form-data, champ 'avatar')."""
        user_id = get_jwt_identity()
        user = facade.user_repository.get_by_id(user_id)
        if not user:
            ns.abort(404, "User not found")

        file = flask_request.files.get('avatar')
        if not file or not file.filename:
            ns.abort(400, "No file provided")

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXT:
            ns.abort(400, f"File type not allowed. Use: {', '.join(ALLOWED_EXT)}")

        # Supprime l'ancienne photo de profil si elle existe
        if user.avatar_url and '/uploads/' in user.avatar_url:
            rel = user.avatar_url.split('/uploads/', 1)[-1]
            old_path = os.path.join(UPLOAD_DIR, rel)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Sauvegarde la nouvelle photo dans uploads/avatars/
        filename  = f"avatar_{uuid.uuid4().hex}.{ext}"
        avatar_dir = os.path.join(UPLOAD_DIR, 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        file.save(os.path.join(avatar_dir, filename))

        user.avatar_url = f"{FRONTEND_URL}/uploads/avatars/{filename}"
        facade.user_repository.save(user)

        return {"avatar_url": user.avatar_url}, 200

    @jwt_required()
    @ns.response(204, "Avatar deleted")
    @ns.response(401, "Missing or invalid token")
    def delete(self):
        """Supprime la photo de profil."""
        user_id = get_jwt_identity()
        user = facade.user_repository.get_by_id(user_id)
        if not user:
            ns.abort(404, "User not found")

        if user.avatar_url and '/uploads/' in user.avatar_url:
            rel = user.avatar_url.split('/uploads/', 1)[-1]
            path = os.path.join(UPLOAD_DIR, rel)
            if os.path.exists(path):
                os.remove(path)
            user.avatar_url = None
            facade.user_repository.save(user)

        return "", 204


@ns.route("/me/stats")
class Stats(Resource):

    @jwt_required()
    @ns.response(200, "User stats")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        user_id = get_jwt_identity()
        return facade.get_user_stats(user_id), 200


@ns.route("/me/friends")
class FriendList(Resource):

    @jwt_required()
    @ns.response(200, "List of friends")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        user_id = get_jwt_identity()
        user = facade.user_repository.get_by_id(user_id)
        return [{"id": f.id, "username": f.username} for f in user.friends.all()], 200


@ns.route("/search")
class UserSearch(Resource):

    @jwt_required()
    @ns.response(200, "Search results")
    @ns.response(400, "Query too short")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        """Cherche des utilisateurs par username. Param: ?q=<query>"""
        user_id = get_jwt_identity()
        q = request.args.get("q", "")
        try:
            users = facade.search_users(q, current_user_id=user_id)
            return [{"id": u.id, "username": u.username} for u in users], 200
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route("/<string:user_id>")
class UserProfile(Resource):

    @jwt_required()
    @ns.response(200, "Public user profile")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "User not found")
    def get(self, user_id):
        """Profil public d'un autre utilisateur."""
        try:
            return facade.get_public_profile(user_id), 200
        except LookupError as e:
            ns.abort(404, str(e))


@ns.route("/<string:friend_id>/friend")
class Friend(Resource):

    @jwt_required()
    @ns.response(200, "Friend added")
    @ns.response(400, "Cannot add yourself or already friends")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "User not found")
    def post(self, friend_id):
        user_id = get_jwt_identity()
        try:
            facade.add_friend(user_id, friend_id)
            return {"message": "Friend added"}, 200
        except LookupError as e:
            ns.abort(404, str(e))
        except ValueError as e:
            ns.abort(400, str(e))

    @jwt_required()
    @ns.response(200, "Friend removed")
    @ns.response(401, "Missing or invalid token")
    @ns.response(404, "Friend not found")
    def delete(self, friend_id):
        user_id = get_jwt_identity()
        try:
            facade.remove_friend(user_id, friend_id)
            return {"message": "Friend removed"}, 200
        except LookupError as e:
            ns.abort(404, str(e))
