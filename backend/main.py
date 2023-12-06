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

if _socket:
    DATABASE_URL = f"mysql+pymysql://{_user}:{_password}@localhost/{_db}?unix_socket={_socket}"
else:
    DATABASE_URL = f"mysql+pymysql://{_user}:{_password}@{_host}/{_db}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

rag_system: Optional[UltimateRAGSystem] = None

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(100), default="New Chat")
    message_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    sender = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
