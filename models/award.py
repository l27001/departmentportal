from app import db
from datetime import datetime

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
    
    def __repr__(self):
        return f'<Award {self.title}>'

class Publication(db.Model):
    __tablename__ = 'publications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='publications')
    
    # Обязательные для всех типов
    publication_type = db.Column(db.String(50), nullable=False)  # book, journal_article, collection_article, dissertation, abstract, internet
    title = db.Column(db.String(500), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    gost_string = db.Column(db.Text, nullable=True)  # АВТО-ГЕНЕРИРУЕТСЯ
    
    # КНИГА (book)
    authors = db.Column(db.String(500))  # для большинства типов
    edition = db.Column(db.String(50))  # "3-е", "2-е" и т.д.
    city = db.Column(db.String(100))  # М., СПб., Екатеринбург и т.д.
    publisher = db.Column(db.String(255))
    pages = db.Column(db.String(50))  # "999" или "25-30"
    
    # ЖУРНАЛ (journal_article)
    journal_name = db.Column(db.String(255))
    issue = db.Column(db.String(50))  # "10", "2-3"
    
    # СБОРНИК (collection_article)
    article_title = db.Column(db.String(500))  # если отличается от title
    collection_title = db.Column(db.String(500))
    
    # ДИССЕРТАЦИЯ / АВТОРЕФЕРАТ (dissertation, abstract)
    author_single = db.Column(db.String(255))  # для диссертаций (один автор)
    degree = db.Column(db.String(50))  # "д-р.", "канд."
    field = db.Column(db.String(100))  # "экон.", "техн.", "биол."
    specialty_code = db.Column(db.String(20))  # "01.01.01"
    
    # ИНТЕРНЕТ-РЕСУРС (internet)
    site_name = db.Column(db.String(255))
    url = db.Column(db.String(500))
    access_date = db.Column(db.String(20))  # "01.01.2021"
    
    # ОБЩИЕ ПОЛЯ
    doi = db.Column(db.String(100))
    points = db.Column(db.Integer, default=5)
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Publication {self.title}>'
    
    def get_gost_string(self):
        """Получить ГОСТ-строку (если не сгенерирована, сгенерировать)"""
        # if not self.gost_string:
        #     self.gost_string = generate_gost_string(self)
        return self.gost_string


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
    training_type = db.Column(db.String(50), nullable=False)  # course, workshop, seminar, webinar, certification
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    duration_hours = db.Column(db.Integer)  # Продолжительность в часах
    certificate_number = db.Column(db.String(255))  # Номер сертификата
    certificate_url = db.Column(db.String(500))  # Ссылка на сертификат
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=6)
    status = db.Column(db.String(20), default='active')
    level = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Training {self.title}>'
