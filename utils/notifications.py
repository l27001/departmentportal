import os
from models.user import User
from utils.email import send_email


def _is_dev_allowed(email):
    if os.getenv("FLASK_ENV") != "development":
        return True
    return email.endswith("@ezdomain.ru")


def notify_meeting_created(meeting, base_url):
    meeting_url = f"{base_url}meetings/{meeting.id}"
    subject = f"Новое заседание кафедры: {meeting.title}"
    date_str = meeting.date.strftime("%d.%m.%Y") if meeting.date else "—"
    desc_html = f"<p>{meeting.description}</p>" if meeting.description else ""

    user_tasks_map = {}
    for t in meeting.tasks:
        for a in t.assignments:
            user_tasks_map.setdefault(a.user_id, []).append(t)

    users = User.query.filter(User.dismissal_date.is_(None)).all()
    for user in users:
        if not user.email:
            continue
        if not _is_dev_allowed(user.email):
            continue

        user_tasks = user_tasks_map.get(user.id, [])
        tasks_html = ""
        if user_tasks:
            task_lines = "".join(
                f'<li>{t.title} (срок: {t.deadline_at.strftime("%d.%m.%Y")})</li>'
                for t in user_tasks
            )
            tasks_html = f"<p><strong>Ваши задачи в заседании:</strong></p><ul>{task_lines}</ul>"

        body_html = f"""\
<h2>Новое заседание кафедры</h2>
<h3>{meeting.title}</h3>
<p><strong>Дата:</strong> {date_str}</p>
{desc_html}
{tasks_html}
<p><a href="{meeting_url}">Подробнее на портале</a></p>
<hr>
<p style="color:#999;font-size:12px;">Это автоматическое уведомление портала кафедры.</p>
"""
        send_email(user.email, subject, body_html)
