from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, DateField, IntegerField, SubmitField, URLField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

AWARD_LEVELS = [
    ('university', 'вузовский'),
    ('regional', 'региональный'),
    ('faculty', 'факультетский'),
    ('federal', 'федеральный'),
    ('international', 'международный'),
    ('sgtu', 'СГТУ'),
]

AWARD_TYPES = [
    ('certificate', 'Сертификат'),
    ('grant', 'Грант'),
    ('prize', 'Премия'),
    ('scholarship', 'Стипендия'),
]

CONFERENCE_ROLES = [
    ('speaker', 'Докладчик'),
    ('participant', 'Участник'),
    ('organizer', 'Организатор'),
]

PUBLICATION_TYPES = [
    ('book', 'Книга'),
    ('journal_article', 'Статья из журнала'),
    ('collection_article', 'Статья из сборника'),
    ('dissertation', 'Диссертация'),
    ('abstract', 'Автореферат'),
    ('internet', 'Интернет-ресурс'),
    ('newspaper_article', 'Статья из газеты'),
]

DEGREES = [
    ('д-р.', 'Доктор наук (д-р.)'),
    ('канд.', 'Кандидат наук (канд.)'),
]

FIELDS_OF_STUDY = [
    ('экон.', 'Экономические (экон.)'),
    ('техн.', 'Технические (техн.)'),
    ('биол.', 'Биологические (биол.)'),
    ('физ.', 'Физические (физ.)'),
    ('хим.', 'Химические (хим.)'),
    ('юрид.', 'Юридические (юрид.)'),
    ('пед.', 'Педагогические (пед.)'),
    ('психол.', 'Психологические (психол.)'),
    ('филол.', 'Филологические (филол.)'),
    ('ист.', 'Исторические (ист.)'),
]

class AwardForm(FlaskForm):
    title = StringField('Название награды', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Описание', validators=[Optional(), Length(max=1000)])
    award_type = SelectField('Тип награды', choices=AWARD_TYPES, validators=[DataRequired()])
    issuer = StringField('Выдавшая организация', validators=[Optional(), Length(max=255)])
    date_received = DateField('Дата получения', validators=[DataRequired()])
    points = IntegerField('Очки рейтинга', default=10, validators=[Optional()])
    level = SelectField(
        'Уровень награды',
        choices=AWARD_LEVELS,
        validators=[DataRequired(message='Выберите уровень награды')]
    )
    owner_id = SelectField(
        'Автор записи',
        choices=[],
        validators=[Optional()],
    )
    submit = SubmitField('Сохранить')

class PublicationForm(FlaskForm):
    publication_type = SelectField('Тип публикации', choices=PUBLICATION_TYPES, validators=[DataRequired()])
    title = StringField('Название', validators=[DataRequired(), Length(min=5, max=500)])
    year = IntegerField('Год', validators=[DataRequired()])
    publication_date = DateField('Дата публикации', validators=[Optional()])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=100)])

    student_report = BooleanField('Студенческий доклад')
    scopus = BooleanField('Scopus')
    vak = BooleanField('ВАК')

    authors = StringField('Авторы (Фамилия И.О., через запятую)', validators=[Optional(), Length(max=500)])
    author_single = StringField('Автор (Фамилия И.О.)', validators=[Optional(), Length(max=255)])

    edition = StringField('Номер издания (например: 3-е)', validators=[Optional(), Length(max=50)])
    city = StringField('Город издания (М., СПб., или полностью)', validators=[Optional(), Length(max=100)])
    publisher = StringField('Издательство', validators=[Optional(), Length(max=255)])
    pages = StringField('Страницы', validators=[Optional(), Length(max=50)])

    journal_name = StringField('Название журнала', validators=[Optional(), Length(max=255)])
    issue = StringField('Номер выпуска', validators=[Optional(), Length(max=50)])

    collection_title = StringField('Название сборника', validators=[Optional(), Length(max=500)])

    degree = SelectField('Учёная степень', choices=DEGREES, validators=[Optional()])
    field = SelectField('Отрасль наук', choices=FIELDS_OF_STUDY, validators=[Optional()])
    specialty_code = StringField('Код специальности (например: 01.01.01)', validators=[Optional(), Length(max=20)])

    site_name = StringField('Название сайта', validators=[Optional(), Length(max=255)])
    url = URLField('Гиперссылка', validators=[Optional()])
    access_date = StringField('Дата обращения (ДД.ММ.ГГГГ)', validators=[Optional(), Length(max=20)])

    newspaper_name = StringField('Название газеты', validators=[Optional(), Length(max=255)])
    newspaper_date = StringField('Дата выхода газеты (ДД.ММ)', validators=[Optional(), Length(max=20)])

    coauthor_ids = SelectMultipleField(
        'Соавторы',
        choices=[],
        validators=[Optional()],
        render_kw={'class': 'form-select', 'size': 5}
    )

    supervisor_id = SelectField(
        'Научный руководитель',
        choices=[],
        validators=[Optional()],
    )

    owner_id = SelectField(
        'Автор записи',
        choices=[],
        validators=[Optional()],
    )

    submit = SubmitField('Сохранить')

class ConferenceForm(FlaskForm):
    name = StringField('Название конференции', validators=[DataRequired(), Length(min=3, max=255)])
    role = SelectField('Роль', choices=CONFERENCE_ROLES, validators=[DataRequired()])
    paper_title = StringField('Название доклада/статьи', validators=[Optional(), Length(max=255)])
    conference_date = DateField('Дата конференции', validators=[DataRequired()])
    location = StringField('Место проведения', validators=[Optional(), Length(max=255)])
    conference_url = URLField('Сайт конференции', validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional(), Length(max=1000)])
    points = IntegerField('Очки рейтинга', default=8, validators=[Optional()])
    coauthors = StringField(
        'Соавторы',
        description='Перечислите через запятую',
        validators=[Optional(), Length(max=255)]
    )
    owner_id = SelectField(
        'Автор записи',
        choices=[],
        validators=[Optional()],
    )
    submit = SubmitField('Сохранить')

class TrainingForm(FlaskForm):
    title = StringField('Название курса/тренинга', validators=[DataRequired(), Length(min=3, max=255)])
    organization = StringField('Организация', validators=[DataRequired(), Length(min=3, max=255)])
    city = StringField('Город проведения', validators=[Optional(), Length(max=100)])
    training_type = SelectField('Тип обучения', choices=[
        ('course', 'Курс'),
        ('workshop', 'Мастер-класс'),
        ('seminar', 'Семинар'),
        ('webinar', 'Вебинар'),
        ('certification', 'Сертификация')
    ], validators=[DataRequired()])
    start_date = DateField('Дата начала', validators=[Optional()])
    end_date = DateField('Дата окончания', validators=[DataRequired()])
    duration_hours = IntegerField('Продолжительность (часов)', validators=[Optional()])
    certificate_number = StringField('Номер сертификата / удостоверения', validators=[Optional(), Length(max=255)])
    certificate_url = URLField('Ссылка на сертификат', validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional(), Length(max=1000)])
    points = IntegerField('Очки рейтинга', default=6, validators=[Optional()])
    level = SelectField(
        'Уровень',
        choices=AWARD_LEVELS,
        validators=[Optional()]
    )
    state_issued = BooleanField('Государственного образца')
    owner_id = SelectField(
        'Автор записи',
        choices=[],
        validators=[Optional()],
    )
    submit = SubmitField('Сохранить')

class SearchFilterForm(FlaskForm):
    search_query = StringField('Поиск', validators=[Optional()])
    sort_by = SelectField('Сортировать по', choices=[
        ('date_desc', 'Новые сначала'),
        ('date_asc', 'Старые сначала'),
        ('title', 'По названию'),
    ], default='date_desc')
    date_range = SelectField('Период', choices=[
        ('all', 'За всё время'),
        ('3', 'За 3 месяца'),
        ('6', 'За полгода'),
        ('12', 'За год'),
        ('36', 'За 3 года'),
        ('60', 'За 5 лет'),
        ('academic_year', 'За учебный год'),
        ('custom', 'Выбрать период'),
    ], default='all')
    date_from = DateField('Дата от', validators=[Optional()])
    date_to = DateField('Дата до', validators=[Optional()])
    submit = SubmitField('Найти')
