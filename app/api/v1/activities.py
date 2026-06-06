from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from app.extensions import facade
from app.models.activity import Activity

ns = Namespace("activities", description="Gestion des activités sportives")

activity_model = ns.model("Activity", {
    "type":         fields.String(required=True, enum=list(Activity.ACTIVITY_TYPES)),
    "distance_km":  fields.Float(description="Obligatoire pour run/bike/swim/walk/trail/triathlon/hyrox"),
    "duration_min": fields.Integer(required=True),
    "date":         fields.String(required=True, description="YYYY-MM-DD"),
    "notes":        fields.String(),
    "extra_data":   fields.Raw(description=(
        "Données spécifiques au sport. "
        "muscu: {weight_kg, sets, reps} | "
        "basket/hand/volley: {score, points} | "
        "foot/hand: {score, goals} | "
        "combat: {result: win/loss/draw, points}"
    )),
})


@ns.route("/")
class ActivityList(Resource):

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        page = int(request.args.get("page", 1))
        activities = facade.get_user_activities(user_id, page=page)
        return [a.to_dict() for a in activities], 200

    @jwt_required()
    @ns.expect(activity_model)
    @ns.response(201, "Activity created")
    @ns.response(400, "Invalid data")
    def post(self):
        user_id = get_jwt_identity()
        data = dict(ns.payload)
        activity_type = data.get("type")

        # Distance obligatoire pour les sports avec déplacement
        if activity_type not in Activity.NO_DISTANCE_TYPES and not data.get("distance_km"):
            ns.abort(400, f"distance_km is required for {activity_type}")

        # Distance ignorée pour les sports sans déplacement
        if activity_type in Activity.NO_DISTANCE_TYPES:
            data["distance_km"] = None

        try:
            activity = facade.create_activity(user_id, data)
            return activity.to_dict(), 201
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route("/<string:activity_id>")
class ActivityDetail(Resource):

    @jwt_required()
    def get(self, activity_id):
        user_id = get_jwt_identity()
        try:
            activity = facade.get_activity(activity_id, user_id)
            return activity.to_dict(), 200
        except LookupError as e:
            ns.abort(404, str(e))
        except PermissionError as e:
            ns.abort(403, str(e))

    @jwt_required()
    @ns.response(204, "Activity deleted")
    def delete(self, activity_id):
        user_id = get_jwt_identity()
        try:
            facade.delete_activity(activity_id, user_id)
            return "", 204
        except LookupError as e:
            ns.abort(404, str(e))
        except PermissionError as e:
            ns.abort(403, str(e))
