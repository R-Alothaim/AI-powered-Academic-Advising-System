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
