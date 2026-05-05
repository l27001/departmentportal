from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.announcement import Announcement
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

    announcement = Announcement(title=title, text=text, deadline=deadline)
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
