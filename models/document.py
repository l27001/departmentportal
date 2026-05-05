from datetime import datetime
from extensions import db

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='documents', lazy=True)
    attachment = db.relationship('Attachment', lazy=True)
    
    def __init__(self, title, creator_id, attachment_id, category=None):
        self.title = title
        self.creator_id = creator_id
        self.attachment_id = attachment_id
        self.category = category
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_name': self.attachment.file_name if self.attachment else None,
            'mime_type': self.attachment.mime_type if self.attachment else None,
            'size': self.attachment.size if self.attachment else None,
        }
