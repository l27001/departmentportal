from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from werkzeug.exceptions import Unauthorized

def jwt_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                # Проверяем, что JWT-токен присутствует в запросе
                verify_jwt_in_request()
            except Exception as e:
                raise Unauthorized("Token is missing or invalid.") from e
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                # Проверяем наличие токена и извлекаем роли пользователя
                verify_jwt_in_request()
                user_role = get_jwt_identity().get('role')
                if user_role not in roles:
                    return jsonify({"msg": "Access denied"}), 403
            except Exception as e:
                raise Unauthorized("Token is missing or invalid.") from e
            return fn(*args, **kwargs)
        return decorator
    return wrapper
