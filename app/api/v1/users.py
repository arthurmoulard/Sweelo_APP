from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import facade

ns = Namespace("users", description="Profil et amis")


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
        data["friends_count"] = user.friends.count()
        data["activities_count"] = user.activities.count()
        return data, 200


@ns.route("/me/stats")
class Stats(Resource):

    @jwt_required()
    @ns.response(200, "User stats")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        user_id = get_jwt_identity()
        return facade.get_user_stats(user_id), 200


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
        except (ValueError, LookupError) as e:
            ns.abort(400, str(e))
