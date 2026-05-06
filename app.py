import os
from flask import Flask, redirect, render_template, url_for, jsonify, flash, request
from extensions import db, jwt
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.documents import documents_bp
from routes.users import users_bp
from routes.rating import rating_bp
from routes.api.announcements import announcements_bp as api_announcements_bp
from routes.announcements import announcements_bp as web_announcements_bp
from routes.api.news import news_bp
from routes.api.chat import chat_bp
from routes.api.groups import groups_bp
from routes.api.attachments import attachments_bp
from routes.api.task_comments import task_comments_bp
from routes.api.tasks import api_tasks_bp
from routes.api.documents import api_documents_bp
from routes.api.auth import api_auth_bp
from dotenv import load_dotenv
from flask_cors import CORS
from flasgger import Swagger
from flask_migrate import Migrate
from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_identity, set_access_cookies,
)
load_dotenv()
from config import Config

# Import models so SQLAlchemy knows about them
from models.user import User
from models.role import Role
from models.task import Task, TaskUserAssignment
from models.document import Document
from models.award import Award
from models.announcement import Announcement
from models.news import News
from models.chat import GeneralChatMessage
from models.group import Group, UserGroup
from models.attachment import Attachment
from models.task_comment import TaskComment


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    app_version = os.getenv("APP_VERSION", "dev")

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Department Portal API",
            "version": app_version
        },
        "definitions": {
            "Announcement": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "deadline": {"type": "string", "format": "date"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "is_deleted": {"type": "boolean"}
                }
            },
            "AnnouncementInput": {
                "type": "object",
                "required": ["title", "text", "deadline"],
                "properties": {
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "deadline": {"type": "string", "format": "date", "example": "2026-06-01"}
                }
            },
            "News": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "is_pinned": {"type": "boolean"},
                    "is_deleted": {"type": "boolean"}
                }
            },
            "NewsInput": {
                "type": "object",
                "required": ["title", "text"],
                "properties": {
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "is_pinned": {"type": "boolean"}
                }
            },
            "ChatMessage": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "author_id": {"type": "integer"},
                    "author_name": {"type": "string"},
                    "text": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            "Group": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "role": {"type": "string"}
                }
            },
            "Attachment": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "task_id": {"type": "integer"},
                    "file_name": {"type": "string"},
                    "file_path": {"type": "string"},
                    "mime_type": {"type": "string"},
                    "size": {"type": "integer"},
                    "uploaded_at": {"type": "string"}
                }
            },
            "Document": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "filename": {"type": "string"},
                    "filepath": {"type": "string"},
                    "category": {"type": "string"},
                    "creator_id": {"type": "integer"},
                    "created_at": {"type": "string"}
                }
            },
            "TaskComment": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "task_id": {"type": "integer"},
                    "author_id": {"type": "integer"},
                    "author_name": {"type": "string"},
                    "recipient_id": {"type": "integer"},
                    "recipient_name": {"type": "string"},
                    "text": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            "Task": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "deadline_at": {"type": "string", "format": "date"},
                    "no_review": {"type": "boolean"},
                    "creator_id": {"type": "integer"},
                    "created_at": {"type": "string"}
                }
            },
            "TaskInput": {
                "type": "object",
                "required": ["title", "deadline_at"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "deadline_at": {"type": "string", "format": "date", "example": "2026-07-01"},
                    "no_review": {"type": "boolean", "default": False},
                    "assignees": {"type": "array", "items": {"type": "integer"}},
                    "group_ids": {"type": "array", "items": {"type": "integer"}}
                }
            },
            "TaskDetail": {
                "allOf": [
                    {"$ref": "#/definitions/Task"},
                    {
                        "type": "object",
                        "properties": {
                            "assignments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {"type": "integer"},
                                        "user_name": {"type": "string"},
                                        "status": {"type": "string"},
                                        "marked_complete": {"type": "boolean"},
                                        "approved": {"type": "boolean"},
                                        "completed_at": {"type": "string"},
                                        "approved_at": {"type": "string"}
                                    }
                                }
                            },
                            "groups": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/Group"}
                            }
                        }
                    }
                ]
            },
            "LoginInput": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "example": "user@example.com"},
                    "password": {"type": "string", "example": "secret123"}
                }
            },
            "LoginResponse": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "user": {"$ref": "#/definitions/User"}
                }
            }
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Format: Bearer {token}"
            }
        },
        "security": [{"BearerAuth": []}]
    }

    Swagger(app, template=swagger_template)

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(rating_bp)

    app.register_blueprint(api_announcements_bp)
    app.register_blueprint(web_announcements_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(task_comments_bp)
    app.register_blueprint(api_tasks_bp)
    app.register_blueprint(api_documents_bp)
    app.register_blueprint(api_auth_bp)

    @app.route('/')
    @jwt_required()
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
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Требуется авторизация"}), 401
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Недействительный токен"}), 401
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Токен истёк"}), 401
        flash("Требуется авторизация", "warning")
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
