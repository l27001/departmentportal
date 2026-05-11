from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.user import User
from models.role import Role
from datetime import datetime

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")


def leader_required():
    role = get_jwt()["role"]
    if role != 1:
        return False
    return True


@admin_users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    """Получить список пользователей (только Руководитель)
    ---
    tags: [Admin]
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
      - name: search
        in: query
        type: string
        description: Поиск по имени или email
    responses:
      200:
        description: Список пользователей
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                $ref: '#/definitions/UserDetail'
            page:
              type: integer
            per_page:
              type: integer
            total:
              type: integer
      403:
        description: Доступ запрещён
    """
    if not leader_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    search = request.args.get("search", "").strip()

    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(User.name.ilike(like), User.email.ilike(like))
        )
    query = query.order_by(User.name.asc())

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "users": [u.to_dict() for u in users],
        "page": page,
        "per_page": per_page,
        "total": total,
    })


@admin_users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    """Получить пользователя по ID (только Руководитель)
    ---
    tags: [Admin]
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Данные пользователя
        schema:
          $ref: '#/definitions/UserDetail'
      403:
        description: Доступ запрещён
      404:
        description: Не найдено
    """
    if not leader_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    user = User.query.get_or_404(user_id)
    d = user.to_dict()
    d["role_id"] = user.role_id
    return jsonify(d)


@admin_users_bp.route("/", methods=["POST"])
@jwt_required()
def create_user():
    """Создать пользователя (только Руководитель)
    ---
    tags: [Admin]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [email, password, name, role_id]
          properties:
            email:
              type: string
            password:
              type: string
            name:
              type: string
            role_id:
              type: integer
            job_title:
              type: string
            phone:
              type: string
            academic_title:
              type: string
            degree:
              type: string
            rate_type:
              type: string
            rate_count:
              type: number
            hire_date:
              type: string
              format: date
    responses:
      201:
        description: Пользователь создан
        schema:
          $ref: '#/definitions/UserDetail'
      400:
        description: Ошибка валидации
      403:
        description: Доступ запрещён
    """
    if not leader_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()
    role_id = data.get("role_id")

    errors = []
    if not email:
        errors.append("Email обязателен")
    if User.query.filter_by(email=email).first():
        errors.append("Пользователь с таким email уже существует")
    if not password or len(password) < 6:
        errors.append("Пароль должен быть не менее 6 символов")
    if not name:
        errors.append("Имя обязательно")
    if not role_id or not Role.query.get(role_id):
        errors.append("Укажите корректную роль")

    if errors:
        return jsonify({"msg": " | ".join(errors)}), 400

    user = User(
        email=email,
        name=name,
        role_id=role_id,
        job_title=data.get("job_title"),
        phone=data.get("phone"),
        academic_title=data.get("academic_title"),
        degree=data.get("degree"),
        rate_type=data.get("rate_type", "основная"),
        rate_count=data.get("rate_count", 1.0),
    )
    user.set_password(password)

    hire_date_str = data.get("hire_date")
    if hire_date_str:
        try:
            user.hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    db.session.add(user)
    db.session.commit()

    d = user.to_dict()
    d["role_id"] = user.role_id
    return jsonify(d), 201


@admin_users_bp.route("/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    """Обновить пользователя (только Руководитель)
    ---
    tags: [Admin]
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
            name:
              type: string
            role_id:
              type: integer
            job_title:
              type: string
            phone:
              type: string
            academic_title:
              type: string
            degree:
              type: string
            rate_type:
              type: string
            rate_count:
              type: number
            hire_date:
              type: string
              format: date
            dismissal_date:
              type: string
              format: date
            is_active:
              type: boolean
    responses:
      200:
        description: Пользователь обновлён
        schema:
          $ref: '#/definitions/UserDetail'
      400:
        description: Ошибка валидации
      403:
        description: Доступ запрещён
      404:
        description: Не найдено
    """
    if not leader_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    user = User.query.get_or_404(user_id)
    data = request.json

    if "email" in data:
        email = data["email"].strip().lower()
        if email != user.email and User.query.filter_by(email=email).first():
            return jsonify({"msg": "Пользователь с таким email уже существует"}), 400
        user.email = email
    if "name" in data:
        user.name = data["name"].strip()
    if "role_id" in data:
        if not Role.query.get(data["role_id"]):
            return jsonify({"msg": "Укажите корректную роль"}), 400
        user.role_id = data["role_id"]
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"msg": "Пароль должен быть не менее 6 символов"}), 400
        user.set_password(data["password"])
    if "job_title" in data:
        user.job_title = data["job_title"]
    if "phone" in data:
        user.phone = data["phone"]
    if "academic_title" in data:
        user.academic_title = data["academic_title"]
    if "degree" in data:
        user.degree = data["degree"]
    if "rate_type" in data:
        user.rate_type = data["rate_type"]
    if "rate_count" in data:
        user.rate_count = data["rate_count"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "hire_date" in data:
        try:
            user.hire_date = datetime.strptime(data["hire_date"], "%Y-%m-%d").date() if data["hire_date"] else None
        except ValueError:
            pass
    if "dismissal_date" in data:
        try:
            user.dismissal_date = datetime.strptime(data["dismissal_date"], "%Y-%m-%d").date() if data["dismissal_date"] else None
        except ValueError:
            pass

    db.session.commit()

    d = user.to_dict()
    d["role_id"] = user.role_id
    return jsonify(d)
