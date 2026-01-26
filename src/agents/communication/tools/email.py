"""Email tools for the Communication Agent."""

import imaplib
import email
import re
from email.header import decode_header
from datetime import datetime

from langchain_core.tools import tool

from src.config import get_settings


@tool
def read_email(count: int = 10) -> str:
    """Reads emails from the configured email account.
    
    Args:
        count: Number of recent emails to read (default: 10)
        
    Returns:
        Formatted string with email contents
    """
    settings = get_settings()
    
    if not settings.gmx_pw:
        return "❌ Error: GMX_PW environment variable not set"
    
    try:
        mail = imaplib.IMAP4_SSL(settings.gmx_imap_server, settings.gmx_imap_port)
        mail.login(settings.gmx_email, settings.gmx_pw)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        email_ids = email_ids[-count:]

        result = f"📧 Reading last {len(email_ids)} emails from {settings.gmx_email}\n\n"
        result += "=" * 80 + "\n\n"

        for email_id in reversed(email_ids):
            status, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject = msg["Subject"]
                    if subject:
                        decoded_subject = decode_header(subject)[0]
                        if isinstance(decoded_subject[0], bytes):
                            subject = decoded_subject[0].decode(decoded_subject[1] or "utf-8")
                        else:
                            subject = decoded_subject[0]

                    from_addr = msg.get("From", "Unknown")
                    date = msg.get("Date", "Unknown")

                    body = _extract_body(msg)

                    if len(body) > 500:
                        body = body[:500] + "\n... (truncated)"

                    result += f"From: {from_addr}\n"
                    result += f"Subject: {subject}\n"
                    result += f"Date: {date}\n"
                    result += f"\n{body}\n"
                    result += "\n" + "-" * 80 + "\n\n"

        mail.close()
        mail.logout()

        return result

    except Exception as e:
        return f"❌ Error reading emails: {str(e)}\n\nPlease check your credentials and internet connection."


def _extract_body(msg) -> str:
    """Extract body text from email message."""
    body = ""
    body_found = False

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain" and not body_found:
                try:
                    payload = part.get_payload(decode=True)
                    if payload and isinstance(payload, bytes):
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        body_found = True
                        break
                except Exception:
                    pass

            elif content_type == "text/html" and not body_found:
                try:
                    payload = part.get_payload(decode=True)
                    if payload and isinstance(payload, bytes):
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='replace')
                        body = re.sub('<[^<]+?>', '', html_body)
                        body = re.sub(r'\s+', ' ', body).strip()
                        body_found = True
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload and isinstance(payload, bytes):
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
                body_found = True
        except Exception:
            try:
                body = str(msg.get_payload())
                body_found = True
            except Exception:
                body = "Could not decode email body"

    if not body_found or not body:
        body = "[No readable content found]"

    return body


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email (placeholder - not yet implemented).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        
    Returns:
        Status message
    """
    # TODO: Implement SMTP sending
    return f"⚠️ Email sending not yet implemented. Would send to: {to}"
