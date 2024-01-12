"""
Ultimate RAG System for University Academic Advising
Advanced Multi-Modal Context Retrieval and Response Generation
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import re
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
import numpy as np
# Try to import machine learning libraries
try:
    from sentence_transformers import SentenceTransformer
    # Import FAISS for vector search - REMOVED due to dependency issues
    # import faiss
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries (sentence-transformers) not found. RAG features will be disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    # Enum member for course prerequisite queries
    COURSE_PREREQUISITE = "course_prerequisite"
    # Enum member for academic calendar queries
    ACADEMIC_CALENDAR = "academic_calendar"
    # Enum member for registration queries
    REGISTRATION = "registration"
    # Enum member for GPA and grades queries
    GPA_GRADES = "gpa_grades"
    # Enum member for course withdrawal queries
    WITHDRAWAL = "withdrawal"
    # Enum member for academic policy queries
    ACADEMIC_POLICY = "academic_policy"
