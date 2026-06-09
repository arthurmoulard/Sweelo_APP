from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token
from app.extensions import facade

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
            token = create_access_token(identity=user.id, additional_claims={"is_admin": user.is_admin})
            return {"access_token": token}, 200
        except (ValueError, PermissionError) as e:
            ns.abort(401, str(e))
