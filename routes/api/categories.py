from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models.category import Category

categories_bp = Blueprint("api_categories", __name__, url_prefix="/api/categories")


def admin_required():
    role = get_jwt()["role"]
    if role not in (1, 2):
        return False
    return True


@categories_bp.route("/", methods=["GET"])
@jwt_required()
def list_categories():
    categories = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in categories])


@categories_bp.route("/", methods=["POST"])
@jwt_required()
def create_category():
    if not admin_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    data = request.json
    name = data.get("name", "").strip().lower()
    if not name:
        return jsonify({"msg": "Название категории обязательно"}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({"msg": "Категория с таким названием уже существует"}), 400

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({"id": category.id, "name": category.name}), 201


@categories_bp.route("/<int:category_id>", methods=["PATCH"])
@jwt_required()
def update_category(category_id):
    if not admin_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    category = Category.query.get_or_404(category_id)
    data = request.json
    name = data.get("name", "").strip().lower()

    if not name:
        return jsonify({"msg": "Название категории обязательно"}), 400

    if name != category.name and Category.query.filter_by(name=name).first():
        return jsonify({"msg": "Категория с таким названием уже существует"}), 400

    category.name = name
    db.session.commit()

    return jsonify({"id": category.id, "name": category.name})


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id):
    if not admin_required():
        return jsonify({"msg": "Доступ запрещён"}), 403

    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()

    return jsonify({"msg": "Категория удалена"})
