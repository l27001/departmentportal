from extensions import db
from datetime import datetime


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref="attachments")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "size": self.size,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
