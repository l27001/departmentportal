from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
from sqlalchemy import desc, asc
from extensions import db
from models.task import Task, TaskUserAssignment
from models.user import User
from models.group import Group, UserGroup

api_tasks_bp = Blueprint("api_tasks", __name__, url_prefix="/api/tasks")


@api_tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    """Получить список задач текущего пользователя
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: priority
        in: query
        type: string
        enum: [low, medium, high]
      - name: status
        in: query
        type: string
        enum: [не начата, в работе, завершена]
      - name: date_from
        in: query
        type: string
        format: date
      - name: date_to
        in: query
        type: string
        format: date
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Список задач с пагинацией
        schema:
          type: object
          properties:
            tasks:
              type: array
              items:
                $ref: '#/definitions/Task'
            pagination:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                total_pages:
                  type: integer
    """
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

    tasks = query.order_by(asc(Task.deadline_at)).all()

    if status:
        tasks = [
            t for t in tasks
            if any(
                s.status == status and s.user_id == user_id
                for s in t.assignments
            )
        ]

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    total = len(tasks)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tasks = tasks[start:end]
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

    return jsonify({
        "tasks": [task.to_dict() for task in paginated_tasks],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    })


@api_tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create_task():
    """Создать задачу (только Руководитель)
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/TaskInput'
    responses:
      201:
        description: Задача создана
        schema:
          $ref: '#/definitions/Task'
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role != 1:
        return jsonify({"msg": "Доступ запрещён"}), 403

    user_id = get_jwt_identity()
    data = request.json

    title = data.get("title")
    description = data.get("description", "")
    priority = data.get("priority", "medium")
    allowed_priorities = ["low", "medium", "high"]
    if priority not in allowed_priorities:
        return jsonify({"msg": f"Недопустимый приоритет. Разрешены: {', '.join(allowed_priorities)}"}), 400
    starts_at = data.get("starts_at")
    deadline_at = data.get("deadline_at")
    no_review = data.get("no_review", False)
    assignees = data.get("assignees", [])

    if not title or not starts_at or not deadline_at:
        return jsonify({"msg": "Заполните обязательные поля"}), 400

    try:
        starts_at_date = date.fromisoformat(starts_at)
        deadline_at_date = date.fromisoformat(deadline_at)
    except ValueError:
        return jsonify({"msg": "Неверный формат даты"}), 400

    is_personal = len(assignees) == 0

    task = Task(
        title=title,
        description=description,
        priority=priority,
        starts_at=starts_at_date,
        deadline_at=deadline_at_date,
        is_personal=is_personal,
        no_review=no_review,
        creator_id=user_id
    )
    db.session.add(task)
    db.session.flush()

    for assignee_id in assignees:
        assignment = TaskUserAssignment(task_id=task.id, user_id=assignee_id)
        db.session.add(assignment)

    db.session.commit()

    return jsonify(task.to_dict()), 201


@api_tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    """Получить задачу по ID
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Задача с исполнителями и группами
        schema:
          $ref: '#/definitions/TaskDetail'
      403:
        description: Нет доступа к задаче
      404:
        description: Не найдено
    """
    user_id = get_jwt_identity()
    role = get_jwt()["role"]

    if role != 1:
        has_assignment = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not has_assignment:
            return jsonify({"msg": "Нет доступа к задаче"}), 403

    task = Task.query.get_or_404(task_id)
    assignments = TaskUserAssignment.query.filter_by(task_id=task_id).all()

    result = task.to_dict()
    result["assignments"] = [
        {
            "user_id": a.user_id,
            "user_name": a.user.name if a.user else None,
            "status": a.status,
            "marked_complete": a.marked_complete,
            "approved": a.approved,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "approved_at": a.approved_at.isoformat() if a.approved_at else None,
        }
        for a in assignments
    ]
    return jsonify(result)


@api_tasks_bp.route("/<int:task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    """Обновить задачу (только Руководитель)
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            priority:
              type: string
              enum: [low, medium, high]
            starts_at:
              type: string
              format: date
            deadline_at:
              type: string
              format: date
            no_review:
              type: boolean
    responses:
      200:
        description: Задача обновлена
        schema:
          $ref: '#/definitions/Task'
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role != 1:
        return jsonify({"msg": "Доступ запрещён"}), 403

    task = Task.query.get_or_404(task_id)
    data = request.json

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "priority" in data:
        allowed_priorities = ["low", "medium", "high"]
        if data["priority"] not in allowed_priorities:
            return jsonify({"msg": f"Недопустимый приоритет. Разрешены: {', '.join(allowed_priorities)}"}), 400
        task.priority = data["priority"]
    if "starts_at" in data:
        task.starts_at = date.fromisoformat(data["starts_at"])
    if "deadline_at" in data:
        task.deadline_at = date.fromisoformat(data["deadline_at"])
    if "no_review" in data:
        task.no_review = data["no_review"]

    db.session.commit()
    return jsonify(task.to_dict())


@api_tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    """Удалить задачу (только Руководитель)
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Задача удалена
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role != 1:
        return jsonify({"msg": "Доступ запрещён"}), 403

    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"msg": "Задача удалена"})


@api_tasks_bp.route("/<int:task_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(task_id):
    """Обновить статус исполнителя задачи
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status:
              type: string
              enum: [не начата, в работе, завершена]
    responses:
      200:
        description: Статус обновлён
      404:
        description: Задача не назначена
    """
    user_id = get_jwt_identity()
    data = request.json

    allowed_statuses = ["не начата", "в работе", "завершена"]
    new_status = data.get("status", "").strip().lower()

    if new_status not in allowed_statuses:
        return jsonify({"msg": f"Недопустимый статус. Разрешены: {', '.join(allowed_statuses)}"}), 400

    task_status = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()

    if not task_status:
        return jsonify({"msg": "Task not assigned"}), 404

    task = Task.query.get_or_404(task_id)

    if new_status == "завершена" and not task.no_review:
        task_status.status = "на проверке"
        task_status.marked_complete = True
        task_status.completed_at = datetime.utcnow()
        task_status.approved = False
    else:
        task_status.status = new_status
        if new_status == "завершена":
            task_status.marked_complete = True
            task_status.completed_at = datetime.utcnow()
            task_status.approved = True
        else:
            task_status.marked_complete = False
            task_status.completed_at = None

    db.session.commit()
    return jsonify({"msg": "Status updated", "status": task_status.status})


@api_tasks_bp.route("/<int:task_id>/assignees/<int:assignee_id>/approve", methods=["PATCH"])
@jwt_required()
def approve_assignee(task_id, assignee_id):
    """Подтвердить выполнение задачи исполнителем (только Руководитель)
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: assignee_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            approved:
              type: boolean
              default: true
    responses:
      200:
        description: Статус подтверждён
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    assignment = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=assignee_id).first_or_404()
    data = request.json

    if data.get("approved", True):
        assignment.approved = True
        assignment.approved_at = datetime.utcnow()
        assignment.status = "завершена"
    else:
        assignment.approved = False
        assignment.status = "в работе"
        assignment.marked_complete = False

    db.session.commit()
    return jsonify({"msg": "Status updated"})


@api_tasks_bp.route("/<int:task_id>/assignees", methods=["POST"])
@jwt_required()
def add_assignees(task_id):
    """Добавить исполнителей к задаче (только Руководитель)
    ---
    tags: [Tasks]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [user_ids]
          properties:
            user_ids:
              type: array
              items:
                type: integer
    responses:
      200:
        description: Исполнители добавлены
      403:
        description: Доступ запрещён
    """
    role = get_jwt()["role"]
    if role != 1:
        return jsonify({"msg": "Доступ запрещён"}), 403

    Task.query.get_or_404(task_id)
    data = request.json
    user_ids = data.get("user_ids", [])

    for uid in user_ids:
        existing = TaskUserAssignment.query.filter_by(task_id=task_id, user_id=uid).first()
        if not existing:
            assignment = TaskUserAssignment(task_id=task_id, user_id=uid)
            db.session.add(assignment)

    db.session.commit()
    return jsonify({"msg": "Assignees added"})

