from extensions import db
from datetime import datetime


class DepartmentMeeting(db.Model):
    __tablename__ = "department_meetings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship(
        "Task",
        secondary="meeting_tasks",
        backref="meetings",
        lazy=True,
        overlaps="meetings",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "task_ids": [t.id for t in self.tasks],
            "attachment_ids": [att.id for att in self.attachments],
        }


class MeetingTask(db.Model):
    __tablename__ = "meeting_tasks"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("department_meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id = db.Column(
        db.Integer,
        db.ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    __table_args__ = (
        db.UniqueConstraint("meeting_id", "task_id", name="uq_meeting_task"),
    )
