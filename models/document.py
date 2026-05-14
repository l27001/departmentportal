from datetime import datetime
from extensions import db

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='documents', lazy=True)
    attachments = db.relationship('Attachment', lazy=True, cascade='all, delete-orphan', overlaps="document")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'attachments': [a.to_dict() for a in self.attachments],
        }


class DocumentLink(db.Model):
    __tablename__ = 'document_links'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='document_links', lazy=True)
