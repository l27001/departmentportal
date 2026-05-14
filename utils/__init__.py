from datetime import datetime

def format_authors(authors_str, max_count=3):
    if not authors_str:
        return ""
    authors_list = [a.strip() for a in authors_str.split(',')]
    if len(authors_list) <= max_count:
        return ', '.join(authors_list)
    else:
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
    short = cities_short.get(city_lower, city_str)
    return short

def generate_gost_string(pub):
    pub_type = pub.__tablename__
    if pub_type == 'publication_books':
        return generate_gost_book(pub)
    elif pub_type == 'publication_journal_articles':
        return generate_gost_journal(pub)
    elif pub_type == 'publication_collection_articles':
        return generate_gost_collection(pub)
    elif pub_type == 'publication_dissertations':
        return generate_gost_dissertation(pub)
    elif pub_type == 'publication_abstracts':
        return generate_gost_abstract(pub)
    elif pub_type == 'publication_internets':
        return generate_gost_internet(pub)
    else:
        return f"{pub.title}. \u2013 {pub.year}."

def generate_gost_book(pub):
    authors = format_authors(pub.authors) if pub.authors else ""
    title = pub.title or ""
    edition = f"{pub.edition} \u0438\u0437\u0434. \u2013 " if pub.edition else ""
    city = normalize_city(pub.city) if pub.city else ""
    publisher = pub.publisher or ""
    year = pub.year or ""
    pages = f"{pub.pages} \u0441." if pub.pages else ""
    result = f"{authors}. {title}" if authors else title
    result += f". \u2013 {edition}" if edition else ". \u2013 "
    result += f"{city} : {publisher}, {year}"
    if pages:
        result += f". \u2013 {pages}"
    return result.replace('. \u2013 .', '.')

def generate_gost_journal(pub):
    authors = format_authors(pub.authors) if pub.authors else ""
    title = pub.title or ""
    journal = pub.journal_name or ""
    year = str(pub.year) if pub.year else ""
    issue = f"\u2116{pub.issue}" if pub.issue else ""
    pages = f"\u0421. {pub.pages}" if pub.pages else ""
    parts = []
    if authors:
        parts.append(f"{authors} {title}")
    else:
        parts.append(title)
    parts.append(f"// {journal}")
    if year:
        parts.append(f"\u2013 {year}")
    if issue:
        parts.append(f"\u2013 {issue}")
    if pages:
        parts.append(f"\u2013 {pages}")
    result = ". ".join(parts) + "."
    result = result.replace(". \u2013", " \u2013")
    return result

def generate_gost_collection(pub):
    authors = format_authors(pub.authors) if pub.authors else ""
    title = pub.title or ""
    collection = pub.collection_title or ""
    city = normalize_city(pub.city) if pub.city else ""
    publisher = pub.publisher or ""
    year = pub.year or ""
    pages = f"\u0421. {pub.pages}" if pub.pages else ""
    result = f"{authors} {title}" if authors else title
    result += f" // {collection}. \u2013 {city}: {publisher}, {year}."
    if pages:
        result += f" \u2013 {pages}."
    return result.replace(".. \u2013", ".").replace(". \u2013", " \u2013").replace(" \u2013 .", ".")

def generate_gost_dissertation(pub):
    author = pub.author_single or ""
    title = pub.title or ""
    degree = pub.degree or ""
    field = pub.field or ""
    spec_code = pub.specialty_code or ""
    city = normalize_city(pub.city) if pub.city else ""
    year = pub.year or ""
    pages = f"{pub.pages} \u0441." if pub.pages else ""
    result = f"{author} {title}: \u0434\u0438\u0441. {degree} {field} \u043d\u0430\u0443\u043a: {spec_code}. \u2013 {city}, {year}."
    if pages:
        result += f" \u2013 {pages}"
    return result.replace(".. \u2013", ".").replace(" \u2013 .", ".")

def generate_gost_abstract(pub):
    author = pub.author_single or ""
    title = pub.title or ""
    degree = pub.degree or ""
    field = pub.field or ""
    spec_code = pub.specialty_code or ""
    city = normalize_city(pub.city) if pub.city else ""
    year = pub.year or ""
    pages = f"{pub.pages} \u0441." if pub.pages else ""
    result = f"{author} {title}: \u0430\u0432\u0442\u043e\u0440\u0435\u0444. \u0434\u0438\u0441. {degree} {field} \u043d\u0430\u0443\u043a: {spec_code}. \u2013 {city}, {year}."
    if pages:
        result += f" \u2013 {pages}"
    return result.replace(".. \u2013", ".").replace(" \u2013 .", ".")

def generate_gost_internet(pub):
    title = pub.title or ""
    site = pub.site_name or ""
    url = pub.url or ""
    access_date = pub.access_date or ""
    result = f"{title} // {site}" if site else title
    if url:
        result += f" URL: {url}"
    if access_date:
        result += f" (\u0434\u0430\u0442\u0430 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f: {access_date})."
    elif url:
        result += "."
    return result


