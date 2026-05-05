from flask import Blueprint, request, jsonify, render_template, flash, url_for, redirect, abort, current_app
from io import StringIO, BytesIO
import csv
import os
import uuid
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, date
from sqlalchemy import desc, exists, asc
from extensions import db, allowed_file
from models.task import Task, TaskUserAssignment
from models.user import User
from models.role import Role
from models.group import Group, UserGroup
from models.attachment import Attachment
from decorators.roles import roles_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    users = []
    groups = []
    groups_members = {}
    tab = request.args.get("tab", "my")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    user_assignments = {
        a.task_id: a
        for a in TaskUserAssignment.query.filter_by(user_id=user_id).all()
    }

    task_ids_by_assignment = [r[0] for r in db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id).all()]
    my_task_ids = task_ids_by_assignment
    assigned_task_ids = set(my_task_ids)

    if role.name in ("Документовед", "Руководитель"):
        users = User.query.all()
        groups = Group.query.all()
        for group in groups:
            members = (
                db.session.query(User)
                .join(UserGroup, UserGroup.user_id == User.id)
                .filter(UserGroup.group_id == group.id)
                .all()
            )
            groups_members[group.id] = [{"id": m.id, "name": m.name} for m in members]

    if role.name in ("Документовед", "Руководитель") and tab == "all":
        tasks = Task.query.order_by(asc(Task.deadline_at)).all()
    else:
        tasks = (
            Task.query
            .filter(Task.id.in_(my_task_ids))
            .order_by(asc(Task.deadline_at))
            .all()
        )

    tasks = sorted(tasks, key=lambda t: 1 if (user_assignments.get(t.id) and user_assignments[t.id].status in ('завершена', 'на проверке')) else 0)

    total = len(tasks)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tasks = tasks[start:end]

    return render_template("tasks/list.html", tasks=paginated_tasks, role=role, users=users, groups=groups, groups_members=groups_members, user_assignments=user_assignments, assigned_task_ids=assigned_task_ids, user_id=user_id, today=date.today(), tab=tab, page=page, total=total, per_page=per_page)

@tasks_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Руководитель")
def create_task():
    if request.method == 'POST':
        user_id = get_jwt_identity()
        role = Role.query.filter_by(id=get_jwt()["role"]).first()
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        starts_at = request.form['starts_at']
        deadline_at = request.form['deadline_at']
        no_review = request.form.get('no_review') == 'on'
        try:
            assignees = request.form.getlist('assignees')
        except (ValueError):
            assignees = []

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            starts_at=starts_at,
            deadline_at=deadline_at,
            no_review=no_review,
            creator_id=user_id
        )

        db.session.add(new_task)
        db.session.commit()

        files = request.files.getlist('files')
        if files and files[0].filename:
            for file in files:
                if file.filename:
                    if not allowed_file(file.filename, current_app.config):
                        flash(f'Недопустимый формат файла: {file.filename}', 'danger')
                        return redirect(url_for('tasks.task_details', task_id=new_task.id))

                    original_name = file.filename
                    ext = os.path.splitext(original_name)[1].lower()
                    safe_filename = str(uuid.uuid4()) + ext
                    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'attachments')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, safe_filename)
                    file.save(file_path)
                    file.seek(0, 2)
                    file_size = file.tell()
                    attachment = Attachment(
                        task_id=new_task.id,
                        file_name=original_name,
                        file_path=file_path,
                        mime_type=file.content_type or 'application/octet-stream',
                        size=file_size
                    )
                    db.session.add(attachment)

        for assignee_id in assignees:
            task_assignment = TaskUserAssignment(task_id=new_task.id, user_id=assignee_id)
            db.session.add(task_assignment)

        db.session.commit()

        flash('Задача успешно создана!', 'success')
        tab = request.args.get('tab', 'my')
        return redirect(url_for('tasks.list_tasks', tab=tab))

@tasks_bp.route("/filter", methods=["GET"])
@jwt_required()
def filter_tasks():
    user_id = get_jwt_identity()
    role = get_jwt()["role"]

    priority = request.args.get("priority")
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = Task.query

    if role == 3:
        task_ids_by_assignment = [r[0] for r in db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id).all()]
        query = query.filter(Task.id.in_(task_ids_by_assignment))

    if priority:
        query = query.filter(Task.priority == priority)

    if date_from:
        query = query.filter(Task.deadline_at >= datetime.fromisoformat(date_from))

    if date_to:
        query = query.filter(Task.deadline_at <= datetime.fromisoformat(date_to))

    tasks = query.all()

    if status:
        tasks = [
            t for t in tasks
            if any(
                s.status == status and s.user_id == user_id
                for s in t.statuses
            )
        ]

    return jsonify([task.to_dict() for task in tasks])


@tasks_bp.route("/calendar", methods=["GET"])
@jwt_required()
def calendar():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    tasks = []
    tab = request.args.get("tab", "my")

    user_assignments = {
        a.task_id: a
        for a in TaskUserAssignment.query.filter_by(user_id=user_id).all()
    }

    task_ids_by_assignment = [r[0] for r in db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id).all()]

    if role.name in ("Документовед", "Руководитель") and tab == "all":
        tasks = Task.query.order_by(desc(Task.deadline_at)).all()
    else:
        tasks = (
            Task.query
            .filter(Task.id.in_(task_ids_by_assignment))
            .order_by(desc(Task.deadline_at))
            .all()
        )

    events = []
    today = date.today()
    for task in tasks:
        assignment = user_assignments.get(task.id)
        status = assignment.status if assignment else None
        is_overdue = status not in ('завершена', 'на проверке') and task.deadline_at < today
        color = None
        if is_overdue:
            color = 'darkred'
        elif task.priority == 'high':
            color = 'red'
        elif task.priority == 'medium':
            color = 'orange'
        else:
            color = 'light-blue'
        title = task.title
        if is_overdue:
            title = f'⚠ {task.title}'
        events.append({
            'title': title,
            'start': task.starts_at.strftime('%Y-%m-%d'),
            'end': task.deadline_at.strftime('%Y-%m-%d'),
            'description': task.description,
            'color': color,
            'url': url_for('tasks.task_details', task_id=task.id),
            'status': status
        })
    tasks_by_deadline = {}
    today = date.today()
    for task in tasks:
        deadline_str = task.deadline_at.strftime('%Y-%m-%d')
        if deadline_str not in tasks_by_deadline:
            tasks_by_deadline[deadline_str] = []
        assignment = user_assignments.get(task.id)
        status = assignment.status if assignment else None
        tasks_by_deadline[deadline_str].append({
            'id': task.id,
            'title': task.title,
            'status': status,
            'priority': task.priority,
            'is_overdue': status != 'завершена' and task.deadline_at < today
        })

    days_all_completed = {}
    days_has_unassigned = {}
    for day, day_tasks in tasks_by_deadline.items():
        days_all_completed[day] = all(t['status'] in ('завершена', 'на проверке') for t in day_tasks)
        days_has_unassigned[day] = any(t['status'] is None for t in day_tasks)

    return render_template("tasks/calendar.html", tasks=events, tasks_by_deadline=tasks_by_deadline, days_all_completed=days_all_completed, days_has_unassigned=days_has_unassigned, tab=tab, role=role)

@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
@roles_required("Руководитель")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    return jsonify({"msg": "Task deleted"})

@tasks_bp.route('/get/<int:task_id>', methods=['GET'])
@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def task_details(task_id):
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()

    if role.name == 'Сотрудник':
        has_assignment = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not has_assignment:
            return abort(404)
        task = Task.query.filter_by(id=task_id).first_or_404()
    else:
        task = Task.query.filter_by(id=task_id).first_or_404()

    assignees = []
    is_assigned = False
    user_assignment = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
    if role.name != 'Сотрудник':
        assignees = TaskUserAssignment.query.filter_by(task_id=task_id).all()

    if user_assignment:
        is_assigned = True

    if role.name == 'Сотрудник':
        assignees = [user_assignment] if user_assignment else []

    return render_template('tasks/details.html', task=task, assignees=assignees, today=date.today(), user_id=user_id, user_role=role, is_assigned=is_assigned, user_assignment=user_assignment)

@tasks_bp.route('/<int:task_id>/report', methods=['GET'])
@jwt_required()
@roles_required("Руководитель")
def generate_task_report(task_id):
    # Получаем задачу по ID
    task = Task.query.get_or_404(task_id)
    assignees = TaskUserAssignment.query.filter_by(task_id=task_id).all()  # Исполнители задачи

    output = StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Заголовки
    writer.writerow(['Задача', 'Описание', 'Приоритет', 'Дата начала', 'Дата выполнения'])
    writer.writerow([task.title, task.description, task.priority, task.starts_at.strftime('%d.%m.%Y'), task.deadline_at.strftime('%d.%m.%Y')])

    writer.writerow([])
    writer.writerow(['Исполнитель', 'Прогресс'])

    # Исполнители
    for assignment in assignees:
        writer.writerow([assignment.user.name, assignment.status])

    output.seek(0)
    bytes_io = BytesIO()
    bytes_io.write(output.getvalue().encode('cp1251'))
    bytes_io.seek(0)

    return send_file(bytes_io, mimetype='text/csv', as_attachment=True, download_name='report.csv')