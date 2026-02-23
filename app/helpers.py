import uuid
import re
import time
import random
import string
from datetime import datetime, timezone


def generate_cuid():
    """Generate a CUID-like unique ID."""
    return uuid.uuid4().hex[:25]


def generate_order_number():
    """Generate order number like ORD-XXXXXX-YYYY."""
    now = int(time.time() * 1000)
    base36 = ""
    while now:
        now, rem = divmod(now, 36)
        base36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[rem] + base36
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{base36}-{rand}"


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def format_price(cents, currency="usd"):
    """Format price in cents to display string."""
    amount = cents / 100
    symbols = {"usd": "$", "eur": "\u20ac", "gbp": "\u00a3"}
    symbol = symbols.get(currency.lower(), "")
    if symbol:
        return f"{symbol}{amount:,.2f}"
    return f"{amount:,.2f} {currency.upper()}"


def utcnow():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)
