import json
from extensions import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    priority = db.Column(db.String(20), default="medium")

    deadline_at = db.Column(db.Date, nullable=False)

    no_review = db.Column(db.Boolean, default=False, nullable=False)

    creator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    creator = db.relationship("User", backref="created_tasks")

    assignments = db.relationship(
        "TaskUserAssignment",
        cascade="all, delete-orphan",
        backref="task"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "deadline_at": self.deadline_at.isoformat(),
            "no_review": self.no_review,
            "creator_id": self.creator_id
        }
    
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class TaskUserAssignment(db.Model):
    __tablename__ = "task_user_assignments"

    task_id = db.Column(
        db.Integer,
        db.ForeignKey("tasks.id"),
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True
    )

    status = db.Column(
        db.String(50),
        default="не начата"
    )

    marked_complete = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref="task_assignments")