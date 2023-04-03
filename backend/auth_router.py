import os
import re
import hmac
import json
import base64
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import bcrypt

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
user_router = APIRouter(tags=["users"])

_get_db = None
_Base = None
_User = None

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
if not os.getenv("JWT_SECRET"):
    logger.warning("JWT_SECRET not set — using random secret (tokens will not survive restarts)")
JWT_EXPIRY_HOURS = 24
ALLOWED_DOMAINS = ["university.edu.sa"]

def _db_dependency():
    gen = _get_db()
    try:
        db = next(gen)
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("$2y$") or stored.startswith("$2b$") or stored.startswith("$2a$"):
        try:
            normalized = stored.replace("$2y$", "$2b$", 1)
            return bcrypt.checkpw(password.encode(), normalized.encode())
        except Exception:
            return False
    if "$" not in stored:
        return False
    salt, h = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(check.hex(), h)

def _make_jwt(user_id: int, name: str, email: str, created_at) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_dict = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "created_at": str(created_at) if created_at else None,
        "exp": (datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)).timestamp(),
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    sig = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"

def _decode_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("bad token")
    header, payload, sig = parts
    expected = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise ValueError("bad signature")
    pad = lambda s: s + "=" * (-len(s) % 4)
    data = json.loads(base64.urlsafe_b64decode(pad(payload)))
    if data["exp"] < datetime.now(timezone.utc).timestamp():
        raise ValueError("expired")
    return data

def _get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    try:
        return _decode_jwt(auth_header[7:])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

def _is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@", 1)[1].lower()
    return domain in ALLOWED_DOMAINS

def _is_strong_password(p: str) -> bool:
    return (
        len(p) >= 8
        and bool(re.search(r"[A-Z]", p))
        and bool(re.search(r"[a-z]", p))
        and bool(re.search(r"\d", p))
        and bool(re.search(r"[^A-Za-z0-9]", p))
    )

def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000}"

class LoginIn(BaseModel):
    email: str
    password: str

class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
