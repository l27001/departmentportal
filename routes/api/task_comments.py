from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.task_comment import TaskComment

task_comments_bp = Blueprint("api_task_comments", __name__, url_prefix="/api/tasks")


@task_comments_bp.route("/<int:task_id>/comments", methods=["GET"])
@jwt_required()
def list_comments(task_id):
    """Получить комментарии к задаче
    ---
    tags: [Task Comments]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Список комментариев
        schema:
          type: array
          items:
            $ref: '#/definitions/TaskComment'
    """
    comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments])


@task_comments_bp.route("/<int:task_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(task_id):
    """Добавить комментарий к задаче
    ---
    tags: [Task Comments]
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
          required: [text]
          properties:
            text:
              type: string
            recipient_id:
              type: integer
    responses:
      201:
        description: Комментарий добавлен
        schema:
          $ref: '#/definitions/TaskComment'
      400:
        description: Пустой комментарий
    """
    user_id = get_jwt_identity()
    data = request.json
    text = data.get("text", "").strip()
    recipient_id = data.get("recipient_id")

    if not text:
        return jsonify({"msg": "Комментарий не может быть пустым"}), 400

    comment = TaskComment(
        task_id=task_id,
        author_id=user_id,
        recipient_id=recipient_id or user_id,
        text=text,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201


@task_comments_bp.route("/<int:task_id>/comments/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(task_id, comment_id):
    """Удалить комментарий к задаче
    ---
    tags: [Task Comments]
    security:
      - BearerAuth: []
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: comment_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Комментарий удалён
      403:
        description: Можно удалять только свои комментарии
    """
    user_id = get_jwt_identity()
    comment = TaskComment.query.filter_by(id=comment_id, task_id=task_id).first_or_404()

    if comment.author_id != user_id:
        return jsonify({"msg": "Можно удалять только свои комментарии"}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"msg": "Комментарий удалён"})
