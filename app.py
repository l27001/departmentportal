from flask import Flask, redirect, render_template, url_for, jsonify, flash
from extensions import db, jwt
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.documents import documents_bp
from routes.users import users_bp
from routes.rating import rating_bp
from dotenv import load_dotenv
from flask_cors import CORS
from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_identity, set_access_cookies,
)
load_dotenv()
from config import Config


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(rating_bp)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template("index.html")
        # return redirect(url_for("tasks.list_tasks"))

    @app.route('/token-refresh', methods=['GET'])
    @jwt_required()
    def refresh():
        # Create the new access token
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)

        # Set the JWT access cookie in the response
        resp = jsonify({'refresh': True})
        set_access_cookies(resp, access_token)
        return resp, 200

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
