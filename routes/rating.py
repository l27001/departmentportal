from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from extensions import db
from models.user import User
from models.award import Award, Publication, Conference, Training
from forms.rating import AwardForm, PublicationForm, ConferenceForm, TrainingForm, SearchFilterForm
from sqlalchemy import or_, desc
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment
from docx import Document
from flask import send_file
from utils import generate_gost_string
from flask import jsonify


rating_bp = Blueprint('rating', __name__, url_prefix='/rating')

# ==================== AWARDS ====================
@rating_bp.route('/awards')
@jwt_required()
def awards_list():
    """Список наград с поиском и фильтрами"""
    user_id = get_jwt_identity()  # Получаем ID текущего пользователя из JWT
    current_user = User.query.get_or_404(user_id)  # Получаем пользователя по ID
    search_form = SearchFilterForm()
    page = request.args.get('page', 1, type=int)
    
    query = Award.query.filter_by(user_id=current_user.id, status='active')
    
    # Поиск
    search_query = request.args.get('search_query', '')
    if search_query:
        query = query.filter(or_(
            Award.title.ilike(f'%{search_query}%'),
            Award.description.ilike(f'%{search_query}%')
        ))
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(desc(Award.date_received))
    elif sort_by == 'date_asc':
        query = query.order_by(Award.date_received)
    elif sort_by == 'title':
        query = query.order_by(Award.title)
    
    awards = query.paginate(page=page, per_page=10)
    
    return render_template('rating/awards.html', awards=awards, search_form=search_form)

@rating_bp.route('/awards/add', methods=['GET', 'POST'])
@jwt_required()
def add_award():
    """Добавление новой награды"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    form = AwardForm()
    if form.validate_on_submit():
        award = Award(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            award_type=form.award_type.data,
            issuer=form.issuer.data,
            date_received=form.date_received.data,
            level=form.level.data,
        )
        db.session.add(award)
        db.session.commit()
        flash('Награда добавлена!', 'success')
        return redirect(url_for('rating.awards_list'))
    
    return render_template('rating/award_form.html', form=form, title='Добавить награду')

@rating_bp.route('/awards/<int:award_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_award(award_id):
    """Редактирование награды"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    award = Award.query.get_or_404(award_id)
    if award.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.awards_list'))
    
    form = AwardForm()
    if form.validate_on_submit():
        award.title = form.title.data
        award.description = form.description.data
        award.award_type = form.award_type.data
        award.issuer = form.issuer.data
        award.date_received = form.date_received.data
        award.level = form.level.data
        db.session.commit()
        flash('Награда обновлена!', 'success')
        return redirect(url_for('rating.awards_list'))
    
    elif request.method == 'GET':
        form.title.data = award.title
        form.description.data = award.description
        form.award_type.data = award.award_type
        form.issuer.data = award.issuer
        form.date_received.data = award.date_received
        form.level.data = award.level
    
    return render_template('rating/award_form.html', form=form, title='Редактировать награду', award=award)

@rating_bp.route('/awards/<int:award_id>/delete', methods=['POST'])
@jwt_required()
def delete_award(award_id):
    """Удаление награды"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    award = Award.query.get_or_404(award_id)
    if award.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.awards_list'))
    
    db.session.delete(award)
    db.session.commit()
    flash('Награда удалена!', 'success')
    return redirect(url_for('rating.awards_list'))

# ==================== PUBLICATIONS ====================

@rating_bp.route('/publications')
@jwt_required()
def publications_list():
    """Список публикаций с поиском и фильтрами"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    search_form = SearchFilterForm()
    page = request.args.get('page', 1, type=int)
    
    # Базовый запрос только для текущего пользователя
    query = Publication.query.filter_by(user_id=current_user.id, status='active')
    
    # Поиск по названию или авторам
    search_query = request.args.get('search_query', '')
    if search_query:
        query = query.filter(or_(
            Publication.title.ilike(f'%{search_query}%'),
            Publication.authors.ilike(f'%{search_query}%'),
            Publication.article_title.ilike(f'%{search_query}%'),
            Publication.author_single.ilike(f'%{search_query}%')
        ))
    
    # Фильтр по типу публикации
    pub_type = request.args.get('pub_type', '')
    if pub_type:
        query = query.filter(Publication.publication_type == pub_type)
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(desc(Publication.year))  # ✅
    elif sort_by == 'date_asc':
        query = query.order_by(Publication.year)  # ✅
    elif sort_by == 'title':
        query = query.order_by(Publication.title)
    
    # Пагинация
    publications = query.paginate(page=page, per_page=10)
    
    
    return render_template(
        'rating/publications.html',
        publications=publications,
        search_form=search_form,
    )

@rating_bp.route('/publications/preview', methods=['POST'])
@jwt_required()
def preview_publication():
    """AJAX preview ГОСТ-строки при вводе формы"""
    data = request.get_json()
    
    try:
        temp_pub = Publication(
            publication_type=data.get('publication_type', ''),
            title=data.get('title', ''),
            year=int(data.get('year', datetime.now().year)) if data.get('year') else datetime.now().year,
            authors=data.get('authors', ''),
            edition=data.get('edition', ''),
            city=data.get('city', ''),
            publisher=data.get('publisher', ''),
            pages=data.get('pages', ''),
            journal_name=data.get('journal_name', ''),
            issue=data.get('issue', ''),
            article_title=data.get('article_title', ''),
            collection_title=data.get('collection_title', ''),
            author_single=data.get('author_single', ''),
            degree=data.get('degree', ''),
            field=data.get('field', ''),
            specialty_code=data.get('specialty_code', ''),
            site_name=data.get('site_name', ''),
            url=data.get('url', ''),
            access_date=data.get('access_date', ''),
        )
        
        gost_string = generate_gost_string(temp_pub)
        return jsonify({'gost_string': gost_string})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@rating_bp.route('/publications/add', methods=['GET', 'POST'])
@jwt_required()
def add_publication():
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    form = PublicationForm()
    if form.validate_on_submit():
        publication = Publication(
            user_id=current_user.id,
            publication_type=form.publication_type.data,
            title=form.title.data,
            year=form.year.data,
            authors=form.authors.data,
            edition=form.edition.data,
            city=form.city.data,
            publisher=form.publisher.data,
            
            pages=form.journal_pages.data if form.publication_type.data == 'journal_article' else (form.collection_pages.data if form.publication_type.data == 'collection_article' else form.pages.data),


            journal_name=form.journal_name.data,
            issue=form.issue.data,
            article_title=form.article_title.data,
            collection_title=form.collection_title.data,
            author_single=form.author_single.data,
            degree=form.degree.data,
            field=form.field.data,
            specialty_code=form.specialty_code.data,
            site_name=form.site_name.data,
            url=form.url.data,
            access_date=form.access_date.data,
            doi=form.doi.data,
            status='active'
        )
        # ГЕНЕРИРУЕМ ГОСТ-СТРОКУ
        publication.gost_string = generate_gost_string(publication)
        db.session.add(publication)
        db.session.commit()
        flash('Публикация добавлена!', 'success')
        return redirect(url_for('rating.publications_list'))
    
    return render_template('rating/publication_form.html', form=form, title='Добавить публикацию')


@rating_bp.route('/publications/<int:pub_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_publication(pub_id):
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    publication = Publication.query.get_or_404(pub_id)
    if publication.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.publications_list'))
    
    form = PublicationForm()
    if form.validate_on_submit():
        publication.publication_type = form.publication_type.data
        publication.title = form.title.data
        publication.year = form.year.data
        publication.authors = form.authors.data
        publication.edition = form.edition.data
        publication.city = form.city.data
        publication.publisher = form.publisher.data
        if form.publication_type.data == 'journal_article':
            publication.pages=form.journal_pages.data
        else:
            publication.pages = (form.collection_pages.data if form.publication_type.data == 'collection_article' else form.pages.data)


        publication.journal_name = form.journal_name.data
        publication.issue = form.issue.data
        publication.article_title = form.article_title.data
        publication.collection_title = form.collection_title.data
        publication.author_single = form.author_single.data
        publication.degree = form.degree.data
        publication.field = form.field.data
        publication.specialty_code = form.specialty_code.data
        publication.site_name = form.site_name.data
        publication.url = form.url.data
        publication.access_date = form.access_date.data
        publication.doi = form.doi.data
        
        # ПЕРЕСЧИТЫВАЕМ ГОСТ-СТРОКУ
        publication.gost_string = generate_gost_string(publication)
        db.session.commit()
        flash('Публикация обновлена!', 'success')
        return redirect(url_for('rating.publications_list'))
    
    elif request.method == 'GET':
        form.publication_type.data = publication.publication_type
        form.title.data = publication.title
        form.year.data = publication.year
        form.authors.data = publication.authors
        form.edition.data = publication.edition
        form.city.data = publication.city
        form.publisher.data = publication.publisher
        form.pages.data = publication.pages
        form.journal_name.data = publication.journal_name
        form.issue.data = publication.issue
        form.article_title.data = publication.article_title
        form.collection_title.data = publication.collection_title
        form.author_single.data = publication.author_single
        form.degree.data = publication.degree
        form.field.data = publication.field
        form.specialty_code.data = publication.specialty_code
        form.site_name.data = publication.site_name
        form.url.data = publication.url
        form.access_date.data = publication.access_date
        form.doi.data = publication.doi

    
    return render_template('rating/publication_form.html', form=form, title='Редактировать публикацию', publication=publication)


@rating_bp.route('/publications/<int:pub_id>', methods=['GET'])
@jwt_required()
def view_publication(pub_id):
    """Просмотр полной информации о публикации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    publication = Publication.query.get_or_404(pub_id)
    if publication.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.publications_list'))
    
    return render_template('rating/publication_view.html', publication=publication)


@rating_bp.route('/publications/<int:pub_id>/delete', methods=['POST'])
@jwt_required()
def delete_publication(pub_id):
    """Удаление публикации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    publication = Publication.query.get_or_404(pub_id)
    if publication.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.publications_list'))
    
    db.session.delete(publication)
    db.session.commit()
    flash('Публикация удалена!', 'success')
    return redirect(url_for('rating.publications_list'))


# ==================== CONFERENCES ====================

@rating_bp.route('/conferences')
@jwt_required()
def conferences_list():
    """Список конференций"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    search_form = SearchFilterForm()
    page = request.args.get('page', 1, type=int)
    
    query = Conference.query.filter_by(user_id=current_user.id, status='active')
    
    search_query = request.args.get('search_query', '')
    if search_query:
        query = query.filter(or_(
            Conference.name.ilike(f'%{search_query}%'),
            Conference.paper_title.ilike(f'%{search_query}%')
        ))
    
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(desc(Conference.conference_date))
    elif sort_by == 'date_asc':
        query = query.order_by(Conference.conference_date)
    elif sort_by == 'title':
        query = query.order_by(Conference.name)
    
    conferences = query.paginate(page=page, per_page=10)
    
    return render_template('rating/conferences.html', conferences=conferences, search_form=search_form)

@rating_bp.route('/conferences/add', methods=['GET', 'POST'])
@jwt_required()
def add_conference():
    """Добавление конференции"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    form = ConferenceForm()
    if form.validate_on_submit():
        conference = Conference(
            user_id=current_user.id,
            name=form.name.data,
            role=form.role.data,
            paper_title=form.paper_title.data,
            conference_date=form.conference_date.data,
            location=form.location.data,
            conference_url=form.conference_url.data,
            description=form.description.data,
            coauthors=form.coauthors.data
        )
        db.session.add(conference)
        db.session.commit()
        flash('Конференция добавлена!', 'success')
        return redirect(url_for('rating.conferences_list'))
    
    return render_template('rating/conference_form.html', form=form, title='Добавить конференцию')

@rating_bp.route('/conferences/<int:conf_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_conference(conf_id):
    """Редактирование конференции"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    conference = Conference.query.get_or_404(conf_id)
    if conference.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.conferences_list'))
    
    form = ConferenceForm()
    if form.validate_on_submit():
        conference.name = form.name.data
        conference.role = form.role.data
        conference.paper_title = form.paper_title.data
        conference.conference_date = form.conference_date.data
        conference.location = form.location.data
        conference.conference_url = form.conference_url.data
        conference.description = form.description.data
        conference.coauthors=form.coauthors.data
        db.session.commit()
        flash('Конференция обновлена!', 'success')
        return redirect(url_for('rating.conferences_list'))
    
    elif request.method == 'GET':
        form.name.data = conference.name
        form.role.data = conference.role
        form.paper_title.data = conference.paper_title
        form.conference_date.data = conference.conference_date
        form.location.data = conference.location
        form.conference_url.data = conference.conference_url
        form.description.data = conference.description
        form.coauthors.data=conference.coauthors
    
    return render_template('rating/conference_form.html', form=form, title='Редактировать конференцию', conference=conference)

@rating_bp.route('/conferences/<int:conf_id>/delete', methods=['POST'])
@jwt_required()
def delete_conference(conf_id):
    """Удаление конференции"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    conference = Conference.query.get_or_404(conf_id)
    if conference.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.conferences_list'))
    
    db.session.delete(conference)
    db.session.commit()
    flash('Конференция удалена!', 'success')
    return redirect(url_for('rating.conferences_list'))


# ==================== TRAININGS ====================

@rating_bp.route('/trainings')
@jwt_required()
def trainings_list():
    """Список повышений квалификации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    search_form = SearchFilterForm()
    page = request.args.get('page', 1, type=int)
    
    query = Training.query.filter_by(user_id=current_user.id, status='active')
    
    search_query = request.args.get('search_query', '')
    if search_query:
        query = query.filter(or_(
            Training.title.ilike(f'%{search_query}%'),
            Training.organization.ilike(f'%{search_query}%')
        ))
    
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_desc':
        query = query.order_by(desc(Training.start_date))
    elif sort_by == 'date_asc':
        query = query.order_by(Training.start_date)
    elif sort_by == 'title':
        query = query.order_by(Training.title)
    
    trainings = query.paginate(page=page, per_page=10)
    
    return render_template('rating/trainings.html', trainings=trainings, search_form=search_form)

@rating_bp.route('/trainings/add', methods=['GET', 'POST'])
@jwt_required()
def add_training():
    """Добавление повышения квалификации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    form = TrainingForm()
    if form.validate_on_submit():
        training = Training(
            user_id=current_user.id,
            title=form.title.data,
            organization=form.organization.data,
            city=form.city.data,
            training_type=form.training_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            duration_hours=form.duration_hours.data,
            certificate_number=form.certificate_number.data,
            certificate_url=form.certificate_url.data,
            description=form.description.data,
            level=form.level.data
        )
        db.session.add(training)
        db.session.commit()
        flash('Повышение квалификации добавлено!', 'success')
        return redirect(url_for('rating.trainings_list'))
    
    return render_template('rating/training_form.html', form=form, title='Добавить повышение квалификации')

@rating_bp.route('/trainings/<int:training_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_training(training_id):
    """Редактирование повышения квалификации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    training = Training.query.get_or_404(training_id)
    if training.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.trainings_list'))
    
    form = TrainingForm()
    if form.validate_on_submit():
        training.title = form.title.data
        training.organization = form.organization.data
        training.city = form.city.data
        training.training_type = form.training_type.data
        training.start_date = form.start_date.data
        training.end_date = form.end_date.data
        training.duration_hours = form.duration_hours.data
        training.certificate_number = form.certificate_number.data
        training.certificate_url = form.certificate_url.data
        training.description = form.description.data
        training.level = form.level.data
        db.session.commit()
        flash('Повышение квалификации обновлено!', 'success')
        return redirect(url_for('rating.trainings_list'))
    
    elif request.method == 'GET':
        form.title.data = training.title
        form.organization.data = training.organization
        form.city.data = training.city
        form.training_type.data = training.training_type
        form.start_date.data = training.start_date
        form.end_date.data = training.end_date
        form.duration_hours.data = training.duration_hours
        form.certificate_number.data = training.certificate_number
        form.certificate_url.data = training.certificate_url
        form.description.data = training.description
        form.level.data = training.level
    
    return render_template('rating/training_form.html', form=form, title='Редактировать повышение квалификации', training=training)

@rating_bp.route('/trainings/<int:training_id>/delete', methods=['POST'])
@jwt_required()
def delete_training(training_id):
    """Удаление повышения квалификации"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    training = Training.query.get_or_404(training_id)
    if training.user_id != current_user.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('rating.trainings_list'))
    
    db.session.delete(training)
    db.session.commit()
    flash('Повышение квалификации удалено!', 'success')
    return redirect(url_for('rating.trainings_list'))

"""Экспорт в Excel"""

@rating_bp.route('/awards/export/excel')
@jwt_required()
def export_awards_excel():
    """Экспорт наград в Excel"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    awards = Award.query.filter_by(user_id=current_user.id, status='active').all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Награды"
    
    headers = ["ID", "Название", "Тип", "Организация", "Дата получения", "Уровень"]
    ws.append(headers)
    
    header_fill = PatternFill(start_color="007BFF", end_color="007BFF", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for award in awards:
        ws.append([
            award.id,
            award.title,
            award.award_type,
            award.issuer or "",
            award.date_received.strftime("%d.%m.%Y"),
            award.level or ""
        ])
    
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 10
    
    bytes_stream = BytesIO()
    wb.save(bytes_stream)
    bytes_stream.seek(0)
    
    return send_file(
        bytes_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"awards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )


@rating_bp.route('/publications/export/excel', methods=['GET'])
@jwt_required()
def export_publications_excel():
    """Export publications to Excel - simple list with links"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    publications = Publication.query.filter_by(user_id=current_user.id, status='active').all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = 'Публикации'
    
    # Заголовки
    headers = ['№', 'Название', 'ГОСТ-строка','Тип']
    ws.append(headers)
    
    # Стиль заголовка
    header_fill = PatternFill(start_color='28A745', end_color='28A745', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Данные
    for idx, pub in enumerate(publications, 1):
        gost = pub.gost_string or pub.title or ''
        ws.append([
            idx,
            pub.title or '',
            gost,
            pub.publication_type or '',
        ])
    
    # Ширина колонок
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 15

    
    # Сохранение
    bytes_stream = BytesIO()
    wb.save(bytes_stream)
    bytes_stream.seek(0)
    
    return send_file(
        bytes_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'publications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@rating_bp.route('/conferences/export/excel')
@jwt_required()
def export_conferences_excel():
    """Экспорт конференций в Excel"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    conferences = Conference.query.filter_by(user_id=current_user.id, status='active').all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Конференции"
    
    headers = ["ID", "Название", "Роль", "Доклад", "Дата", "Место", "Соавторы"]
    ws.append(headers)
    
    header_fill = PatternFill(start_color="FFC107", end_color="FFC107", fill_type="solid")
    header_font = Font(bold=True, color="000000")
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for conf in conferences:
        ws.append([
            conf.id,
            conf.name,
            conf.role,
            conf.paper_title or "",
            conf.conference_date.strftime("%d.%m.%Y"),
            conf.location or "",
            conf.coauthors or ""
        ])
    
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 30
    
    bytes_stream = BytesIO()
    wb.save(bytes_stream)
    bytes_stream.seek(0)
    
    return send_file(
        bytes_stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"conferences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )


# ==================== ЭКСПОРТ В WORD ====================

@rating_bp.route('/awards/export/word')
@jwt_required()
def export_awards_word():
    """Экспорт наград в Word"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    awards = Award.query.filter_by(user_id=current_user.id, status='active').all()
    
    doc = Document()
    
    title = doc.add_heading('Отчет о наградах', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    date_para = doc.add_paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    date_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    doc.add_heading('Общая информация', level=2)
    info_table = doc.add_table(rows=1, cols=2)
    info_table.style = 'Light Grid Accent 1'
    
    info_table.rows[0].cells[0].text = 'Всего наград:'
    info_table.rows[0].cells[1].text = str(len(awards))

    doc.add_paragraph()
    
    doc.add_heading('Список наград', level=2)
    
    awards_table = doc.add_table(rows=1, cols=5)
    awards_table.style = 'Light Grid Accent 1'
    
    header_cells = awards_table.rows[0].cells
    header_cells[0].text = 'Название'
    header_cells[1].text = 'Тип'
    header_cells[2].text = 'Организация'
    header_cells[3].text = 'Дата'
    header_cells[4].text = 'Уровень'
    
    for award in awards:
        row_cells = awards_table.add_row().cells
        row_cells[0].text = award.title
        row_cells[1].text = award.award_type
        row_cells[2].text = award.issuer or '-'
        row_cells[3].text = award.date_received.strftime("%d.%m.%Y")
        row_cells[4].text = award.level or ''
    
    bytes_stream = BytesIO()
    doc.save(bytes_stream)
    bytes_stream.seek(0)
    
    return send_file(
        bytes_stream,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f"awards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    )




@rating_bp.route('/publications/export/word', methods=['GET'])
@jwt_required()
def export_publications_word():
    """Export publications to Word - simple list with links"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    publications = Publication.query.filter_by(user_id=current_user.id, status='active').all()
    
    doc = Document()
    
    # Заголовок
    title = doc.add_heading('Публикации', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Дата
    date_para = doc.add_paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    date_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    doc.add_paragraph()
    
    # Таблица
    if publications:
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light Grid Accent 1'
        
        # Заголовки
        header_cells = table.rows[0].cells
        header_cells[0].text = '№'
        header_cells[1].text = 'Название'
        header_cells[2].text = 'ГОСТ-строка'
        header_cells[3].text = 'Год'
        
        # Данные
        for idx, pub in enumerate(publications, 1):
            row_cells = table.add_row().cells
            row_cells[0].text = str(idx)
            
            # Название с ссылкой (если есть URL)
            if pub.url:
                para = row_cells[1].paragraphs[0]
                run = para.add_run(pub.title or 'Публикация')
                # run.font.color.rgb = RGBColor(0, 0, 255)
                run.font.underline = True
                # Добавляем ссылку в скобках
                para.add_run(f' ({pub.url})')
            else:
                row_cells[1].text = pub.title or ''
            
            # ГОСТ-строка
            row_cells[2].text = pub.gost_string or pub.title or ''
            
            # Год
            row_cells[3].text = str(pub.year) if pub.year else ''
    else:
        doc.add_paragraph('Публикаций не найдено.')
    
    # Сохранение
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f'publications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
    )



@rating_bp.route('/conferences/export/word')
@jwt_required()
def export_conferences_word():
    """Экспорт конференций в Word"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    conferences = Conference.query.filter_by(user_id=current_user.id, status='active').all()
    
    doc = Document()
    
    title = doc.add_heading('Отчет о конференциях', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    date_para = doc.add_paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    date_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    doc.add_heading('Общая информация', level=2)
    info_table = doc.add_table(rows=1, cols=2)
    info_table.style = 'Light Grid Accent 1'
    
    info_table.rows[0].cells[0].text = 'Всего конференций:'
    info_table.rows[0].cells[1].text = str(len(conferences))
    
    doc.add_paragraph()
    
    doc.add_heading('Список конференций', level=2)
    
    conf_table = doc.add_table(rows=1, cols=5)
    conf_table.style = 'Light Grid Accent 1'
    
    header_cells = conf_table.rows[0].cells
    header_cells[0].text = 'Название'
    header_cells[1].text = 'Роль'
    header_cells[2].text = 'Доклад'
    header_cells[3].text = 'Дата'
    header_cells[4].text = 'Соавторы'
    
    for conf in conferences:
        row_cells = conf_table.add_row().cells
        row_cells[0].text = conf.name
        row_cells[1].text = conf.role
        row_cells[2].text = conf.paper_title or '-'
        row_cells[3].text = conf.conference_date.strftime("%d.%m.%Y")
        row_cells[4].text = conf.coauthors or '-'
    
    bytes_stream = BytesIO()
    doc.save(bytes_stream)
    bytes_stream.seek(0)
    
    return send_file(
        bytes_stream,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f"conferences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    )


# ==================== ЭКСПОРТ ПОВЫШЕНИЙ КВАЛИФИКАЦИЙ ====================

# В app/routes/rating.py найдите функцию export_qualifications_excel и замените полностью:

@rating_bp.route('/qualifications/export/excel', methods=['GET'])
@jwt_required()
def export_qualifications_excel():
    """Экспорт тренингов в Excel"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    trainings = Training.query.filter_by(user_id=current_user.id, status='active').all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Тренинги"
    
    # Заголовки
    headers = ['Дата начала', 'Дата окончания', 'Название курса', 'Организатор', 'Город', "Уровень", 'Часы', 'Номер сертификата']
    ws.append(headers)
    
    # Данные
    for training in trainings:
        ws.append([
            training.start_date.strftime('%d.%m.%Y') if training.start_date else '',
            training.end_date.strftime('%d.%m.%Y') if training.end_date else '',
            training.title or '',
            training.organization or '',
            training.city or '',
            training.level or '',
            training.duration_hours or 0,
            training.certificate_number or ''
        ])
    
    # Форматирование
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 20

    
    # Отправка
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'trainings_{current_user.id}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


@rating_bp.route('/qualifications/export/word', methods=['GET'])
@jwt_required()
def export_qualifications_word():
    """Экспорт тренингов в Word"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    trainings = Training.query.filter_by(user_id=current_user.id, status='active').all()
    
    doc = Document()
    doc.add_heading('Тренинги и повышение квалификации', 0)
    
    if not trainings:
        doc.add_paragraph('Нет данных для экспорта.')
    else:
        table = doc.add_table(rows=1, cols=8)
        table.style = 'Light Grid Accent 1'
        
        # Заголовки
        header_cells = table.rows[0].cells
        headers = ['Дата начала', 'Дата окончания', 'Название курса', 'Организатор', 'Город', "Уровень", 'Часы', 'Сертификат']
        for i, header in enumerate(headers):
            header_cells[i].text = header
        
        # Данные
        for training in trainings:
            row_cells = table.add_row().cells
            row_cells[0].text = training.start_date.strftime('%d.%m.%Y') if training.start_date else ''
            row_cells[1].text = training.end_date.strftime('%d.%m.%Y') if training.end_date else ''
            row_cells[2].text = training.title or ''
            row_cells[3].text = training.organization or ''
            row_cells[4].text = training.city or ''
            row_cells[5].text = training.level or ''
            row_cells[6].text = str(training.duration_hours) if training.duration_hours else '0'
            row_cells[7].text = training.certificate_number or ''
    
    # Отправка
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f'trainings_{current_user.id}_{datetime.now().strftime("%Y%m%d")}.docx'
    )
