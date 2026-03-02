from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, SubmitField, URLField
from wtforms.validators import DataRequired, Optional, Length, URL

award_levels = [
    ('university', 'вузовский'),
    ('regional', 'региональный'),
    ('faculty', 'факультетский'),
    ('federal', 'федеральный'),
    ('international', 'международный'),
    ]
    
class AwardForm(FlaskForm):
    title = StringField('Название награды', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('Описание', validators=[Optional(), Length(max=1000)])
    award_type = SelectField('Тип награды', choices=[
        ('certificate', 'Сертификат'),
        ('grant', 'Грант'),
        ('prize', 'Премия'),
        ('scholarship', 'Стипендия')
    ], validators=[DataRequired()])
    issuer = StringField('Выдавшая организация', validators=[Optional(), Length(max=255)])
    date_received = DateField('Дата получения', validators=[DataRequired()])
    points = IntegerField('Очки рейтинга', default=10, validators=[Optional()])
    level = SelectField(
        'Уровень награды',
        choices=award_levels,
        validators=[DataRequired(message='Выберите уровень награды')]
    )
    submit = SubmitField('Сохранить')

# Добавь в forms/rating.py:

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, SubmitField, URLField
from wtforms.validators import DataRequired, Optional, Length

PUBLICATION_TYPES = [
    ('book', 'Книга'),
    ('journal_article', 'Статья из журнала'),
    ('collection_article', 'Статья из сборника'),
    ('dissertation', 'Диссертация'),
    ('abstract', 'Автореферат'),
    ('internet', 'Интернет-ресурс'),
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

class PublicationForm(FlaskForm):
    # ====== ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ======
    publication_type = SelectField('Тип публикации', choices=PUBLICATION_TYPES, validators=[DataRequired()])
    title = StringField('Название', validators=[DataRequired(), Length(min=5, max=500)])
    year = IntegerField('Год', validators=[DataRequired()])
    points = IntegerField('Очки рейтинга', default=5, validators=[Optional()])
    
    # ====== КНИГА ======
    authors = StringField('Авторы (Фамилия И.О., через запятую)', validators=[Optional(), Length(max=500)])
    edition = StringField('Номер издания (например: 3-е)', validators=[Optional(), Length(max=50)])
    city = StringField('Город издания (М., СПб., или полностью)', validators=[Optional(), Length(max=100)])
    publisher = StringField('Издательство', validators=[Optional(), Length(max=255)])
    pages = StringField('Количество страниц', validators=[Optional(), Length(max=50)])
    
    # ====== ЖУРНАЛ ======
    journal_name = StringField('Название журнала', validators=[Optional(), Length(max=255)])
    issue = StringField('Номер выпуска (например: 10 или 2-3)', validators=[Optional(), Length(max=50)])
    
    # ====== СБОРНИК ======
    article_title = StringField('Название статьи (если отличается)', validators=[Optional(), Length(max=500)])
    collection_title = StringField('Название сборника', validators=[Optional(), Length(max=500)])
    
    # ====== ДИССЕРТАЦИЯ / АВТОРЕФЕРАТ ======
    author_single = StringField('Автор (Фамилия И.О.)', validators=[Optional(), Length(max=255)])
    degree = SelectField('Учёная степень', choices=DEGREES, validators=[Optional()])
    field = SelectField('Отрасль наук', choices=FIELDS_OF_STUDY, validators=[Optional()])
    specialty_code = StringField('Код специальности (например: 01.01.01)', validators=[Optional(), Length(max=20)])
    
    # ====== ИНТЕРНЕТ-РЕСУРС ======
    site_name = StringField('Название сайта', validators=[Optional(), Length(max=255)])
    url = URLField('Гиперссылка', validators=[Optional()])
    access_date = StringField('Дата обращения (ДД.ММ.ГГГГ)', validators=[Optional(), Length(max=20)])
    
    # ====== ПРОЧЕЕ ======
    doi = StringField('DOI', validators=[Optional(), Length(max=100)])
    
    journal_pages = StringField('Страницы статьи в журнале', validators=[Optional(), Length(max=50)])
    collection_pages = StringField('Страницы статьи в сборнике', validators=[Optional(), Length(max=50)])
    dissertation_pages = StringField('Количество страниц', validators=[Optional(), Length(max=50)])

    submit = SubmitField('Сохранить')


class ConferenceForm(FlaskForm):
    name = StringField('Название конференции', validators=[DataRequired(), Length(min=3, max=255)])
    role = SelectField('Роль', choices=[
        ('speaker', 'Докладчик'),
        ('participant', 'Участник'),
        ('organizer', 'Организатор')
    ], validators=[DataRequired()])
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
    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата окончания', validators=[Optional()])
    duration_hours = IntegerField('Продолжительность (часов)', validators=[Optional()])
    certificate_number = StringField('Номер сертификата', validators=[Optional(), Length(max=255)])
    certificate_url = URLField('Ссылка на сертификат', validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional(), Length(max=1000)])
    points = IntegerField('Очки рейтинга', default=6, validators=[Optional()])
    level = SelectField(
        'Уровень',
        choices=award_levels,  # можно переиспользовать тот же список
        validators=[Optional()]
    )
    submit = SubmitField('Сохранить')

class SearchFilterForm(FlaskForm):
    search_query = StringField('Поиск', validators=[Optional()])
    sort_by = SelectField('Сортировать по', choices=[
        ('date_desc', 'Новые сначала'),
        ('date_asc', 'Старые сначала'),
        ('title', 'По названию'),
        ('points', 'По рейтингу')
    ], default='date_desc')
    submit = SubmitField('Найти')
