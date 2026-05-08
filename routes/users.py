from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.user import User
from models.role import Role
from extensions import db
from decorators.roles import roles_required
from datetime import datetime

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
    role = Role.query.filter_by(id=get_jwt()["role"]).first()

    data = request.form
    user.name = data.get('name', user.name)
    user.job_title = data.get('job_title', user.job_title)
    user.phone = data.get('phone', user.phone)
    user.degree = data.get('degree', user.degree)
    user.academic_title = data.get('academic_title', user.academic_title)

    if role.name == 'Руководитель':
        hire_date_str = data.get('hire_date', '').strip()
        dismissal_date_str = data.get('dismissal_date', '').strip()
        if hire_date_str:
            try:
                user.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if dismissal_date_str:
            try:
                user.dismissal_date = datetime.strptime(dismissal_date_str, '%Y-%m-%d').date()
            except ValueError:
                user.dismissal_date = None
        else:
            user.dismissal_date = None

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
        'job_title': user.job_title,
        'hire_date': user.hire_date.isoformat() if user.hire_date else None,
        'dismissal_date': user.dismissal_date.isoformat() if user.dismissal_date else None,
    } for user in users]

    return jsonify(users_list)


@users_bp.route('/<int:user_id>/employment', methods=['POST'])
@jwt_required()
@roles_required('Руководитель')
def update_user_employment(user_id):
    user = User.query.get_or_404(user_id)
    data = request.form

    hire_date_str = data.get('hire_date', '').strip()
    dismissal_date_str = data.get('dismissal_date', '').strip()

    if hire_date_str:
        try:
            user.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if dismissal_date_str:
        try:
            user.dismissal_date = datetime.strptime(dismissal_date_str, '%Y-%m-%d').date()
        except ValueError:
            user.dismissal_date = None
    else:
        user.dismissal_date = None

    db.session.commit()
    return jsonify({"msg": "Данные обновлены", "user_id": user.id})
