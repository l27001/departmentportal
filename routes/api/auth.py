from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash, generate_password_hash
from models.user import User
from models.role import Role
from extensions import db
from datetime import datetime

api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@api_auth_bp.route("/login", methods=["POST"])
def login():
    """Вход в систему
    ---
    tags: [Auth]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/LoginInput'
    responses:
      200:
        description: Успешный вход
        schema:
          $ref: '#/definitions/LoginResponse'
      400:
        description: Не указаны email или пароль
      401:
        description: Неверный email или пароль
      403:
        description: Аккаунт заблокирован
    """
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Укажите email и пароль"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Неверный email или пароль"}), 401

    if not user.is_active:
        return jsonify({"msg": "Аккаунт заблокирован"}), 403

    access_token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role.id}
    )

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


@api_auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Получить профиль текущего пользователя
    ---
    tags: [Auth]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Профиль пользователя
        schema:
          $ref: '#/definitions/User'
      401:
        description: Не авторизован
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@api_auth_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_profile():
    """Редактировать профиль
    ---
    tags: [Auth]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            job_title:
              type: string
            phone:
              type: string
            degree:
              type: string
            academic_title:
              type: string
            hire_date:
              type: string
              format: date
            dismissal_date:
              type: string
              format: date
    responses:
      200:
        description: Профиль обновлён
        schema:
          $ref: '#/definitions/User'
      401:
        description: Не авторизован
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    role = Role.query.filter_by(id=get_jwt()["role"]).first()

    data = request.json
    if not data:
        return jsonify({"msg": "Нет данных для обновления"}), 400

    user.name = data.get("name", user.name)
    user.job_title = data.get("job_title", user.job_title)
    user.phone = data.get("phone", user.phone)
    user.degree = data.get("degree", user.degree)
    user.academic_title = data.get("academic_title", user.academic_title)

    if role.name == "Руководитель":
        hire_date_str = data.get("hire_date")
        dismissal_date_str = data.get("dismissal_date")
        if hire_date_str:
            try:
                user.hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"msg": "Неверный формат hire_date, ожидается YYYY-MM-DD"}), 400
        if dismissal_date_str:
            try:
                user.dismissal_date = datetime.strptime(dismissal_date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"msg": "Неверный формат dismissal_date, ожидается YYYY-MM-DD"}), 400
        else:
            user.dismissal_date = None

    db.session.commit()
    return jsonify(user.to_dict()), 200


@api_auth_bp.route("/refresh", methods=["GET"])
@jwt_required()
def refresh():
    """Обновить токен доступа
    ---
    tags: [Auth]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Токен обновлён
        schema:
          type: object
          properties:
            access_token:
              type: string
      401:
        description: Не авторизован
    """
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    access_token = create_access_token(
        identity=current_user,
        additional_claims={"role": user.role.id}
    )
    return jsonify({"access_token": access_token}), 200


@api_auth_bp.route("/changepass", methods=["PATCH"])
@jwt_required()
def change_password():
    """Сменить пароль
    ---
    tags: [Auth]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - old_password
            - new_password
          properties:
            old_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Пароль изменён
      400:
        description: Не указаны поля или новый пароль совпадает со старым
      401:
        description: Неверный текущий пароль
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"msg": "Укажите текущий и новый пароль"}), 400

    if old_password == new_password:
        return jsonify({"msg": "Новый пароль совпадает с текущим"}), 400

    if len(new_password) < 6:
        return jsonify({"msg": "Минимальная длина пароля — 6 символов"}), 400

    if not check_password_hash(user.password, old_password):
        return jsonify({"msg": "Неверный текущий пароль"}), 401

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"msg": "Пароль успешно изменён"}), 200
