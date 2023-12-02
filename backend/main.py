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
