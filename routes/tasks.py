from flask import Blueprint, request, jsonify, render_template, flash, url_for, redirect, send_file, abort
from io import StringIO, BytesIO
import csv
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, date
from sqlalchemy import desc, or_, exists
from extensions import db
from models.task import Task, TaskUserAssignment
from models.user import User
from models.role import Role
from models.group import Group, UserGroup, TaskGroup
from decorators.roles import roles_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    users = []
    groups = []
    if role.name in ("Документовед", "Руководитель"):
        tasks = Task.query.order_by(desc(Task.deadline_at)).all()
        users = User.query.all()
        groups = Group.query.all()

        task_ids_by_assignment = db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id).all()
        task_ids_by_group = (
            db.session.query(TaskGroup.task_id)
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(UserGroup.user_id == user_id)
            .all()
        )
        assigned_task_ids = {t[0] for t in task_ids_by_assignment} | {t[0] for t in task_ids_by_group}
    else:
        task_ids_by_assignment = db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id)
        task_ids_by_group = (
            db.session.query(TaskGroup.task_id)
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(UserGroup.user_id == user_id)
        )
        tasks = (
            Task.query
            .filter(
                or_(
                    Task.id.in_(task_ids_by_assignment),
                    Task.id.in_(task_ids_by_group)
                )
            )
            .order_by(desc(Task.deadline_at))
            .all()
        )
        assigned_task_ids = {t.id for t in tasks}

    return render_template("tasks/list.html", tasks=tasks, role=role, users=users, groups=groups, assigned_task_ids=assigned_task_ids, user_id=user_id, today=date.today())

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
            assignees = [user_id]
        group_ids = request.form.getlist('groups')
        is_personal = role.name != 'Руководитель' or (len(assignees) == 0 and len(group_ids) == 0)

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            starts_at=starts_at,
            deadline_at=deadline_at,
            is_personal=is_personal,
            no_review=no_review,
            creator_id=user_id
        )

        db.session.add(new_task)
        db.session.commit()

        for assignee_id in assignees:
            task_assignment = TaskUserAssignment(task_id=new_task.id, user_id=assignee_id)
            db.session.add(task_assignment)

        for group_id in group_ids:
            task_group = TaskGroup(task_id=new_task.id, group_id=int(group_id))
            db.session.add(task_group)

        db.session.commit()

        flash('Задача успешно создана!', 'success')
        return redirect(url_for('tasks.list_tasks'))

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

    if role == "Сотрудник":
        task_ids_by_assignment = db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id)
        task_ids_by_group = (
            db.session.query(TaskGroup.task_id)
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(UserGroup.user_id == user_id)
        )
        query = query.filter(
            or_(
                Task.id.in_(task_ids_by_assignment),
                Task.id.in_(task_ids_by_group)
            )
        )

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

    if role.name == "Сотрудник":
        task_ids_by_assignment = db.session.query(TaskUserAssignment.task_id).filter(TaskUserAssignment.user_id == user_id)
        task_ids_by_group = (
            db.session.query(TaskGroup.task_id)
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(UserGroup.user_id == user_id)
        )
        tasks = (
            Task.query
            .filter(
                or_(
                    Task.id.in_(task_ids_by_assignment),
                    Task.id.in_(task_ids_by_group)
                )
            )
            .all()
        )
    else:
        tasks = Task.query.order_by(desc(Task.deadline_at)).all()

    events = []
    for task in tasks:
        status = None
        if(len(task.assignments) > 0):
            status = task.assignments[0].status
        color = None
        if(task.priority == 'high'):
            color = 'red'
        elif(task.priority == 'medium'):
            color = 'orange'
        else:
            color = 'light-blue'
        events.append({
            'title': task.title,
            'start': task.starts_at.strftime('%Y-%m-%d'),  # Дата окончания задачи
            'end': task.deadline_at.strftime('%Y-%m-%d'),  # Дата окончания задачи
            'description': task.description,
            'color': color,
            'url': url_for('tasks.task_details', task_id=task.id),
            'status': status
        })
    return render_template("tasks/calendar.html", tasks=events)

@tasks_bp.route("/<int:task_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(task_id):
    user_id = get_jwt_identity()
    data = request.json

    task_status = TaskUserAssignment.query.filter_by(
        task_id=task_id,
        user_id=user_id
    ).first()

    if not task_status:
        has_group = (
            TaskGroup.query
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(TaskGroup.task_id == task_id, UserGroup.user_id == user_id)
            .first()
        )
        if not has_group:
            return jsonify({"msg": "Task not assigned"}), 404
        task_status = TaskUserAssignment(task_id=task_id, user_id=user_id, status=data["status"].lower())
        db.session.add(task_status)
    else:
        task_status.status = data["status"].lower()

    db.session.commit()

    return jsonify({"msg": "Status updated"})

@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
@roles_required("Руководитель")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    return jsonify({"msg": "Task deleted"})

@tasks_bp.route('/get/<int:task_id>', methods=['GET'])
@jwt_required()
def task_details(task_id):
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()

    if role.name == 'Сотрудник':
        has_assignment = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        has_group = (
            TaskGroup.query
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(TaskGroup.task_id == task_id, UserGroup.user_id == user_id)
            .first()
        )
        if not has_assignment and not has_group:
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
    else:
        has_group = (
            TaskGroup.query
            .join(UserGroup, UserGroup.group_id == TaskGroup.group_id)
            .filter(TaskGroup.task_id == task_id, UserGroup.user_id == user_id)
            .first()
        )
        if has_group:
            is_assigned = True
            user_assignment = TaskUserAssignment(task_id=task_id, user_id=user_id, status="не начата")
            db.session.add(user_assignment)
            db.session.commit()

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