from extensions import db
from datetime import datetime


class GeneralChatMessage(db.Model):
    __tablename__ = "general_chat"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User", backref="chat_messages")

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
