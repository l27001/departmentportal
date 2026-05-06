import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, allowed_file
from models.attachment import Attachment
from models.task import Task
from models.news import News
from models.announcement import Announcement
from models.document import Document
from models.meeting import DepartmentMeeting

attachments_bp = Blueprint("api_attachments", __name__, url_prefix="/api")


@attachments_bp.route("/tasks/<int:task_id>/attachments", methods=["GET"])
@jwt_required()
def list_attachments(task_id):
    """Получить вложения задачи
    ---
    tags: [Attachments]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Список вложений
        schema:
          type: array
          items:
            $ref: '#/definitions/Attachment'
    """
    Task.query.get_or_404(task_id)
    attachments = Attachment.query.filter_by(task_id=task_id).order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([a.to_dict() for a in attachments])


@attachments_bp.route("/tasks/<int:task_id>/attachments", methods=["POST"])
@jwt_required()
def upload_attachment(task_id):
    """Загрузить вложение к задаче
    ---
    tags: [Attachments]
    security:
      - BearerAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: file
        in: formData
        type: file
        required: true
    responses:
      201:
        description: Вложение загружено
        schema:
          $ref: '#/definitions/Attachment'
      400:
        description: Ошибка загрузки файла
    """
    Task.query.get_or_404(task_id)
    if "file" not in request.files:
        return jsonify({"msg": "Файл не найден"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "Файл не выбран"}), 400

    if not allowed_file(file.filename, current_app.config):
        return jsonify({"msg": "Недопустимый тип файла"}), 400

    original_name = file.filename
    ext = os.path.splitext(original_name)[1] if '.' in original_name else ''
    safe_filename = str(uuid.uuid4()) + ext
    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "attachments", str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, safe_filename)

    file.save(save_path)
    file_size = os.path.getsize(save_path)

    mime_type = file.content_type or "application/octet-stream"
    attachment = Attachment(
        task_id=task_id,
        file_name=original_name,
        file_path=save_path,
        mime_type=mime_type,
        size=file_size,
    )
    db.session.add(attachment)
    db.session.commit()

    return jsonify(attachment.to_dict()), 201


@attachments_bp.route("/attachments/<int:id>", methods=["GET"])
@jwt_required()
def download_attachment(id):
    """Скачать вложение
    ---
    tags: [Attachments]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Файл
        schema:
          type: file
      404:
        description: Не найдено
    """
    attachment = Attachment.query.get_or_404(id)
    if not os.path.exists(attachment.file_path):
        return jsonify({"msg": "Файл не найден на сервере"}), 404

    return send_file(attachment.file_path, mimetype=attachment.mime_type, as_attachment=True, download_name=attachment.file_name)


@attachments_bp.route("/attachments/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_attachment(id):
    """Удалить вложение
    ---
    tags: [Attachments]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Вложение удалено
      404:
        description: Не найдено
    """
    attachment = Attachment.query.get_or_404(id)
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    db.session.delete(attachment)
    db.session.commit()
    return jsonify({"msg": "Вложение удалено"})


def _upload_attachment(entity_model, entity_id):
    entity = entity_model.query.get_or_404(entity_id)
    if "file" not in request.files:
        return jsonify({"msg": "Файл не найден"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "Файл не выбран"}), 400

    if not allowed_file(file.filename, current_app.config):
        return jsonify({"msg": "Недопустимый тип файла"}), 400

    original_name = file.filename
    ext = os.path.splitext(original_name)[1] if '.' in original_name else ''
    safe_filename = str(uuid.uuid4()) + ext
    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "attachments", entity_model.__tablename__, str(entity_id))
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, safe_filename)

    file.save(save_path)
    file_size = os.path.getsize(save_path)

    mime_type = file.content_type or "application/octet-stream"

    kwargs = {entity_model.__tablename__ + "_id": entity_id}
    attachment = Attachment(
        **kwargs,
        file_name=original_name,
        file_path=save_path,
        mime_type=mime_type,
        size=file_size,
    )
    db.session.add(attachment)
    db.session.commit()

    return jsonify(attachment.to_dict()), 201


@attachments_bp.route("/news/<int:news_id>/attachments", methods=["GET"])
@jwt_required()
def list_news_attachments(news_id):
    News.query.get_or_404(news_id)
    attachments = Attachment.query.filter_by(news_id=news_id).order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([a.to_dict() for a in attachments])


@attachments_bp.route("/news/<int:news_id>/attachments", methods=["POST"])
@jwt_required()
def upload_news_attachment(news_id):
    return _upload_attachment(News, news_id)


@attachments_bp.route("/announcements/<int:announcement_id>/attachments", methods=["GET"])
@jwt_required()
def list_announcement_attachments(announcement_id):
    Announcement.query.get_or_404(announcement_id)
    attachments = Attachment.query.filter_by(announcement_id=announcement_id).order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([a.to_dict() for a in attachments])


@attachments_bp.route("/announcements/<int:announcement_id>/attachments", methods=["POST"])
@jwt_required()
def upload_announcement_attachment(announcement_id):
    return _upload_attachment(Announcement, announcement_id)


@attachments_bp.route("/documents/<int:document_id>/attachments", methods=["GET"])
@jwt_required()
def list_document_attachments(document_id):
    Document.query.get_or_404(document_id)
    attachments = Attachment.query.filter_by(document_id=document_id).order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([a.to_dict() for a in attachments])


@attachments_bp.route("/documents/<int:document_id>/attachments", methods=["POST"])
@jwt_required()
def upload_document_attachment(document_id):
    return _upload_attachment(Document, document_id)


@attachments_bp.route("/meetings/<int:meeting_id>/attachments", methods=["GET"])
@jwt_required()
def list_meeting_attachments(meeting_id):
    DepartmentMeeting.query.get_or_404(meeting_id)
    attachments = Attachment.query.filter_by(meeting_id=meeting_id).order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([a.to_dict() for a in attachments])


@attachments_bp.route("/meetings/<int:meeting_id>/attachments", methods=["POST"])
@jwt_required()
def upload_meeting_attachment(meeting_id):
    return _upload_attachment(DepartmentMeeting, meeting_id)
