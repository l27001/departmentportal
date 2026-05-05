from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from models.user import User

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
