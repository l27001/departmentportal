from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.chat import GeneralChatMessage

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
    """Отправить сообщение в чат
    ---
    tags: [Chat]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [text]
          properties:
            text:
              type: string
    responses:
      201:
        description: Сообщение отправлено
        schema:
          $ref: '#/definitions/ChatMessage'
      400:
        description: Пустое сообщение
    """
    user_id = get_jwt_identity()
    data = request.json
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"msg": "Сообщение не может быть пустым"}), 400

    message = GeneralChatMessage(author_id=user_id, text=text)
    db.session.add(message)
    db.session.commit()

    return jsonify(message.to_dict()), 201


@chat_bp.route("/messages/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_message(id):
    """Удалить своё сообщение из чата
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

    db.session.delete(message)
    db.session.commit()
    return jsonify({"msg": "Сообщение удалено"})
