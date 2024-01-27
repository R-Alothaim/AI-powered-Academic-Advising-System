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
    # Enum member for general advice queries
    GENERAL_ADVICE = "general_advice"
    # Enum member for specific course information queries
    COURSE_INFO = "course_info"

@dataclass
# Apply the dataclass decorator to automatically generate methods like __init__ and __repr__
@dataclass
class ContextChunk:
    content: str
    source: str
    chunk_type: str
    # Dictionary containing additional metadata about the chunk
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    relevance_score: float = 0.0

class UltimateRAGSystem:
    """
    Advanced RAG system with multi-modal context retrieval,
    semantic search, and intelligent response grounding.
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.db_path = self.workspace_path / "rag_knowledge.db"
        self.embeddings_model = None
        # Initialize the embeddings matrix to None (Replaces FAISS index)
        self.embeddings_matrix = None
        
        # Check if machine learning libraries are available
        if ML_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")

        
        self.chunks = []
        
        # Ensure the cache directory exists
        self._ensure_cache_dir()
        # Initialize the SQLite database schema
        self._init_database()
        
        self.course_mapping = {}
        self._load_course_mapping()
        
        # Try to load the existing index from disk
        if not self.load_index():
            # If load fails, load all documents from source
            self._load_all_documents()
            # If ML libraries and model are available
            if ML_AVAILABLE and self.embeddings_model:
                self._build_vector_index()
                self.save_index()
        
    def save_index(self):
        """Save vector index and chunks to disk."""
        # Check if the index or chunks are missing
        if self.embeddings_matrix is None or not self.chunks:
            # If so, return immediately without saving
            return
            
        try:
            import pickle
            embeddings_path = self.workspace_path / "cache/embeddings.npy"
            np.save(embeddings_path, self.embeddings_matrix)
            
            chunks_path = self.workspace_path / "cache/chunks.pkl"
            with open(chunks_path, 'wb') as f:
                # Dump the chunks list to the file using pickle
                pickle.dump(self.chunks, f)
            logger.info("Saved vector embeddings and chunks to disk")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def load_index(self) -> bool:
        """Load vector index and chunks from disk."""
        # Check if machine learning libraries are available
        if not ML_AVAILABLE:
            # If not, return False indicating failure to load
            return False
            
        try:
            import pickle
            embeddings_path = self.workspace_path / "cache/embeddings.npy"
            chunks_path = self.workspace_path / "cache/chunks.pkl"
            
            if not embeddings_path.exists() or not chunks_path.exists():
                # If either is missing, return False
                return False
                
            self.embeddings_matrix = np.load(embeddings_path)
            
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
                
            logger.info(f"Loaded vector index with {len(self.chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
        
    # Define the helper method to ensure the cache directory exists
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        cache_dir = self.workspace_path / "cache"
        cache_dir.mkdir(exist_ok=True)
        self.db_path = cache_dir / "rag_knowledge.db"
        
    def _init_database(self):
        """Initialize SQLite database for structured knowledge storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
