from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
)
from app.extensions import facade, db

ns = Namespace("auth", description="Inscription et connexion")

register_model = ns.model("Register", {
    "email":    fields.String(required=True, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "username": fields.String(required=True, min_length=3, max_length=30,
                              pattern=r"^[a-zA-Z0-9_-]+$"),
    "password": fields.String(required=True, min_length=8),
})

login_model = ns.model("Login", {
    "email":    fields.String(required=True),
    "password": fields.String(required=True),
})


@ns.route("/register")
class Register(Resource):

    @ns.expect(register_model, validate=True)
    @ns.response(201, "User created")
    @ns.response(400, "Validation error")
    @ns.response(409, "Email or username already used")
    def post(self):
        data = ns.payload
        try:
            user = facade.register(
                email=data["email"].strip().lower(),
                username=data["username"].strip(),
                password=data["password"],
            )
            return user.to_dict(), 201
        except ValueError as e:
            ns.abort(409, str(e))


@ns.route("/login")
class Login(Resource):

    @ns.expect(login_model, validate=True)
    @ns.response(200, "Login successful")
    @ns.response(400, "Validation error")
    @ns.response(401, "Invalid credentials or account banned")
    def post(self):
        data = ns.payload
        try:
            user = facade.login(email=data["email"], password=data["password"])
            claims = {"is_admin": user.is_admin}
            return {
                "access_token":  create_access_token(identity=user.id, additional_claims=claims),
                "refresh_token": create_refresh_token(identity=user.id, additional_claims=claims),
            }, 200
        except (ValueError, PermissionError) as e:
            ns.abort(401, str(e))


@ns.route("/refresh")
class Refresh(Resource):

    @jwt_required(refresh=True)
    @ns.response(200, "New access token")
    @ns.response(401, "Invalid or expired refresh token")
    def post(self):
        """Échange un refresh token contre un nouvel access token."""
        user_id = get_jwt_identity()
        user = facade.user_repository.get_by_id(user_id)
        if not user or user.is_banned:
            ns.abort(401, "Account unavailable")
        claims = {"is_admin": user.is_admin}
        return {"access_token": create_access_token(identity=user_id, additional_claims=claims)}, 200


@ns.route("/logout")
class Logout(Resource):

    @jwt_required()
    @ns.response(200, "Logged out")
    @ns.response(401, "Missing or invalid token")
    def post(self):
        """Révoque le token courant (l'ajoute à la blocklist)."""
        from app.models.token_blocklist import TokenBlocklist
        jti = get_jwt()["jti"]
        db.session.add(TokenBlocklist(jti=jti))
        db.session.commit()
        return {"message": "Logged out"}, 200
