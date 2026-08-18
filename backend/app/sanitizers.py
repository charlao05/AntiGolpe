import re
from urllib.parse import urlsplit, urlunsplit
CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
CNPJ = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{14}\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\s-]?\d{4}(?!\d)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
PIX_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

def sanitize_text(text: str) -> str:
    out = CPF.sub("[CPF_REDACTED]", text)
    out = CNPJ.sub("[CNPJ_REDACTED]", out)
    out = EMAIL.sub("[EMAIL_REDACTED]", out)
    out = CARD.sub("[CARD_REDACTED]", out)
    out = PHONE.sub("[PHONE_REDACTED]", out)
    return PIX_UUID.sub("[PIX_KEY_REDACTED]", out)

def sanitize_url(raw: str | None) -> str | None:
    if not raw: return None
    try:
        parts = urlsplit(raw.strip() if "://" in raw.strip() else "https://" + raw.strip())
        if not parts.netloc: return None
        return urlunsplit(((parts.scheme or "https").lower(), (parts.hostname or "").lower(), parts.path.rstrip("/") or "/", "", ""))
    except ValueError:
        return None
