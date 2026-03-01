from extensions import db
from werkzeug.security import generate_password_hash
from models.role import Role

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    name = db.Column(db.String(255))
    job_title = db.Column(db.String(255))

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False
    )

    role = db.relationship(Role)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.name
        }