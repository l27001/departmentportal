from datetime import date

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
from routes.api.meetings import meetings_bp as api_meetings_bp
from routes.meetings import meetings_bp as web_meetings_bp
from routes.news import news_bp as web_news_bp
from routes.chat import chat_bp as web_chat_bp
from routes.admin import admin_bp
from routes.api.admin_users import admin_users_bp
from routes.api.categories import categories_bp
from routes.about import about_bp
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
from models.document import Document, DocumentLink
from models.award import Award
from models.announcement import Announcement
from models.news import News
from models.category import Category
from models.chat import GeneralChatMessage
from models.group import Group, UserGroup
from models.attachment import Attachment
from models.task_comment import TaskComment
from models.meeting import DepartmentMeeting, MeetingTask
from models.about import GalleryAlbum, GalleryPhoto


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    app.json.sort_keys = False

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
                    "creator_id": {"type": "integer"},
                    "creator_name": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "is_deleted": {"type": "boolean"},
                    "view_count": {"type": "integer"},
                    "require_rsvp": {"type": "boolean"},
                    "rsvp_count": {"type": "integer"}
                }
            },
            "AnnouncementInput": {
                "type": "object",
                "required": ["title", "text", "deadline"],
                "properties": {
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "deadline": {"type": "string", "format": "date", "example": "2026-06-01"},
                    "require_rsvp": {"type": "boolean"}
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
                    "created_at": {"type": "string"},
                    "attachments": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Attachment"}
                    }
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
                    "news_id": {"type": "integer"},
                    "announcement_id": {"type": "integer"},
                    "document_id": {"type": "integer"},
                    "meeting_id": {"type": "integer"},
                    "chat_message_id": {"type": "integer"},
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

    if os.getenv("FLASK_ENV") == "development":
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
    app.register_blueprint(about_bp)

    app.register_blueprint(api_announcements_bp)
    app.register_blueprint(web_announcements_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(web_news_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(task_comments_bp)
    app.register_blueprint(api_tasks_bp)
    app.register_blueprint(api_documents_bp)
    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_meetings_bp)
    app.register_blueprint(web_meetings_bp)
    app.register_blueprint(web_chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(categories_bp)

    @app.context_processor
    def inject_user():
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(user_id)
                if user:
                    return {'current_user': user}
        except:
            pass
        return {'current_user': None}

    @app.route('/')
    @jwt_required()
    def index():
        recent_news = News.query.filter_by(is_deleted=False).order_by(News.is_pinned.desc(), News.created_at.desc()).limit(5).all()
        return render_template("index.html", news=recent_news)

    @app.route('/token-refresh', methods=['GET'])
    @jwt_required()
    def refresh():
        current_user = get_jwt_identity()
        user = User.query.get(current_user)
        access_token = create_access_token(
            identity=current_user,
            additional_claims={"role": user.role.id}
        )
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

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        user_id = jwt_payload.get("sub")
        if user_id:
            user = User.query.get(user_id)
            if user and (not user.is_active or (user.dismissal_date and user.dismissal_date <= date.today())):
                return True
        return False

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Аккаунт деактивирован"}), 401
        flash("Ваш аккаунт деактивирован", "danger")
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Не найдено"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Внутренняя ошибка сервера"}), 500
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
