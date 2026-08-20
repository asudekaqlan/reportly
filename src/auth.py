"""Local JSONL accounts. Passwords are salted hashes; no SQL database.

Roles: customer (chat UI) and admin (complaint queue).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USERS_PATH = ROOT / "data" / "users.jsonl"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_CAPTCHA_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DEFAULT_ADMIN_EMAIL = "admin@reportly.local"
DEFAULT_ADMIN_PASSWORD = "AdminReportly1!"


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))


def password_checks(password: str) -> dict[str, bool]:
    value = password or ""
    return {
        "length": len(value) >= 12,
        "upper": bool(re.search(r"[A-Z]", value)),
        "lower": bool(re.search(r"[a-z]", value)),
        "digit": bool(re.search(r"[0-9]", value)),
        "special": bool(re.search(r"[^A-Za-z0-9]", value)),
    }


def password_issues(password: str) -> list[str]:
    checks = password_checks(password)
    labels = {
        "length": "En az 12 karakter olmalı.",
        "upper": "En az bir büyük harf olmalı.",
        "lower": "En az bir küçük harf olmalı.",
        "digit": "En az bir rakam olmalı.",
        "special": "En az bir özel karakter olmalı.",
    }
    return [labels[key] for key, ok in checks.items() if not ok]


def random_captcha(length: int = 5) -> str:
    return "".join(secrets.choice(_CAPTCHA_ALPHABET) for _ in range(length))


def random_email_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def captcha_matches(expected: str, typed: str) -> bool:
    return (expected or "").strip().upper() == (typed or "").strip().upper()


def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return (
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def _load_users() -> list[dict]:
    if not USERS_PATH.exists():
        return []
    users: list[dict] = []
    for line in USERS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        users.append(json.loads(line))
    return users


def find_user(email: str) -> dict | None:
    needle = (email or "").strip().lower()
    if not needle:
        return None
    for user in _load_users():
        if str(user.get("email", "")).lower() == needle:
            return user
    return None


def public_user(user: dict) -> dict:
    return {
        "email": user.get("email", ""),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "role": user.get("role") or "customer",
    }


def authenticate(email: str, password: str, *, role: str | None = None) -> dict | None:
    user = find_user(email)
    if not user:
        return None
    try:
        salt = base64.b64decode(user.get("salt", ""))
        expected = base64.b64decode(user.get("password_hash", ""))
    except (ValueError, TypeError):
        return None
    _, digest = _hash_password(password, salt)
    actual = base64.b64decode(digest)
    if not secrets.compare_digest(actual, expected):
        return None
    user_role = user.get("role") or "customer"
    if role and user_role != role:
        return None
    return public_user(user)


def register_user(
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
) -> dict:
    email_norm = email.strip().lower()
    if find_user(email_norm):
        raise ValueError("Bu e-posta ile kayıtlı bir hesap zaten var.")
    salt, password_hash = _hash_password(password)
    user = {
        "email": email_norm,
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "salt": salt,
        "password_hash": password_hash,
        "consent": True,
        "role": "customer",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USERS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(user, ensure_ascii=False) + "\n")
    return public_user(user)


def ensure_default_admin() -> None:
    if find_user(DEFAULT_ADMIN_EMAIL):
        return
    salt, password_hash = _hash_password(DEFAULT_ADMIN_PASSWORD)
    admin = {
        "email": DEFAULT_ADMIN_EMAIL,
        "first_name": "ITSM",
        "last_name": "Admin",
        "salt": salt,
        "password_hash": password_hash,
        "consent": True,
        "role": "admin",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USERS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(admin, ensure_ascii=False) + "\n")
