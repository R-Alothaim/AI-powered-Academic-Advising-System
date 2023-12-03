import os
import re
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel

from ultimate_rag_system import UltimateRAGSystem
from auth_router import (
    router as auth_router,
    user_router,
    setup as auth_setup,
    _decode_jwt,
    _get_current_user,
)
from calendar_router import router as calendar_router

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_socket = os.getenv("MYSQL_UNIX_SOCKET", "")
_user = os.getenv("MYSQL_USER", "root")
_password = os.getenv("MYSQL_PASSWORD", "")
_host = os.getenv("MYSQL_HOST", "localhost")
_db = os.getenv("MYSQL_DB", "university_reviews")
