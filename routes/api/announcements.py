from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.announcement import Announcement, AnnouncementView
from models.user import User
from datetime import date

announcements_bp = Blueprint("api_announcements", __name__, url_prefix="/api/announcements")


@announcements_bp.route("/", methods=["GET"])
@jwt_required()
def list_announcements():
    """Получить все объявления
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Список объявлений
        schema:
          type: array
          items:
            $ref: '#/definitions/Announcement'
    """
    announcements = Announcement.query.filter_by(is_deleted=False).order_by(Announcement.created_at.desc()).all()
    return jsonify([a.to_dict() for a in announcements])


@announcements_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_announcement(id):
    """Получить объявление по ID
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Объявление
        schema:
          $ref: '#/definitions/Announcement'
      404:
        description: Не найдено
    """
    announcement = Announcement.query.filter_by(id=id, is_deleted=False).first_or_404()
    return jsonify(announcement.to_dict())


@announcements_bp.route("/", methods=["POST"])
@jwt_required()
def create_announcement():
    """Создать объявление (только Руководитель/Документовед)
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/AnnouncementInput'
    responses:
      201:
        description: Объявление создано
        schema:
          $ref: '#/definitions/Announcement'
      400:
        description: Ошибка валидации
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    user_id = get_jwt_identity()

    data = request.json
    title = data.get("title")
    text = data.get("text")
    deadline_str = data.get("deadline")

    if not title or not text or not deadline_str:
        return jsonify({"msg": "Заполните все поля"}), 400

    try:
        deadline = date.fromisoformat(deadline_str)
    except ValueError:
        return jsonify({"msg": "Неверный формат даты"}), 400

    announcement = Announcement(title=title, text=text, deadline=deadline, creator_id=user_id)
    db.session.add(announcement)
    db.session.commit()

    return jsonify(announcement.to_dict()), 201


@announcements_bp.route("/<int:id>", methods=["PATCH"])
@jwt_required()
def update_announcement(id):
    """Обновить объявление (только Руководитель/Документовед)
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            text:
              type: string
            deadline:
              type: string
              format: date
    responses:
      200:
        description: Объявление обновлено
        schema:
          $ref: '#/definitions/Announcement'
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    announcement = Announcement.query.filter_by(id=id, is_deleted=False).first_or_404()
    data = request.json

    if "title" in data:
        announcement.title = data["title"]
    if "text" in data:
        announcement.text = data["text"]
    if "deadline" in data:
        try:
            announcement.deadline = date.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"msg": "Неверный формат даты"}), 400

    db.session.commit()
    return jsonify(announcement.to_dict())


@announcements_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_announcement(id):
    """Удалить объявление (soft delete)
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Объявление удалено
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    announcement = Announcement.query.filter_by(id=id, is_deleted=False).first_or_404()
    announcement.is_deleted = True
    db.session.commit()
    return jsonify({"msg": "Объявление удалено"})


@announcements_bp.route("/<int:id>/view", methods=["POST"])
@jwt_required()
def mark_viewed(id):
    """Отметить объявление как просмотренное
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Просмотр отмечен
      404:
        description: Не найдено
    """
    user_id = get_jwt_identity()
    announcement = Announcement.query.filter_by(id=id, is_deleted=False).first_or_404()

    existing = AnnouncementView.query.filter_by(announcement_id=id, user_id=user_id).first()
    if not existing:
        view = AnnouncementView(announcement_id=id, user_id=user_id)
        db.session.add(view)
        db.session.commit()

    return jsonify({"msg": "Просмотр отмечен"})


@announcements_bp.route("/<int:id>/views", methods=["GET"])
@jwt_required()
def get_views(id):
    """Получить список просмотров объявления (только Руководитель/Документовед)
    ---
    tags: [Announcements]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Список просмотров
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    views = AnnouncementView.query.filter_by(announcement_id=id).order_by(AnnouncementView.viewed_at.desc()).all()
    return jsonify([{
        "user_id": v.user_id,
        "user_name": v.user.name if v.user else None,
        "viewed_at": v.viewed_at.isoformat() if v.viewed_at else None,
    } for v in views])


@announcements_bp.route("/<int:id>/read-status", methods=["GET"])
@jwt_required()
def get_read_status(id):
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    announcement = Announcement.query.filter_by(id=id, is_deleted=False).first_or_404()

    viewed_ids = {v.user_id for v in AnnouncementView.query.filter_by(announcement_id=id).all()}
    active_users = User.query.filter(User.dismissal_date.is_(None)).order_by(User.name).all()

    read = []
    unread = []
    for u in active_users:
        entry = {"user_id": u.id, "user_name": u.name}
        if u.id in viewed_ids:
            read.append(entry)
        else:
            unread.append(entry)

    return jsonify({"read": read, "unread": unread})
