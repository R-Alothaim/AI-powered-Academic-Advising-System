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
