# app/utils.py
from datetime import datetime

def format_authors(authors_str, max_count=3):
    """Форматирует список авторов по ГОСТ (макс 3, потом [и др.])"""
    if not authors_str:
        return ""
    
    authors_list = [a.strip() for a in authors_str.split(',')]
    
    if len(authors_list) <= max_count:
        return ', '.join(authors_list)
    else:
        return ', '.join(authors_list[:max_count]) + ' [и др.]'

def normalize_city(city_str):
    """Преобразует город в ГОСТ-формат"""
    if not city_str:
        return ""
    
    cities_short = {
        'москва': 'М.',
        'москва': 'М.',
        'санкт-петербург': 'СПб.',
        'спб': 'СПб.',
        'питер': 'СПб.',
        'ленинград': 'СПб.',
    }
    
    city_lower = city_str.lower().strip('.')
    short = cities_short.get(city_lower, city_str)
    
    return short

def generate_gost_string(publication):
    """
    Генерирует ГОСТ-строку на основе типа публикации
    ГОСТ Р 7.0.5-2008
    """
    
    pub_type = publication.publication_type.lower()
    
    if pub_type == 'book':
        return generate_gost_book(publication)
    elif pub_type == 'journal_article':
        return generate_gost_journal(publication)
    elif pub_type == 'collection_article':
        return generate_gost_collection(publication)
    elif pub_type == 'dissertation':
        return generate_gost_dissertation(publication)
    elif pub_type == 'abstract':
        return generate_gost_abstract(publication)
    elif pub_type == 'internet':
        return generate_gost_internet(publication)
    else:
        return f"{publication.title}. – {publication.year}."

# ========== КНИГА ==========
def generate_gost_book(pub):
    """
    Иванов И.М., Петров С.Н. Наука как искусство. – 3-е изд. – М. : Просвещение, 2020. – 999 с.
    """
    authors = format_authors(pub.authors) if pub.authors else ""
    title = pub.title or ""
    edition = f"{pub.edition} изд. – " if pub.edition else ""
    city = normalize_city(pub.city) if pub.city else ""
    publisher = pub.publisher or ""
    year = pub.year or ""
    pages = f"{pub.pages} с." if pub.pages else ""
    
    result = f"{authors}. {title}" if authors else title
    result += f". – {edition}" if edition else ". – "
    result += f"{city} : {publisher}, {year}"
    if pages:
        result += f". – {pages}"
    result += "."
    
    return result.replace('. – .', '.')

# ========== СТАТЬЯ ИЗ ЖУРНАЛА ==========
def generate_gost_journal(pub):
    print(f"DEBUG generate_gost_journal called:")
    print(f"  authors: {pub.authors}")
    print(f"  title: {pub.title}")
    print(f"  journal_name: {pub.journal_name}")
    print(f"  year: {pub.year}")
    print(f"  issue: {pub.issue}")
    print(f"  pages: {pub.pages}")
    """
    Статья из журнала по ГОСТ
    Формат: Авторы. Название // Журнал. – Год. – № Выпуск. – С. Страницы.
    Пример: Иванов И.М. Статья // Наука. – 2026. – № 5. – С. 10-20.
    """
    # Авторы
    if pub.authors:
        authors = pub.authors.strip()
    else:
        authors = ""
    
    # Название
    title = pub.title if pub.title else ""
    
    # Журнал
    journal = pub.journal_name if pub.journal_name else ""
    
    # Год
    year = str(pub.year) if pub.year else ""
    
    # Номер выпуска
    if pub.issue:
        issue = f"№ {pub.issue}"
    else:
        issue = ""
    
    # Страницы
    if pub.pages:
        pages = f"С. {pub.pages}"
    else:
        pages = ""
    
    # СОБИРАЕМ СТРОКУ
    parts = []
    
    # Авторы и название
    if authors:
        parts.append(f"{authors}. {title}")
    else:
        parts.append(title)
    
    # Журнал
    parts.append(f"// {journal}")
    
    # Год
    parts.append(f"– {year}")
    
    # Номер
    if issue:
        parts.append(f"– {issue}")
    
    # Страницы
    if pages:
        parts.append(f"– {pages}")
    
    # Объединяем с точками
    result = ". ".join(parts) + "."
    
    # Заменяем ". –" на " –"
    result = result.replace(". –", " –")
    
    return result



# ========== СТАТЬЯ ИЗ СБОРНИКА ==========
def generate_gost_collection(pub):
    """
    Иванов И.М., Петров С.Н. Наука как искусство // Сборник научных трудов. – М. : АСТ, 2020. – С. 25-30.
    """
    authors = format_authors(pub.authors) if pub.authors else ""
    article_title = pub.article_title or pub.title or ""
    collection = pub.collection_title or ""
    city = normalize_city(pub.city) if pub.city else ""
    publisher = pub.publisher or ""
    year = pub.year or ""
    pages = f"С. {pub.pages}" if pub.pages else ""
    
    result = f"{authors}. {article_title}" if authors else article_title
    result += f" // {collection}. – {city} : {publisher}, {year}."
    if pages:
        result += f" – {pages}."
    
    return result.replace(".. –", ".").replace(". –", " –").replace(" – .", ".")

# ========== ДИССЕРТАЦИЯ ==========
def generate_gost_dissertation(pub):
    """
    Иванов И.М. Наука как искусство : дис. ... д-р. экон. наук : 01.01.01. – М., 2020. – 199 с.
    """
    author = pub.author_single or ""
    title = pub.title or ""
    degree = pub.degree or "д-р."
    field = pub.field or "наук"
    spec_code = pub.specialty_code or ""
    city = normalize_city(pub.city) if pub.city else ""
    year = pub.year or ""
    pages = f"{pub.pages} с." if pub.pages else ""
    
    result = f"{author}. {title} : дис. ... {degree}. {field} наук : {spec_code}. – {city}, {year}."
    if pages:
        result += f" – {pages}."
    
    return result.replace(".. –", ".").replace(" – .", ".")

# ========== АВТОРЕФЕРАТ ==========
def generate_gost_abstract(pub):
    """
    Иванов И.М. Наука как искусство : автореф. дис. ... канд. экон. наук : 01.01.01. – М., 2020. – 99 с.
    """
    author = pub.author_single or ""
    title = pub.title or ""
    degree = pub.degree or "канд."
    field = pub.field or "наук"
    spec_code = pub.specialty_code or ""
    city = normalize_city(pub.city) if pub.city else ""
    year = pub.year or ""
    pages = f"{pub.pages} с." if pub.pages else ""
    
    result = f"{author}. {title} : автореф. дис. ... {degree}. {field} наук : {spec_code}. – {city}, {year}."
    if pages:
        result += f" – {pages}."
    
    return result.replace(".. –", ".").replace(" – .", ".")

# ========== ИНТЕРНЕТ-РЕСУРС ==========
def generate_gost_internet(pub):
    """
    Иванов И.М. Наука как искусство : статья // Ведомости : веб-сайт. – URL: https://... (дата обращения: 01.01.2021).
    """
    authors = format_authors(pub.authors) if pub.authors else ""
    title = pub.title or ""
    site = pub.site_name or ""
    url = pub.url or ""
    access_date = pub.access_date or ""
    
    result = f"{authors}. {title}" if authors else title
    result += f" : статья // {site} : веб-сайт." if site else " : электронный ресурс."
    if url:
        result += f" – URL: {url}"
    if access_date:
        result += f" (дата обращения: {access_date})."
    elif url:
        result += "."
    
    return result.strip()
