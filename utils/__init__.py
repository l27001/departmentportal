from utils.email import send_email

# ГОСТ-функции, импортируются как from utils import generate_gost_string
from datetime import datetime


def format_authors(authors_str, max_count=3):
    if not authors_str:
        return ""
    authors_list = [a.strip() for a in authors_str.split(',')]
    if len(authors_list) <= max_count:
        return ', '.join(authors_list)
    return ', '.join(authors_list[:max_count]) + ' [и др.]'


def normalize_city(city_str):
    if not city_str:
        return ""
    cities_short = {
        'москва': 'М.',
        'санкт-петербург': 'СПб.',
        'спб': 'СПб.',
        'питер': 'СПб.',
        'ленинград': 'СПб.',
    }
    city_lower = city_str.lower().strip('.')
    return cities_short.get(city_lower, city_str)


def generate_gost_string(publication):
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
    return f"{publication.title}. – {publication.year}."


def generate_gost_book(pub):
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


def generate_gost_journal(pub):
    authors = pub.authors.strip() if pub.authors else ""
    title = pub.title if pub.title else ""
    journal = pub.journal_name if pub.journal_name else ""
    year = str(pub.year) if pub.year else ""
    issue = f"№ {pub.issue}" if pub.issue else ""
    pages = f"С. {pub.pages}" if pub.pages else ""
    parts = []
    if authors:
        parts.append(f"{authors}. {title}")
    else:
        parts.append(title)
    parts.append(f"// {journal}")
    parts.append(f"– {year}")
    if issue:
        parts.append(f"– {issue}")
    if pages:
        parts.append(f"– {pages}")
    result = ". ".join(parts) + "."
    result = result.replace(". –", " –")
    return result


def generate_gost_collection(pub):
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


def generate_gost_dissertation(pub):
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


def generate_gost_abstract(pub):
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


def generate_gost_internet(pub):
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
