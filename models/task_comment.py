from extensions import db
from datetime import datetime


class TaskComment(db.Model):
    __tablename__ = "task_comments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref=db.backref("comments", cascade="all, delete-orphan", passive_deletes=True))
    author = db.relationship("User", foreign_keys=[author_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient.name if self.recipient else None,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
