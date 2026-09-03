
import requests

import config

RESEND_URL = "https://api.resend.com/emails"
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
TIMEOUT = 15


class MailError(RuntimeError):
    pass


def send_email(to, subject, html):
    """Return True on success, raise MailError with the provider's reason on failure."""
    if not config.EMAIL_API_KEY:
        raise MailError("EMAIL_API_KEY chưa được đặt trong backend/.env")

    if config.EMAIL_PROVIDER == "sendgrid":
        return _send_sendgrid(to, subject, html)
    return _send_resend(to, subject, html)


def _send_resend(to, subject, html):
    payload = {
        "from": config.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if config.EMAIL_REPLY_TO:
        payload["reply_to"] = config.EMAIL_REPLY_TO

    res = requests.post(
        RESEND_URL,
        json=payload,
        headers={"Authorization": f"Bearer {config.EMAIL_API_KEY}"},
        timeout=TIMEOUT,
    )
    if res.status_code >= 400:
        raise MailError(f"Resend {res.status_code}: {res.text[:300]}")
    return True


def _send_sendgrid(to, subject, html):
    # sendgrid wants the sender split into name/email, ours is "Name <addr>"
    sender = config.EMAIL_FROM
    name = ""
    if "<" in sender and sender.endswith(">"):
        name, sender = sender.split("<", 1)
        name, sender = name.strip(), sender[:-1].strip()

    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": sender, "name": name} if name else {"email": sender},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}],
    }
    if config.EMAIL_REPLY_TO:
        payload["reply_to"] = {"email": config.EMAIL_REPLY_TO}

    res = requests.post(
        SENDGRID_URL,
        json=payload,
        headers={"Authorization": f"Bearer {config.EMAIL_API_KEY}"},
        timeout=TIMEOUT,
    )
    if res.status_code >= 400:
        raise MailError(f"SendGrid {res.status_code}: {res.text[:300]}")
    return True
