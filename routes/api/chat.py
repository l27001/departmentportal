import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, allowed_file
from models.chat import GeneralChatMessage
from models.attachment import Attachment

chat_bp = Blueprint("api_chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/messages", methods=["GET"])
@jwt_required()
def get_messages():
    """Получить сообщения чата с пагинацией
    ---
    tags: [Chat]
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: Сообщения с пагинацией
        schema:
          type: object
          properties:
            messages:
              type: array
              items:
                $ref: '#/definitions/ChatMessage'
            page:
              type: integer
            pages:
              type: integer
            has_next:
              type: boolean
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    pagination = GeneralChatMessage.query.order_by(
        GeneralChatMessage.created_at.asc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "messages": [m.to_dict() for m in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    })


@chat_bp.route("/messages", methods=["POST"])
@jwt_required()
def send_message():
    """Отправить сообщение в чат (поддерживает text/plain, multipart/form-data с файлами)
    ---
    tags: [Chat]
    security:
      - BearerAuth: []
    consumes:
      - application/json
      - multipart/form-data
    parameters:
      - name: text
        in: formData
        type: string
        required: false
        description: Текст сообщения (можно пустое, если есть файл)
      - name: file
        in: formData
        type: file
        required: false
        description: Файл для прикрепления (можно несколько)
    responses:
      201:
        description: Сообщение отправлено
        schema:
          $ref: '#/definitions/ChatMessage'
      400:
        description: Пустое сообщение без файла
    """
    user_id = get_jwt_identity()

    text = ""
    files = []

    if request.content_type and "multipart/form-data" in request.content_type:
        text = request.form.get("text", "").strip()
        uploaded_files = request.files.getlist("file")
        for f in uploaded_files:
            if f and f.filename:
                files.append(f)
    else:
        data = request.json or {}
        text = data.get("text", "").strip()

    if not text and not files:
        return jsonify({"msg": "Сообщение не может быть пустым"}), 400

    message = GeneralChatMessage(author_id=user_id, text=text or "")
    db.session.add(message)
    db.session.flush()

    for f in files:
        if not allowed_file(f.filename, current_app.config):
            continue
        original_name = f.filename
        ext = os.path.splitext(original_name)[1] if '.' in original_name else ''
        safe_filename = str(uuid.uuid4()) + ext
        upload_dir = os.path.join(
            current_app.config.get("UPLOAD_FOLDER", "uploads"),
            "attachments", "chat", str(message.id)
        )
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, safe_filename)
        f.save(save_path)
        file_size = os.path.getsize(save_path)
        mime_type = f.content_type or "application/octet-stream"
        attachment = Attachment(
            chat_message_id=message.id,
            file_name=original_name,
            file_path=save_path,
            mime_type=mime_type,
            size=file_size,
        )
        db.session.add(attachment)

    db.session.commit()
    return jsonify(message.to_dict()), 201


@chat_bp.route("/messages/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_message(id):
    """Удалить своё сообщение из чата (с файлами)
    ---
    tags: [Chat]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Сообщение удалено
      403:
        description: Можно удалять только свои сообщения
    """
    user_id = get_jwt_identity()
    message = GeneralChatMessage.query.get_or_404(id)
    if message.author_id != user_id:
        return jsonify({"msg": "Можно удалять только свои сообщения"}), 403

    for att in message.attachments.all():
        if os.path.exists(att.file_path):
            os.remove(att.file_path)
        db.session.delete(att)

    db.session.delete(message)
    db.session.commit()
    return jsonify({"msg": "Сообщение удалено"})
