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


class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

class ChatOut(BaseModel):
    id: int
    title: str
    message_count: int = 0
    created_at: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_system
    logger.info("Initializing RAG System...")
    workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rag_system = UltimateRAGSystem(workspace_path)
    logger.info("RAG System initialized")

    Base.metadata.create_all(bind=engine)
    auth_setup(get_db, Base, engine)
    logger.info("Database and auth initialized")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="University Academic Advising System",
    description="AI-powered academic advisor with RAG-based context grounding",
    version="3.0.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(calendar_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/auth/me")
async def auth_me(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        data = _decode_jwt(auth_header[7:])
        return {
            "user_id": data["user_id"],
            "name": data["name"],
            "email": data["email"],
            "created_at": data.get("created_at"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

