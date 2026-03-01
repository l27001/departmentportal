from flask_jwt_extended import get_jwt
from functools import wraps
from flask import jsonify
from models.role import Role

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            role = Role.query.filter_by(id=claims['role']).first()
            if role is None or role.name not in roles:
                return jsonify({"msg": "Access denied"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper