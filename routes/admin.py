from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt
from models.role import Role

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def users_list():
    role_id = get_jwt()["role"]
    if role_id != 1:
        return render_template("index.html")
    role = Role.query.get(role_id)
    return render_template("admin/users.html", role=role)
