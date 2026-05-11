import os
import uuid
from flask import Blueprint, request, render_template, flash, redirect, url_for, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import date
from extensions import db, allowed_file
from models.meeting import DepartmentMeeting
from models.task import Task, TaskUserAssignment
from models.attachment import Attachment
from models.role import Role
from models.user import User
from models.group import Group, UserGroup
from utils.notifications import notify_meeting_created

meetings_bp = Blueprint("web_meetings", __name__, url_prefix="/meetings")


def _get_groups_data():
    groups = Group.query.all()
    groups_members = {}
    for group in groups:
        members = (
            User.query.join(UserGroup, UserGroup.user_id == User.id)
            .filter(UserGroup.group_id == group.id, User.is_active == True, User.dismissal_date.is_(None))
            .all()
        )
        groups_members[str(group.id)] = [{"id": m.id, "name": m.name} for m in members]
    return groups, groups_members


@meetings_bp.route("/", methods=["GET"])
@jwt_required()
def list_meetings():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = DepartmentMeeting.query.order_by(DepartmentMeeting.date.desc()).paginate(page=page, per_page=per_page, error_out=False)

    if role.name == 'Сотрудник':
        user_task_ids = set(
            a.task_id for a in TaskUserAssignment.query.filter_by(user_id=user_id).all()
        )
        meeting_task_counts = {}
        for meeting in pagination.items:
            meeting_task_counts[meeting.id] = len([t for t in meeting.tasks if t.id in user_task_ids])
    else:
        meeting_task_counts = {m.id: len(m.tasks) for m in pagination.items}

    return render_template("meetings/list.html", meetings=pagination.items, page=page, total=pagination.total, per_page=per_page, total_pages=pagination.pages, role=role, meeting_task_counts=meeting_task_counts)


def _process_new_tasks(meeting, meeting_date):
    new_task_titles = request.form.getlist("new_task_title")
    new_task_descs = request.form.getlist("new_task_desc")
    new_task_deadlines = request.form.getlist("new_task_deadline")
    new_task_priorities = request.form.getlist("new_task_priority")
    new_task_executors = request.form.getlist("new_task_executors")
    new_task_no_reviews = request.form.getlist("new_task_no_review")

    for i in range(len(new_task_titles)):
        nt_title = new_task_titles[i].strip() if i < len(new_task_titles) else ""
        if not nt_title:
            continue

        nt_deadline_str = new_task_deadlines[i] if i < len(new_task_deadlines) else meeting_date.isoformat()
        try:
            nt_deadline = date.fromisoformat(nt_deadline_str)
        except ValueError:
            nt_deadline = meeting_date

        nt_desc = new_task_descs[i] if i < len(new_task_descs) else ""
        nt_priority = new_task_priorities[i] if i < len(new_task_priorities) else "medium"
        nt_no_review = i < len(new_task_no_reviews)
        executor_str = new_task_executors[i] if i < len(new_task_executors) else ""

        if not executor_str:
            raise ValueError(f'Задача "{nt_title}" не имеет исполнителей')

        new_task = Task(
            title=nt_title,
            description=nt_desc,
            priority=nt_priority,
            deadline_at=nt_deadline,
            creator_id=get_jwt_identity(),
            no_review=nt_no_review,
        )
        db.session.add(new_task)
        db.session.flush()

        meeting.tasks.append(new_task)

        for uid in executor_str.split(","):
            uid = uid.strip()
            if uid:
                assignment = TaskUserAssignment(task_id=new_task.id, user_id=int(uid))
                db.session.add(assignment)


def _render_create(role):
    groups, groups_members = _get_groups_data()
    tasks = Task.query.order_by(Task.deadline_at.asc()).all()
    return render_template("meetings/create.html", role=role, tasks=tasks, groups=groups, groups_members=groups_members)


@meetings_bp.route("/create", methods=["GET", "POST"])
@jwt_required()
def create_meeting():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_meetings.list_meetings"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        date_str = request.form.get("date")
        task_ids = request.form.getlist("task_ids")
        files = request.files.getlist("files")

        if not title or not date_str:
            flash("Заполните обязательные поля", "danger")
            return _render_create(role)

        for f in files:
            if f.filename and not allowed_file(f.filename, current_app.config):
                flash(f"Недопустимый формат файла: {f.filename}", "danger")
                return _render_create(role)

        try:
            meeting_date = date.fromisoformat(date_str)
        except ValueError:
            flash("Неверный формат даты", "danger")
            return _render_create(role)

        meeting = DepartmentMeeting(title=title, description=description, date=meeting_date)
        db.session.add(meeting)
        db.session.flush()

        for tid in task_ids:
            task = Task.query.get(int(tid))
            if task:
                meeting.tasks.append(task)

        try:
            _process_new_tasks(meeting, meeting_date)
        except ValueError as e:
            flash(str(e), "danger")
            return _render_create(role)

        if files:
            upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments", "meetings", str(meeting.id))
            os.makedirs(upload_dir, exist_ok=True)

            for f in files:
                if f.filename:
                    original_name = f.filename
                    ext = os.path.splitext(original_name)[1].lower()
                    safe_name = str(uuid.uuid4()) + ext
                    save_path = os.path.join(upload_dir, safe_name)
                    f.save(save_path)
                    file_size = os.path.getsize(save_path)

                    attachment = Attachment(
                        meeting_id=meeting.id,
                        file_name=original_name,
                        file_path=save_path,
                        mime_type=f.content_type or "application/octet-stream",
                        size=file_size,
                    )
                    db.session.add(attachment)

        db.session.commit()
        notify_meeting_created(meeting, request.host_url)
        flash("Заседание успешно создано", "success")
        return redirect(url_for("web_meetings.list_meetings"))

    return _render_create(role)


@meetings_bp.route("/<int:meeting_id>", methods=["GET"])
@jwt_required()
def meeting_details(meeting_id):
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    meeting = DepartmentMeeting.query.get_or_404(meeting_id)

    if role.name == 'Сотрудник':
        user_task_ids = set(
            a.task_id for a in TaskUserAssignment.query.filter_by(user_id=user_id).all()
        )
        visible_tasks = [t for t in meeting.tasks if t.id in user_task_ids]
    else:
        visible_tasks = meeting.tasks

    return render_template("meetings/details.html", meeting=meeting, role=role, visible_tasks=visible_tasks)


def _render_edit(meeting, role):
    groups, groups_members = _get_groups_data()
    tasks = Task.query.order_by(Task.deadline_at.asc()).all()
    return render_template("meetings/edit.html", meeting=meeting, role=role, tasks=tasks, groups=groups, groups_members=groups_members)


@meetings_bp.route("/<int:meeting_id>/edit", methods=["GET", "POST"])
@jwt_required()
def edit_meeting(meeting_id):
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_meetings.list_meetings"))

    meeting = DepartmentMeeting.query.get_or_404(meeting_id)

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        date_str = request.form.get("date")
        task_ids = request.form.getlist("task_ids")
        delete_attachments = request.form.getlist("delete_attachments")
        new_files = request.files.getlist("files")

        if not title or not date_str:
            flash("Заполните обязательные поля", "danger")
            return _render_edit(meeting, role)

        for att_id in delete_attachments:
            att = Attachment.query.get(int(att_id))
            if att and att.meeting_id == meeting.id:
                if os.path.exists(att.file_path):
                    os.remove(att.file_path)
                db.session.delete(att)

        try:
            meeting.date = date.fromisoformat(date_str)
        except ValueError:
            flash("Неверный формат даты", "danger")
            return _render_edit(meeting, role)

        meeting.title = title
        meeting.description = description

        meeting.tasks = []
        for tid in task_ids:
            task = Task.query.get(int(tid))
            if task:
                meeting.tasks.append(task)

        try:
            _process_new_tasks(meeting, meeting.date)
        except ValueError as e:
            flash(str(e), "danger")
            return _render_edit(meeting, role)

        if new_files:
            upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments", "meetings", str(meeting.id))
            os.makedirs(upload_dir, exist_ok=True)

            for f in new_files:
                if f.filename and allowed_file(f.filename, current_app.config):
                    original_name = f.filename
                    ext = os.path.splitext(original_name)[1].lower()
                    safe_name = str(uuid.uuid4()) + ext
                    save_path = os.path.join(upload_dir, safe_name)
                    f.save(save_path)
                    file_size = os.path.getsize(save_path)
                    attachment = Attachment(
                        meeting_id=meeting.id,
                        file_name=original_name,
                        file_path=save_path,
                        mime_type=f.content_type or "application/octet-stream",
                        size=file_size,
                    )
                    db.session.add(attachment)

        db.session.commit()
        flash("Заседание успешно обновлено", "success")
        return redirect(url_for("web_meetings.meeting_details", meeting_id=meeting.id))

    return _render_edit(meeting, role)


@meetings_bp.route("/file/<int:attachment_id>")
@jwt_required()
def serve_meeting_file(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    if not attachment.meeting_id:
        return "Not found", 404
    directory = os.path.dirname(attachment.file_path)
    filename = os.path.basename(attachment.file_path)
    return send_from_directory(directory, filename, mimetype=attachment.mime_type, as_attachment=True)


@meetings_bp.route("/<int:meeting_id>/delete", methods=["POST"])
@jwt_required()
def delete_meeting(meeting_id):
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_meetings.list_meetings"))

    meeting = DepartmentMeeting.query.get_or_404(meeting_id)
    db.session.delete(meeting)
    db.session.commit()
    flash("Заседание удалено", "success")
    return redirect(url_for("web_meetings.list_meetings"))
