from extensions import db
from datetime import datetime


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    news_id = db.Column(db.Integer, db.ForeignKey("news.id", ondelete="CASCADE"), nullable=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey("announcements.id", ondelete="CASCADE"), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("department_meetings.id", ondelete="CASCADE"), nullable=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey("general_chat.id", ondelete="CASCADE"), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref="attachments")
    news = db.relationship("News", backref="attachments")
    announcement = db.relationship("Announcement", backref="attachments")
    document = db.relationship("Document")
    meeting = db.relationship("DepartmentMeeting", backref="attachments")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "news_id": self.news_id,
            "announcement_id": self.announcement_id,
            "document_id": self.document_id,
            "meeting_id": self.meeting_id,
            "chat_message_id": self.chat_message_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "size": self.size,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
