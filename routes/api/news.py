from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.news import News

news_bp = Blueprint("api_news", __name__, url_prefix="/api/news")


@news_bp.route("/", methods=["GET"])
@jwt_required()
def list_news():
    """Получить все новости
    ---
    tags: [News]
    security:
      - BearerAuth: []
    parameters:
      - name: pinned
        in: query
        type: integer
        enum: [0, 1]
        description: Фильтр закреплённых новостей (1 = только закреплённые)
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
        description: Список новостей
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/News'
            page:
              type: integer
            per_page:
              type: integer
            total:
              type: integer
            pages:
              type: integer
    """
    pinned = request.args.get("pinned")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    base_query = News.query.filter_by(is_deleted=False)
    if pinned == "1":
        base_query = base_query.filter_by(is_pinned=True)
    base_query = base_query.order_by(News.is_pinned.desc(), News.created_at.desc())

    total = base_query.count()
    news = base_query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "items": [n.to_dict() for n in news],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


@news_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_news(id):
    """Получить новость по ID
    ---
    tags: [News]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Новость
        schema:
          $ref: '#/definitions/News'
      404:
        description: Не найдено
    """
    news = News.query.filter_by(id=id, is_deleted=False).first_or_404()
    return jsonify(news.to_dict())


@news_bp.route("/", methods=["POST"])
@jwt_required()
def create_news():
    """Создать новость
    ---
    tags: [News]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/NewsInput'
    responses:
      201:
        description: Новость создана
        schema:
          $ref: '#/definitions/News'
      400:
        description: Ошибка валидации
    """
    user_id = get_jwt_identity()

    data = request.json
    title = data.get("title")
    text = data.get("text")
    is_pinned = data.get("is_pinned", False)

    if not title or not text:
        return jsonify({"msg": "Заполните заголовок и текст"}), 400

    news = News(title=title, text=text, is_pinned=is_pinned)
    db.session.add(news)
    db.session.commit()

    return jsonify(news.to_dict()), 201


@news_bp.route("/<int:id>", methods=["PATCH"])
@jwt_required()
def update_news(id):
    """Обновить новость (только Руководитель/Документовед)
    ---
    tags: [News]
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
            is_pinned:
              type: boolean
    responses:
      200:
        description: Новость обновлена
        schema:
          $ref: '#/definitions/News'
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    news = News.query.filter_by(id=id, is_deleted=False).first_or_404()
    data = request.json

    if "title" in data:
        news.title = data["title"]
    if "text" in data:
        news.text = data["text"]
    if "is_pinned" in data:
        news.is_pinned = data["is_pinned"]

    db.session.commit()
    return jsonify(news.to_dict())


@news_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_news(id):
    """Удалить новость (soft delete)
    ---
    tags: [News]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Новость удалена
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    news = News.query.filter_by(id=id, is_deleted=False).first_or_404()
    news.is_deleted = True
    db.session.commit()
    return jsonify({"msg": "Новость удалена"})
