from extensions import db
from datetime import datetime
from utils import generate_gost_string

LEVEL_MAP = {
    'university': 'вузовский',
    'regional': 'региональный',
    'faculty': 'факультетский',
    'federal': 'федеральный',
    'international': 'международный',
    'sgtu': 'сгту',
}

AWARD_TYPE_MAP = {
    'certificate': 'сертификат',
    'grant': 'грант',
    'prize': 'премия',
    'scholarship': 'стипендия',
}

ROLE_MAP = {
    'speaker': 'докладчик',
    'participant': 'участник',
    'organizer': 'организатор',
}

class Award(db.Model):
    __tablename__ = 'awards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='awards')
    
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    award_type = db.Column(db.String(50), nullable=False)
    issuer = db.Column(db.String(255))
    date_received = db.Column(db.Date, nullable=False, index=True)
    points = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default='active')
    level = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_level_display(self):
        return LEVEL_MAP.get(self.level, self.level)

    def get_award_type_display(self):
        return AWARD_TYPE_MAP.get(self.award_type, self.award_type)

    def __repr__(self):
        return f'<Award {self.title}>'

class PublicationBase:
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    publication_date = db.Column(db.Date, nullable=True)
    gost_string = db.Column(db.Text, nullable=True)
    isbn = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_gost_string(self):
        if not self.gost_string:
            self.gost_string = generate_gost_string(self)
        return self.gost_string

class Book(db.Model, PublicationBase):
    __tablename__ = 'publication_books'
    user = db.relationship('User', backref='books')
    authors = db.Column(db.String(500))
    edition = db.Column(db.String(50))
    city = db.Column(db.String(100))
    publisher = db.Column(db.String(255))
    pages = db.Column(db.String(50))

    def __repr__(self):
        return f'<Book {self.title}>'

class JournalArticle(db.Model, PublicationBase):
    __tablename__ = 'publication_journal_articles'
    user = db.relationship('User', backref='journal_articles')
    authors = db.Column(db.String(500))
    journal_name = db.Column(db.String(255))
    issue = db.Column(db.String(50))
    pages = db.Column(db.String(50))

    def __repr__(self):
        return f'<JournalArticle {self.title}>'

class CollectionArticle(db.Model, PublicationBase):
    __tablename__ = 'publication_collection_articles'
    user = db.relationship('User', backref='collection_articles')
    authors = db.Column(db.String(500))
    collection_title = db.Column(db.String(500))
    city = db.Column(db.String(100))
    publisher = db.Column(db.String(255))
    pages = db.Column(db.String(50))

    def __repr__(self):
        return f'<CollectionArticle {self.title}>'

class Dissertation(db.Model, PublicationBase):
    __tablename__ = 'publication_dissertations'
    user = db.relationship('User', backref='dissertations')
    author_single = db.Column(db.String(255))
    degree = db.Column(db.String(50))
    field = db.Column(db.String(100))
    specialty_code = db.Column(db.String(20))
    city = db.Column(db.String(100))
    pages = db.Column(db.String(50))

    def __repr__(self):
        return f'<Dissertation {self.title}>'

class Abstract(db.Model, PublicationBase):
    __tablename__ = 'publication_abstracts'
    user = db.relationship('User', backref='abstracts')
    author_single = db.Column(db.String(255))
    degree = db.Column(db.String(50))
    field = db.Column(db.String(100))
    specialty_code = db.Column(db.String(20))
    city = db.Column(db.String(100))
    pages = db.Column(db.String(50))

    def __repr__(self):
        return f'<Abstract {self.title}>'

class Internet(db.Model, PublicationBase):
    __tablename__ = 'publication_internets'
    user = db.relationship('User', backref='internets')
    authors = db.Column(db.String(500))
    site_name = db.Column(db.String(255))
    url = db.Column(db.String(500))
    access_date = db.Column(db.String(20))

    def __repr__(self):
        return f'<Internet {self.title}>'

class NewspaperArticle(db.Model, PublicationBase):
    __tablename__ = 'publication_newspaper_articles'
    user = db.relationship('User', backref='newspaper_articles')
    authors = db.Column(db.String(500))
    newspaper_name = db.Column(db.String(255))
    newspaper_date = db.Column(db.String(20))
    issue = db.Column(db.String(50))

    def __repr__(self):
        return f'<NewspaperArticle {self.title}>'

class Conference(db.Model):
    __tablename__ = 'conferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='conferences')
    
    name = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(50), nullable=False)
    paper_title = db.Column(db.String(255))
    conference_date = db.Column(db.Date, nullable=False, index=True)
    location = db.Column(db.String(255))
    conference_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=8)
    status = db.Column(db.String(20), default='active')
    coauthors = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_role_display(self):
        return ROLE_MAP.get(self.role, self.role)
    
    def __repr__(self):
        return f'<Conference {self.name}>'

class Training(db.Model):
    __tablename__ = 'trainings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='trainings')
    
    title = db.Column(db.String(255), nullable=False, index=True)
    organization = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    training_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    duration_hours = db.Column(db.Integer)
    certificate_number = db.Column(db.String(255))
    certificate_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=6)
    status = db.Column(db.String(20), default='active')
    level = db.Column(db.String(50), nullable=True)
    state_issued = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_level_display(self):
        return LEVEL_MAP.get(self.level, self.level)

    def __repr__(self):
        return f'<Training {self.title}>'

class RatingTemplate(db.Model):
    __tablename__ = 'rating_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    sub_type = db.Column(db.String(50), nullable=True)
    template_data = db.Column(db.JSON, nullable=False, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<RatingTemplate {self.name} ({self.entity_type})>'


class EntityCoauthor(db.Model):
    __tablename__ = 'entity_coauthors'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='coauthored_entities')

    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'user_id', name='uq_entity_coauthor'),
    )

    def __repr__(self):
        return f'<EntityCoauthor {self.entity_type}:{self.entity_id} user={self.user_id}>'


class EntitySupervisor(db.Model):
    __tablename__ = 'entity_supervisors'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='supervised_entities')

    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'user_id', name='uq_entity_supervisor'),
    )

    def __repr__(self):
        return f'<EntitySupervisor {self.entity_type}:{self.entity_id} user={self.user_id}>'
