from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.role import Role

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/', methods=['GET'])
@jwt_required()
def chat_page():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    return render_template('chat/chat.html', role=role)
