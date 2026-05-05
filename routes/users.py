from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from extensions import db
from decorators.roles import roles_required

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return render_template('user/profile.html', user=user)

@users_bp.route('/profile', methods=['POST'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    data = request.form
    user.name = data.get('name', user.name)
    user.job_title = data.get('job_title', user.job_title)
    user.phone = data.get('phone', user.phone)
    user.degree = data.get('degree', user.degree)
    user.academic_title = data.get('academic_title', user.academic_title)

    db.session.commit()
    flash("Данные успешно сохранены", "success")

    return redirect(url_for('users.get_profile'))

@users_bp.route('/', methods=['GET'])
@jwt_required()  # Требует авторизации через JWT
@roles_required('Руководитель')  # Требует роль "Руководитель"
def get_users():
    users = User.query.all()  # Получаем всех пользователей из базы данных

    users_list = [{
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'name': user.name,
        'job_title': user.job_title
    } for user in users]

    return jsonify(users_list)
