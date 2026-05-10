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
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Список документов
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/Document'
            page:
              type: integer
            per_page:
              type: integer
            total:
              type: integer
            pages:
              type: integer
    """
    category = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    base_query = Document.query
    if category:
        base_query = base_query.filter_by(category=category)
    base_query = base_query.order_by(Document.created_at.desc())

    total = base_query.count()
    docs = base_query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "items": [d.to_dict() for d in docs],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


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

    files = request.files.getlist("file")
    files = [f for f in files if f.filename]
    if not files:
        return jsonify({"msg": "Файлы не выбраны"}), 400

    for file in files:
        if not allowed_file(file.filename, current_app.config):
            return jsonify({"msg": f"Недопустимый тип файла: {file.filename}"}), 400

    title = request.form.get("title") or files[0].filename
    category = request.form.get("category")

    doc = Document(
        title=title,
        creator_id=user_id,
        category=category,
    )
    db.session.add(doc)
    db.session.flush()

    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "attachments", "documents", str(doc.id))
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
        safe_name = str(uuid.uuid4()) + ext
        save_path = os.path.join(upload_dir, safe_name)

        file.save(save_path)
        file_size = os.path.getsize(save_path)

        attachment = Attachment(
            document_id=doc.id,
            file_name=original_filename,
            file_path=save_path,
            mime_type=file.content_type or "application/octet-stream",
            size=file_size,
        )
        db.session.add(attachment)

    db.session.commit()

    return jsonify(doc.to_dict()), 201


@api_documents_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_document(id):
    """Получить документ по ID
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
        description: Документ с вложениями
        schema:
          $ref: '#/definitions/Document'
      404:
        description: Не найдено
    """
    doc = Document.query.get_or_404(id)
    return jsonify(doc.to_dict())


@api_documents_bp.route("/<int:id>/download/<int:attachment_id>", methods=["GET"])
@jwt_required()
def download_attachment(id, attachment_id):
    """Скачать вложение документа
    ---
    tags: [Documents]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: attachment_id
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
    doc = Document.query.get_or_404(id)
    attachment = Attachment.query.filter_by(id=attachment_id, document_id=doc.id).first_or_404()
    if not os.path.exists(attachment.file_path):
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

    for attachment in doc.attachments:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"msg": "Документ удалён"})
