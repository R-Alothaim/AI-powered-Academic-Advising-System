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


LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")


class LLMClient:
    def __init__(self):
        self.base_url = LLM_BASE_URL
        self.model = LLM_MODEL

    async def generate_response(self, messages: List[Dict[str, str]], context_info: Dict[str, Any] = None) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.85, "top_k": 40, "repeat_penalty": 1.1},
                }
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    return response.json().get("message", {}).get("content", "No response generated")
                logger.error(f"LLM API error: {response.status_code}")
                return "Sorry, I'm experiencing technical difficulties. Please try again."
            except Exception as e:
                logger.error(f"LLM connection error: {e}")
                return "Sorry, I'm currently unavailable. Please try again later."


llm_client = LLMClient()


def detect_language(text: str) -> str:
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    return "ar" if arabic_chars > len(text) * 0.3 else "en"


def is_academic_question(text: str) -> bool:
    keywords = {
        "en": [
            "course", "prerequisite", "credit", "gpa", "grade", "exam", "test",
            "registration", "enrollment", "withdraw", "drop", "semester", "academic",
            "degree", "major", "graduation", "transcript", "schedule", "calendar",
            "university", "college", "student", "advisor", "plan", "level",
            "project", "senior", "lecture", "attend", "absence", "excuse", "class",
            "program", "duration", "computer", "science", "deadline", "fee",
            "tuition", "scholarship", "instructor", "professor", "office",
            "cs", "math", "lab", "midterm", "final", "quiz", "assignment", "study",
        ],
        "ar": [
            "مقرر", "متطلب", "ساعة", "معدل", "درجة", "اختبار", "امتحان",
            "تسجيل", "انسحاب", "حذف", "فصل", "أكاديمي", "تخصص", "تخرج",
            "جدول", "تقويم", "جامعة", "كلية", "طالب", "مرشد", "خطة", "مستوى",
            "مشروع", "محاضرة", "حضور", "غياب", "برنامج", "حاسب", "علوم",
            "موعد", "رسوم", "منحة", "دكتور", "أستاذ", "مكتب",
            "واجب", "معمل", "نصفي", "نهائي", "دراسة", "مذاكرة",
        ],
    }
    text_lower = text.lower()
    if re.search(r"cs\s*\d{3}", text_lower):
        return True
    lang = detect_language(text)
    if any(kw in text_lower for kw in keywords.get(lang, keywords["en"])):
        return True
    if re.search(r"\d+%", text):
        return True
    follow_ups = [r"what else", r"tell me more", r"more info", r"what about", r"ماذا أيضا", r"المزيد", r"أخبرني المزيد"]
    return any(re.search(p, text_lower) for p in follow_ups)


@app.get("/")
async def root():
    return {
        "message": "University Academic Advising System API v3.0",
        "status": "active",
        "rag_system": "enabled" if rag_system else "disabled",
    }


@app.get("/health")
async def health_check():
    rag_status = "healthy" if rag_system and rag_system.embeddings_matrix is not None else "unavailable"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{LLM_BASE_URL}/api/tags")
            llm_status = "healthy" if r.status_code == 200 else "unhealthy"
    except Exception:
        llm_status = "unreachable"
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "healthy",
            "rag_system": rag_status,
            "llm": llm_status,
            "vector_index": f"{len(rag_system.chunks) if rag_system else 0} chunks indexed",
        },
    }


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    return {
        "chats": db.query(Chat).count(),
        "messages": db.query(Message).count(),
        "rag_chunks": len(rag_system.chunks) if rag_system else 0,
        "supported_languages": ["en", "ar"],
    }


@app.get("/users/{user_id}/chats", response_model=List[ChatOut])
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).all()
    return [
        ChatOut(id=c.id, title=c.title, message_count=c.message_count or 0, created_at=c.created_at)
        for c in chats
    ]


@app.post("/chats")
async def create_chat(chat_in: Dict[str, Any], db: Session = Depends(get_db)):
    user_id = chat_in.get("user_id", 1)
    title = chat_in.get("title", "New Chat")
    try:
        chat = Chat(user_id=user_id, title=title)
