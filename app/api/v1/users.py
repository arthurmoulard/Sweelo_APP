from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from app.extensions import facade

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
