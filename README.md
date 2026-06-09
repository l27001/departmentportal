# Информационная система «Кафедра ВУЗа»

Внутренний портал для управления деятельностью кафедры университета.

## Возможности

- **Таск-менеджер** — задачи с приоритетами, дедлайнами, файлами, комментариями и статусами
- **Документы** — загрузка и каталогизация документов и внешних ссылок
- **Новости** — публикация новостей с закреплением и изображениями
- **Анонсы** — с дедлайнами, RSVP и отслеживанием просмотров
- **Заседания** — планирование, привязка задач, уведомления по email
- **Чат** — общий чат кафедры с вложениями
- **Рейтинг сотрудников** — портфолио: награды, публикации, конференции, повышения квалификации
- **О кафедре** — галерея, список сотрудников, фотографии

## Стек

- Python 3 + Flask + SQLAlchemy + PostgreSQL
- JWT-аутентификация (Flask-JWT-Extended)
- Jinja2-шаблоны, WTForms, Swagger (Flasgger)
- Docker, Gunicorn

## Развёртывание

### Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: portal
      POSTGRES_PASSWORD: password
      POSTGRES_DB: portal
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    image: ghcr.io/l27001/departmentportal:latest
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://portal:password@db:5432/portal
      JWT_SECRET_KEY: change-me
      SECRET_KEY: change-me-too
      FLASK_ENV: production
    depends_on:
      - db
    volumes:
      - uploads:/app/uploads

volumes:
  pgdata:
  uploads:
```

```bash
docker compose up -d
```

### Вручную

```bash
pip install -r requirements.txt
flask db upgrade
flask run
```
