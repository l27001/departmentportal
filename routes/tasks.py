from flask import Blueprint, request, jsonify, render_template, flash, url_for, redirect, send_file
from io import StringIO, BytesIO
import csv
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, date
from sqlalchemy import desc
from extensions import db
from models.task import Task, TaskUserAssignment
from models.user import User
from models.role import Role
from decorators.roles import roles_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    users = []
    if role.name in ("Документовед", "Руководитель"):
        tasks = Task.query.join(Task.assignments.and_(TaskUserAssignment.user_id == user_id), isouter=True).order_by(desc(Task.deadline_at)).all()
        users = User.query.all()
    else:
        tasks = (
            Task.query
            .join(TaskUserAssignment)
            .filter(TaskUserAssignment.user_id == user_id)
            .order_by(desc(Task.deadline_at))
            .all()
        )

    return render_template("tasks/list.html", tasks=tasks, role=role, users=users, user_id=user_id, today=date.today())

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
        try:
            assignees = request.form.getlist('assignees')
        except (ValueError):
            assignees = [user_id]
        is_personal = role.name != 'Руководитель' or len(assignees) == 0

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            starts_at=starts_at,
            deadline_at=deadline_at,
            is_personal=is_personal,
            creator_id=user_id  # Создатель задачи
        )

        # Сохранение задачи в базе данных
        db.session.add(new_task)
        db.session.commit()

        for assignee_id in assignees:
            task_assignment = TaskUserAssignment(task_id=new_task.id, user_id=assignee_id)
            db.session.add(task_assignment)
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
        query = (
            query.join(TaskUserAssignment)
            .filter(TaskUserAssignment.user_id == user_id)
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
    role = get_jwt()["role"]
    tasks = []

    if role == "Сотрудник":
        tasks = (
            Task.query
            .join(TaskUserAssignment)
            .filter(TaskUserAssignment.user_id == user_id)
            .all()
        )
    else:
        tasks = Task.query.join(TaskUserAssignment).all()

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
        return jsonify({"msg": "Task not assigned"}), 404

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
    task = Task.query.filter_by(id=task_id).join(Task.assignments.and_(TaskUserAssignment.user_id == user_id), isouter=True).first_or_404()
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    assignees = []
    if(role.name != 'Сотрудник'):
        assignees = TaskUserAssignment.query.filter_by(task_id=task_id).all()  # Получаем исполнителей задачи
    else:
        assignees = [TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first_or_404()]
    
    return render_template('tasks/details.html', task=task, assignees=assignees, today=date.today(), user_id=user_id, user_role=role)

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