import smtplib
import logging
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid, formataddr
from flask import current_app

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_html: str) -> bool:
    config = current_app.config
    host = config.get("SMTP_HOST", "localhost")
    port = config.get("SMTP_PORT", 587)
    user = config.get("SMTP_USER", "")
    password = config.get("SMTP_PASSWORD", "")
    use_tls = config.get("SMTP_USE_TLS", True)
    mail_from = config.get("MAIL_FROM", "noreply@department.local")
    from_name = config.get("MAIL_FROM_NAME", "Портал кафедры")

    if not host:
        logger.warning("SMTP not configured — email not sent (to=%s, subject=%s)", to, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, mail_from))
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=mail_from.split("@")[-1] if "@" in mail_from else None)
    msg["MIME-Version"] = "1.0"

    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        if use_tls:
            server = smtplib.SMTP(host, port)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(host, port)

        if user and password:
            server.login(user, password)

        server.sendmail(mail_from, [to], msg.as_string())
        server.quit()
        logger.info("Email sent to %s — %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False
