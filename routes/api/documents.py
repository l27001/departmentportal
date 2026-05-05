import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, allowed_file
from models.document import Document
from models.attachment import Attachment

api_documents_bp = Blueprint("api_documents", __name__, url_prefix="/api/documents")


@api_documents_bp.route("/", methods=["GET"])
@jwt_required()
def list_documents():
    """Получить список документов
    ---
    tags: [Documents]
    security:
      - BearerAuth: []
    parameters:
      - name: category
        in: query
        type: string
        description: Фильтр по категории
    responses:
      200:
        description: Список документов
        schema:
          type: array
          items:
            $ref: '#/definitions/Document'
    """
    category = request.args.get("category")
    query = Document.query
    if category:
        query = query.filter_by(category=category)
    docs = query.order_by(Document.created_at.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@api_documents_bp.route("/", methods=["POST"])
@jwt_required()
def upload_document():
    """Загрузить документ
    ---
    tags: [Documents]
    security:
      - BearerAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
      - name: title
        in: formData
        type: string
        required: true
      - name: category
        in: formData
        type: string
    responses:
      201:
        description: Документ загружен
        schema:
          $ref: '#/definitions/Document'
      400:
        description: Ошибка загрузки
    """
    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"msg": "Файл не найден"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "Файл не выбран"}), 400

    if not allowed_file(file.filename, current_app.config):
        return jsonify({"msg": "Недопустимый тип файла"}), 400

    title = request.form.get("title", file.filename)
    category = request.form.get("category")

    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
    safe_name = str(uuid.uuid4()) + ext
    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "attachments")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, safe_name)

    file.save(save_path)
    file_size = os.path.getsize(save_path)

    attachment = Attachment(
        task_id=None,
        file_name=original_filename,
        file_path=save_path,
        mime_type=file.content_type or "application/octet-stream",
        size=file_size,
    )
    db.session.add(attachment)
    db.session.flush()

    doc = Document(
        title=title,
        attachment_id=attachment.id,
        creator_id=user_id,
        category=category,
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify(doc.to_dict()), 201


@api_documents_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def download_document(id):
    """Скачать документ
    ---
    tags: [Documents]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Файл документа
        schema:
          type: file
      404:
        description: Не найдено
    """
    doc = Document.query.get_or_404(id)
    attachment = doc.attachment
    if not attachment or not os.path.exists(attachment.file_path):
        return jsonify({"msg": "Файл не найден на сервере"}), 404

    return send_file(attachment.file_path, as_attachment=True, download_name=attachment.file_name)


@api_documents_bp.route("/<int:id>", methods=["PATCH"])
@jwt_required()
def update_document(id):
    """Обновить документ (только автор или Руководитель/Документовед)
    ---
    tags: [Documents]
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
            category:
              type: string
    responses:
      200:
        description: Документ обновлён
        schema:
          $ref: '#/definitions/Document'
      403:
        description: Доступ запрещён
    """
    user_id = get_jwt_identity()
    role = get_jwt()["role"]
    doc = Document.query.get_or_404(id)

    if doc.creator_id != user_id and role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    data = request.json
    if "title" in data:
        doc.title = data["title"]
    if "category" in data:
        doc.category = data["category"]

    db.session.commit()
    return jsonify(doc.to_dict())


@api_documents_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_document(id):
    """Удалить документ (только автор или Руководитель/Документовед)
    ---
    tags: [Documents]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Документ удалён
      403:
        description: Доступ запрещён
    """
    user_id = get_jwt_identity()
    role = get_jwt()["role"]
    doc = Document.query.get_or_404(id)

    if doc.creator_id != user_id and role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    attachment = doc.attachment
    if attachment and os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
        db.session.delete(attachment)

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"msg": "Документ удалён"})
