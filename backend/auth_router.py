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
