from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models.group import Group, UserGroup

groups_bp = Blueprint("api_groups", __name__, url_prefix="/api/groups")


@groups_bp.route("/", methods=["GET"])
@jwt_required()
def list_groups():
    """Получить все группы
    ---
    tags: [Groups]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Список групп
        schema:
          type: array
          items:
            $ref: '#/definitions/Group'
    """
    groups = Group.query.all()
    return jsonify([g.to_dict() for g in groups])


@groups_bp.route("/", methods=["POST"])
@jwt_required()
def create_group():
    """Создать группу (только Руководитель/Документовед)
    ---
    tags: [Groups]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name:
              type: string
    responses:
      201:
        description: Группа создана
        schema:
          $ref: '#/definitions/Group'
      400:
        description: Не указано название
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"msg": "Укажите название группы"}), 400

    group = Group(name=name)
    db.session.add(group)
    db.session.commit()

    return jsonify(group.to_dict()), 201


@groups_bp.route("/<int:id>", methods=["PATCH"])
@jwt_required()
def update_group(id):
    """Обновить группу (только Руководитель/Документовед)
    ---
    tags: [Groups]
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
            name:
              type: string
    responses:
      200:
        description: Группа обновлена
        schema:
          $ref: '#/definitions/Group'
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    group = Group.query.get_or_404(id)
    data = request.json
    if "name" in data:
        group.name = data["name"]
    db.session.commit()
    return jsonify(group.to_dict())


@groups_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_group(id):
    """Удалить группу (только Руководитель/Документовед)
    ---
    tags: [Groups]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Группа удалена
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    group = Group.query.get_or_404(id)
    db.session.delete(group)
    db.session.commit()
    return jsonify({"msg": "Группа удалена"})


@groups_bp.route("/<int:id>/users", methods=["GET"])
@jwt_required()
def get_group_users(id):
    """Получить пользователей группы
    ---
    tags: [Groups]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Список пользователей
        schema:
          type: array
          items:
            $ref: '#/definitions/User'
    """
    group = Group.query.get_or_404(id)
    users = [ug.user.to_dict() for ug in UserGroup.query.filter_by(group_id=id).all()]
    return jsonify(users)


@groups_bp.route("/<int:id>/users", methods=["POST"])
@jwt_required()
def add_user_to_group(id):
    """Добавить пользователя в группу (только Руководитель/Документовед)
    ---
    tags: [Groups]
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
          required: [user_id]
          properties:
            user_id:
              type: integer
    responses:
      201:
        description: Пользователь добавлен
      400:
        description: Не указан user_id
      409:
        description: Пользователь уже в группе
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    Group.query.get_or_404(id)
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"msg": "Укажите user_id"}), 400

    existing = UserGroup.query.filter_by(group_id=id, user_id=user_id).first()
    if existing:
        return jsonify({"msg": "Пользователь уже в группе"}), 409

    user_group = UserGroup(group_id=id, user_id=user_id)
    db.session.add(user_group)
    db.session.commit()
    return jsonify({"msg": "Пользователь добавлен"}), 201


@groups_bp.route("/<int:id>/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_user_from_group(id, user_id):
    """Удалить пользователя из группы (только Руководитель/Документовед)
    ---
    tags: [Groups]
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Пользователь удалён
      404:
        description: Пользователь не найден в группе
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    user_group = UserGroup.query.filter_by(group_id=id, user_id=user_id).first()
    if not user_group:
        return jsonify({"msg": "Пользователь не найден в группе"}), 404

    db.session.delete(user_group)
    db.session.commit()
    return jsonify({"msg": "Пользователь удалён из группы"})
