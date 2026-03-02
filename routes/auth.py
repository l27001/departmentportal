from flask import Blueprint, request, jsonify, render_template, url_for, redirect, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import check_password_hash
from models.user import User
from decorators.auth import jwt_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if(request.method == 'POST'):
        data = request.form

        # Получаем пользователя по email
        user = User.query.filter_by(email=data['email']).first()

        # Проверяем, существует ли пользователь и правильность пароля
        if not user or not check_password_hash(user.password, data['password']):
            flash("Неверный логин или пароль", "danger")
            return render_template("auth/login.html")

        # Создаем JWT токен
        token = create_access_token(identity=user.id, additional_claims={"role": user.role.id})
        redir = redirect(url_for("index"))
        set_access_cookies(redir, token)
        flash("Вы успешно вошли", "success")
        return redir
    return render_template("auth/login.html")

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    return jsonify({
        "email": user.email,
        "role": user.role,
        "id": user.id
    }), 200

@auth_bp.route('/logout', methods=['GET'])
@jwt_required()
def logout():
    resp = redirect(url_for('auth.login'))
    unset_jwt_cookies(resp)
    flash("Вы успешно вышли", "success")
    return resp, 302
