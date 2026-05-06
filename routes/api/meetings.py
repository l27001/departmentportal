from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import date
from extensions import db
from models.meeting import DepartmentMeeting, MeetingTask
from models.task import Task
from models.attachment import Attachment

meetings_bp = Blueprint("api_meetings", __name__, url_prefix="/api/meetings")


@meetings_bp.route("/", methods=["GET"])
@jwt_required()
def list_meetings():
    """Список заседаний кафедры"""
    user_id = get_jwt_identity()
    role = get_jwt()["role"]

    query = DepartmentMeeting.query.order_by(DepartmentMeeting.date.desc())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    total = query.count()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meetings = pagination.items

    return jsonify({
        "meetings": [m.to_dict() for m in meetings],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": pagination.pages,
        }
    })


@meetings_bp.route("/", methods=["POST"])
@jwt_required()
def create_meeting():
    """Создать заседание кафедры (Руководитель, Документовед)"""
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    user_id = get_jwt_identity()
    data = request.json

    title = data.get("title")
    description = data.get("description", "")
    date_str = data.get("date")

    if not title or not date_str:
        return jsonify({"msg": "Заполните обязательные поля"}), 400

    try:
        meeting_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"msg": "Неверный формат даты"}), 400

    meeting = DepartmentMeeting(
        title=title,
        description=description,
        date=meeting_date,
    )

    task_ids = data.get("task_ids", [])

    for tid in task_ids:
        task = Task.query.get(tid)
        if task:
            meeting.tasks.append(task)

    db.session.add(meeting)
    db.session.commit()

    return jsonify(meeting.to_dict()), 201


@meetings_bp.route("/<int:meeting_id>", methods=["GET"])
@jwt_required()
def get_meeting(meeting_id):
    """Получить заседание по ID"""
    meeting = DepartmentMeeting.query.get_or_404(meeting_id)

    result = meeting.to_dict()
    result["tasks"] = [
        {
            "id": t.id,
            "title": t.title,
            "deadline_at": t.deadline_at.isoformat() if t.deadline_at else None,
        }
        for t in meeting.tasks
    ]
    result["attachments"] = [
        {
            "id": a.id,
            "file_name": a.file_name,
            "size": a.size,
            "mime_type": a.mime_type,
            "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None,
        }
        for a in meeting.attachments
    ]
    return jsonify(result)


@meetings_bp.route("/<int:meeting_id>", methods=["PATCH"])
@jwt_required()
def update_meeting(meeting_id):
    """Обновить заседание кафедры (Руководитель, Документовед)"""
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    meeting = DepartmentMeeting.query.get_or_404(meeting_id)
    data = request.json

    if "title" in data:
        meeting.title = data["title"]
    if "description" in data:
        meeting.description = data["description"]
    if "date" in data:
        try:
            meeting.date = date.fromisoformat(data["date"])
        except ValueError:
            return jsonify({"msg": "Неверный формат даты"}), 400

    if "task_ids" in data:
        meeting.tasks = []
        for tid in data["task_ids"]:
            task = Task.query.get(tid)
            if task:
                meeting.tasks.append(task)

    db.session.commit()
    return jsonify(meeting.to_dict())


@meetings_bp.route("/<int:meeting_id>", methods=["DELETE"])
@jwt_required()
def delete_meeting(meeting_id):
    """Удалить заседание кафедры (Руководитель, Документовед)"""
    role = get_jwt()["role"]
    if role not in (1, 2):
        return jsonify({"msg": "Доступ запрещён"}), 403

    meeting = DepartmentMeeting.query.get_or_404(meeting_id)
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({"msg": "Заседание удалено"})
