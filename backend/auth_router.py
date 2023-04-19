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

class OtpIn(BaseModel):
    email: str
    code: str

class EmailIn(BaseModel):
    email: str

class ResetIn(BaseModel):
    email: str
    otp: str

class PasswordChangeIn(BaseModel):
    new_password: str
    confirm_password: str

def setup(get_db, Base, engine):
    global _get_db, _Base, _User

    _get_db = get_db

    class User(Base):
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}
        user_id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(255))
        email = Column(String(255), unique=True)
        password = Column(String(255))
        is_verified = Column(Integer, default=0)
        otp_hash = Column(String(255), nullable=True)
        otp_expires_at = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    _User = User
    Base.metadata.create_all(bind=engine)

@router.post("/register")
async def register(data: RegisterIn, db: Session = Depends(_db_dependency)):
    if not _is_valid_email(data.email):
        raise HTTPException(400, "Only @university.edu.sa emails are allowed")
    if not _is_strong_password(data.password):
        raise HTTPException(400, "Password must be 8+ chars with upper, lower, digit, and special character")

    existing = db.query(_User).filter(_User.email == data.email).first()
    if existing and existing.is_verified:
        raise HTTPException(400, "Email already registered")
    if existing and not existing.is_verified:
        db.delete(existing)
        db.commit()

    otp = _generate_otp()
    user = _User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password=_hash_password(data.password),
        is_verified=0,
        otp_hash=_hash_password(otp),
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # TODO: Send OTP via email (SMTP). For dev, check server logs at DEBUG level.
    logger.debug(f"[DEV-ONLY] OTP for {data.email}: {otp}")

    return {"message": "OTP sent to your email", "email": data.email}

@router.post("/login")
async def login(data: LoginIn, db: Session = Depends(_db_dependency)):
    user = db.query(_User).filter(_User.email == data.email.lower().strip()).first()
    if not user:
        raise HTTPException(401, "Invalid email or password")

    if not _verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid email or password")

    if user.password and (user.password.startswith("$2y$") or user.password.startswith("$2b$") or user.password.startswith("$2a$")):
        user.password = _hash_password(data.password)
        db.commit()

    if not user.is_verified:
        otp = _generate_otp()
        user.otp_hash = _hash_password(otp)
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        logger.debug(f"[DEV-ONLY] Verification OTP for {data.email}: {otp}")
        return {"requires_verification": True, "email": data.email, "message": "Please verify your email first"}

    token = _make_jwt(user.user_id, user.name, user.email, user.created_at)
    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "created_at": str(user.created_at),
        },
    }

@router.post("/verify-otp")
async def verify_otp(data: OtpIn, db: Session = Depends(_db_dependency)):
    user = db.query(_User).filter(_User.email == data.email.lower().strip()).first()
    if not user:
        raise HTTPException(400, "Invalid request")
    if not user.otp_hash or not user.otp_expires_at:
        raise HTTPException(400, "No OTP pending")
    if datetime.now(timezone.utc) > user.otp_expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(400, "OTP has expired. Please request a new one.")
    if not _verify_password(data.code, user.otp_hash):
        raise HTTPException(400, "Invalid OTP code")

    user.is_verified = 1
    user.otp_hash = None
    user.otp_expires_at = None
    db.commit()

    token = _make_jwt(user.user_id, user.name, user.email, user.created_at)
    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "created_at": str(user.created_at),
        },
    }

@router.post("/resend-otp")
async def resend_otp(data: EmailIn, db: Session = Depends(_db_dependency)):
    user = db.query(_User).filter(_User.email == data.email.lower().strip()).first()
    if not user:
        return {"message": "If an account exists, a new OTP has been sent"}

    otp = _generate_otp()
    user.otp_hash = _hash_password(otp)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    logger.debug(f"[DEV-ONLY] Resend OTP for {data.email}: {otp}")
    return {"message": "If an account exists, a new OTP has been sent"}

@router.post("/forgot-password")
async def forgot_password(data: EmailIn, db: Session = Depends(_db_dependency)):
    if not _is_valid_email(data.email):
        raise HTTPException(400, "Only @university.edu.sa emails are allowed")

    user = db.query(_User).filter(_User.email == data.email.lower().strip()).first()
    if not user:
        return {"message": "If an account exists, an OTP has been sent", "email": data.email}

    otp = _generate_otp()
    user.otp_hash = _hash_password(otp)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    logger.debug(f"[DEV-ONLY] Forgot-password OTP for {data.email}: {otp}")
    return {"message": "If an account exists, an OTP has been sent", "email": data.email}

@router.post("/reset-password")
async def reset_password(data: ResetIn, db: Session = Depends(_db_dependency)):
    user = db.query(_User).filter(_User.email == data.email.lower().strip()).first()
    if not user:
        raise HTTPException(400, "Invalid request")
    if not user.otp_hash or not user.otp_expires_at:
        raise HTTPException(400, "No OTP pending")
    if datetime.now(timezone.utc) > user.otp_expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(400, "OTP has expired")
    if not _verify_password(data.otp, user.otp_hash):
        raise HTTPException(400, "Invalid OTP code")

    temp_password = secrets.token_urlsafe(8)
    user.password = _hash_password(temp_password)
    user.otp_hash = None
    user.otp_expires_at = None
    db.commit()

    # TODO: Send temp password via email (SMTP)
    logger.debug(f"[DEV-ONLY] Temp password for {data.email}: {temp_password}")
    return {"message": "A temporary password has been sent to your email"}

@user_router.get("/users/{user_id}")
async def get_user(user_id: int, request: Request, db: Session = Depends(_db_dependency)):
    current = _get_current_user(request)
    if current["user_id"] != user_id:
        raise HTTPException(403, "Forbidden")
    user = db.query(_User).filter(_User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "created_at": str(user.created_at),
    }

@user_router.post("/users/{user_id}/change-password")
