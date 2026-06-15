from extensions import db
from werkzeug.security import generate_password_hash
from models.role import Role
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    name = db.Column(db.String(255))
    job_title = db.Column(db.String(255))

    phone = db.Column(db.String(50), nullable=True)
    academic_title = db.Column(db.String(255), nullable=True)
    degree = db.Column(db.String(50), nullable=True)
    rate_type = db.Column(db.String(50), nullable=False, default="основная")
    rate_count = db.Column(db.Float, nullable=False, default=1.0)
    avatar_url = db.Column(db.String(500), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    hire_date = db.Column(db.Date, nullable=True)
    dismissal_date = db.Column(db.Date, nullable=True)

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = db.relationship(Role)

    groups = db.relationship(
        "Group",
        secondary="user_groups",
        backref=db.backref("users", lazy="dynamic"),
        lazy="dynamic"
    )

    @property
    def short_name(self):
        parts = (self.name or "").split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
        elif len(parts) == 2:
            return f"{parts[0]} {parts[1][0]}."
        return self.name or "Профиль"

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.name,
            "phone": self.phone,
            "job_title": self.job_title,
            "academic_title": self.academic_title,
            "degree": self.degree,
            "rate_type": self.rate_type,
            "rate_count": self.rate_count,
            "avatar_url": self.avatar_url,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "is_active": self.is_active,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "dismissal_date": self.dismissal_date.isoformat() if self.dismissal_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }