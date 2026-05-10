import os
import uuid
from flask import Blueprint, request, render_template, flash, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import date
from extensions import db, allowed_file
from models.announcement import Announcement, AnnouncementView
from models.attachment import Attachment
from models.role import Role

announcements_bp = Blueprint('announcements', __name__, url_prefix='/announcements')


@announcements_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_announcement():
    role_id = get_jwt()["role"]
    role = Role.query.get(role_id)
    if role.name not in ('Руководитель', 'Документовед'):
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('tasks.list_tasks'))

    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        deadline_str = request.form.get('deadline')
        require_rsvp = request.form.get('require_rsvp') == 'on'
        files = request.files.getlist('file')

        if not title or not text or not deadline_str:
            flash('Заполните все поля', 'danger')
            return render_template('announcements/create.html', role=role)

        try:
            deadline = date.fromisoformat(deadline_str)
        except ValueError:
            flash('Неверный формат даты', 'danger')
            return render_template('announcements/create.html', role=role)

        files = [f for f in files if f.filename]
        for f in files:
            if not allowed_file(f.filename, current_app.config):
                flash(f'Недопустимый формат файла: {f.filename}', 'danger')
                return render_template('announcements/create.html', role=role)

        user_id = get_jwt_identity()
        announcement = Announcement(title=title, text=text, deadline=deadline, creator_id=user_id, require_rsvp=require_rsvp)
        db.session.add(announcement)
        db.session.flush()

        if files:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'attachments', 'announcements', str(announcement.id))
            os.makedirs(upload_dir, exist_ok=True)

            for file in files:
                original_name = file.filename
                ext = os.path.splitext(original_name)[1] if '.' in original_name else ''
                safe_name = str(uuid.uuid4()) + ext
                save_path = os.path.join(upload_dir, safe_name)
                file.save(save_path)
                file_size = os.path.getsize(save_path)

                attachment = Attachment(
                    announcement_id=announcement.id,
                    file_name=original_name,
                    file_path=save_path,
                    mime_type=file.content_type or 'application/octet-stream',
                    size=file_size,
                )
                db.session.add(attachment)

        db.session.commit()
        flash('Анонс успешно создан', 'success')
        return redirect(url_for('tasks.list_tasks'))

    return render_template('announcements/create.html', role=role)


@announcements_bp.route('/all', methods=['GET'])
@jwt_required()
def all_announcements():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    role_id = get_jwt()["role"]
    pagination = Announcement.query.filter_by(is_deleted=False).order_by(Announcement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    user_id = get_jwt_identity()
    viewed_ids = {v.announcement_id for v in AnnouncementView.query.filter_by(user_id=user_id).all()}
    return render_template('announcements/all.html', announcements=pagination.items, page=page, total=pagination.total, per_page=per_page, total_pages=pagination.pages, viewed_ids=viewed_ids, role_id=role_id)
