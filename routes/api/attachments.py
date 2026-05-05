import os
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models.attachment import Attachment
from models.task import Task

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg", "gif", "txt", "zip", "rar"}

attachments_bp = Blueprint("api_attachments", __name__, url_prefix="/api")


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

    if not _allowed_file(file.filename):
        return jsonify({"msg": "Недопустимый тип файла"}), 400

    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "attachments", str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)

    file.save(save_path)
    file_size = os.path.getsize(save_path)

    mime_type = file.content_type or "application/octet-stream"
    attachment = Attachment(
        task_id=task_id,
        file_name=filename,
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
