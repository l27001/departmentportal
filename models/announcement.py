from extensions import db
from datetime import datetime


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    creator = db.relationship("User")
    views = db.relationship("AnnouncementView", backref="announcement", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
            "view_count": len(self.views),
        }


class AnnouncementView(db.Model):
    __tablename__ = "announcement_views"

    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_user_view"),
    )
