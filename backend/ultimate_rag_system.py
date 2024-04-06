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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_prerequisites (
                course_code TEXT PRIMARY KEY,
                course_name_en TEXT,
                course_name_ar TEXT,
                credits INTEGER,
                prerequisites TEXT,
                description TEXT,
                program TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS academic_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_en TEXT,
                event_ar TEXT,
                hijri_start TEXT,
                hijri_end TEXT,
                gregorian_start TEXT,
                gregorian_end TEXT,
                status TEXT,
                category TEXT,
                level TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS academic_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_name_en TEXT,
                policy_name_ar TEXT,
                content_en TEXT,
                content_ar TEXT,
                category TEXT,
                source_document TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                source_file TEXT,
                chunk_type TEXT,
                language TEXT,
                metadata TEXT,
                embedding_vector BLOB
            )
        """)
        
        conn.commit()
        conn.close()
        
    def _load_all_documents(self):
        """Load and process all available documents."""
        logger.info("Loading all University documents...")
        
        self._load_cs_courses()
        
        self._load_manual_course_details()
        
        self._load_academic_calendar()
        
        self._load_general_info()
        
        self._load_document_chunks()
        
        logger.info(f"Loaded {len(self.chunks)} knowledge chunks")
        
    def _load_cs_courses(self):
        """Load CS course prerequisites from the official list."""
        cs_courses_file = self.workspace_path / "data/project-pdfs/CS_Courses_List.txt"
        
        if not cs_courses_file.exists():
            # Log a warning if the file is missing
            logger.warning(f"CS Courses List file not found at {cs_courses_file}")
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        with open(cs_courses_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        course_pattern = r'(\d+)\s*\|\s*(CS\d+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|\n]*)'
        matches = re.findall(course_pattern, content)
        
        for match in matches:
            order, code, name, credits, prereqs = match
            prereqs = prereqs.strip() if prereqs.strip() != '-' else ''
            
            cursor.execute("""
                INSERT OR REPLACE INTO course_prerequisites 
                (course_code, course_name_en, credits, prerequisites, program)
                VALUES (?, ?, ?, ?, ?)
            """, (code, name.strip(), int(credits), prereqs, 'Computer Science'))
            
            chunk_content = f"Course {code}: {name.strip()}. Credits: {credits}. Prerequisites: {prereqs or 'None'}"
            chunk = ContextChunk(
                content=chunk_content,
                source="CS_Courses_List.txt",
                chunk_type="course_info",
                metadata={
                    "course_code": code,
                    "course_name": name.strip(),
                    "credits": credits,
                    "prerequisites": prereqs,
                    "language": "en"
                }
            )
            self.chunks.append(chunk)
            
        conn.commit()
        conn.close()
        logger.info(f"Loaded {len(matches)} CS courses")
        
    def _load_academic_calendar(self):
        """Load academic calendar from JSON files."""
        calendar_files = [
            self.workspace_path / "cache/calendar_1447_en.json",
            self.workspace_path / "cache/calendar_1447_ar.json"
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for calendar_file in calendar_files:
            if not calendar_file.exists():
                # Skip if file is missing
                continue
                
            # Determine the language based on the filename
            lang = 'ar' if '_ar.json' in str(calendar_file) else 'en'
            
            with open(calendar_file, 'r', encoding='utf-8') as f:
                calendar_data = json.load(f)
                
            for level, events in calendar_data.items():
                for event in events:
                    event_name = event.get('event', '')
                    hijri_start = event.get('hijri_start', '')
                    hijri_end = event.get('hijri_end', '')
                    gregorian_start = event.get('gregorian_start', '')
                    gregorian_end = event.get('gregorian_end', '')
                    status = event.get('status', '')
                    
                    if lang == 'en':
                        cursor.execute("""
                            INSERT OR REPLACE INTO academic_calendar 
                            (event_en, hijri_start, hijri_end, gregorian_start, gregorian_end, status, category, level)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (event_name, hijri_start, hijri_end, gregorian_start, gregorian_end, status, 'calendar', level))
                    else:
                        # Update existing record with Arabic event name
                        cursor.execute("""
                            UPDATE academic_calendar SET event_ar = ? 
                            WHERE event_en = ? OR (hijri_start = ? AND gregorian_start = ?)
                        """, (event_name, '', hijri_start, gregorian_start))
                    
                    chunk_content = f"Event: {event_name}. Dates: {gregorian_start} to {gregorian_end}. Status: {status}"
                    chunk = ContextChunk(
                        content=chunk_content,
                        source=f"calendar_1447_{lang}.json",
                        chunk_type="calendar_event",
                        metadata={
                            "event": event_name,
                            "hijri_start": hijri_start,
                            "hijri_end": hijri_end,
                            "gregorian_start": gregorian_start,
                            "gregorian_end": gregorian_end,
                            "status": status,
                            "level": level,
                            "language": lang
                        }
                    )
                    self.chunks.append(chunk)
                    
        conn.commit()
        conn.close()
        logger.info("Loaded academic calendar data")
        
    def _load_document_chunks(self):
        """Load additional document chunks for comprehensive coverage."""
        policy_chunks = [
            {
                "content": "Academic standing is determined by cumulative GPA. Students with GPA below 2.0 may be placed on academic probation.",
                "source": "academic_policies",
                "chunk_type": "policy",
                "metadata": {"category": "gpa", "language": "en"}
            },
            {
                "content": "الوضع الأكاديمي يحدد بناءً على المعدل التراكمي. الطلاب الذين معدلهم أقل من 2.0 قد يوضعون تحت الإنذار الأكاديمي.",
                "source": "academic_policies",
                "chunk_type": "policy", 
                "metadata": {"category": "gpa", "language": "ar"}
            },
            {
                "content": "Course withdrawal deadlines: With refund by September 4, 2025. Without refund by December 6, 2025.",
                "source": "academic_calendar",
                "chunk_type": "deadline",
                "metadata": {"category": "withdrawal", "language": "en"}
            },
            {
                "content": "مواعيد انسحاب المقررات: مع الاسترداد حتى 4 سبتمبر 2025. بدون استرداد حتى 6 ديسمبر 2025.",
                "source": "academic_calendar",
                "chunk_type": "deadline",
                "metadata": {"category": "withdrawal", "language": "ar"}
            },
            {
                "content": "Attendance Policy: Students are expected to attend all lectures. Missing more than 25% of lectures without a valid excuse will result in a DN (Denial) grade, which disqualifies the student from the course.",
                "source": "academic_policies",
                "chunk_type": "policy",
                "metadata": {"category": "attendance", "language": "en"}
            },
            {
                "content": "سياسة الحضور: يتوقع من الطلاب حضور جميع المحاضرات. غياب أكثر من 25% من المحاضرات بدون عذر مقبول سيؤدي إلى الحرمان (DN)، مما يعني استبعاد الطالب من المقرر.",
                "source": "academic_policies",
                "chunk_type": "policy",
                "metadata": {"category": "attendance", "language": "ar"}
            },
            {
                "content": "Grade Appeal Policy: Students have the right to object to their final grade. The appeal must be submitted via the electronic portal within 15 days of the result announcement. The appeal is reviewed by the department council.",
                "source": "academic_policies",
                "chunk_type": "policy",
                "metadata": {"category": "grades", "language": "en"}
            },
            {
                "content": "سياسة الاعتراض على الدرجات: يحق للطالب الاعتراض على النتيجة النهائية. يجب تقديم الاعتراض عبر البوابة الإلكترونية خلال 15 يوماً من إعلان النتيجة. يتم النظر في الاعتراض من قبل مجلس القسم.",
                "source": "academic_policies",
                "chunk_type": "policy",
                "metadata": {"category": "grades", "language": "ar"}
            },
            {
                "content": "Student Rights - Complaints: Students have the right to file a complaint against any faculty member or staff for misconduct (e.g., insults, harassment). Complaints should be submitted to the Head of Department or via the Student Rights Unit.",
                "source": "student_rights",
                "chunk_type": "policy",
                "metadata": {"category": "complaints", "language": "en"}
            },
            {
                "content": "حقوق الطالب - الشكاوى: يحق للطالب تقديم شكوى ضد أي عضو هيئة تدريس أو موظف في حال سوء السلوك (مثل الإهانة أو التحرش). تقدم الشكاوى لرئيس القسم أو عبر وحدة حقوق الطلاب.",
                "source": "student_rights",
                "chunk_type": "policy",
                "metadata": {"category": "complaints", "language": "ar"}
            }
        ]
        
        for chunk_data in policy_chunks:
            chunk = ContextChunk(
                content=chunk_data["content"],
                source=chunk_data["source"],
                chunk_type=chunk_data["chunk_type"],
                metadata=chunk_data["metadata"]
            )
            self.chunks.append(chunk)
            
    def _build_vector_index(self):
        """Build Numpy vector index for semantic search."""
        if not ML_AVAILABLE or not self.chunks:
            logger.warning("No chunks available or ML libraries missing")
            return
            
        logger.info("Building vector index...")
        
        texts = [chunk.content for chunk in self.chunks]
        # Encode texts using the sentence transformer model
        embeddings = self.embeddings_model.encode(texts)
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1
        # Normalize
        embeddings = embeddings / norms
        
        for i, chunk in enumerate(self.chunks):
            chunk.embedding = embeddings[i]
            
        self.embeddings_matrix = embeddings.astype(np.float32)
        
        logger.info(f"Built vector index with {len(self.chunks)} embeddings")

    def _load_manual_course_details(self):
        """Load manual course details for Senior Projects."""
        courses = [
            {
                "content": "Course: CS479 Senior Project 1\\nCredits: 3\\nPrerequisites: CS350, CS352\\nDescription:\\nThis is the first part of a two-semester senior project sequence. Students work in teams to design and implement a significant software system. The course focuses on project proposal, requirements analysis, system design, and initial implementation. Students learn to apply software engineering principles, project management techniques, and effective communication skills.\\nObjectives:\\n1. Apply software engineering lifecycle models.\\n2. Conduct feasibility studies and requirements elicitation.\\n3. Design software architecture and user interfaces.\\n4. Develop a project plan and schedule.\\n5. Present technical proposals and progress reports.",
                "source": "manual_course_details",
                "chunk_type": "course_details",
                "metadata": {"course_code": "CS479", "type": "course_details"}
            },
            {
                "content": "Course: CS489 Senior Project 2\\nCredits: 3\\nPrerequisites: CS479\\nDescription:\\nThis is the second part of the senior project sequence. Students continue the work started in CS479, focusing on implementation, testing, deployment, and evaluation of the software system. The course culminates in a final presentation and demonstration of the completed project.\\nObjectives:\\n1. Implement the software system based on the design from CS479.\\n2. Perform unit, integration, and system testing.\\n3. Deploy and maintain the software application.\\n4. Evaluate the system against initial requirements.\\n5. Write a comprehensive final report and user manual.\\n6. Demonstrate the final product to faculty and peers.",
                "source": "manual_course_details",
                "chunk_type": "course_details",
                "metadata": {"course_code": "CS489", "type": "course_details"}
            }
        ]
        
        for chunk_data in courses:
            chunk = ContextChunk(
                content=chunk_data["content"],
                source=chunk_data["source"],
                chunk_type=chunk_data["chunk_type"],
                metadata=chunk_data["metadata"]
            )
            self.chunks.append(chunk)

    def _load_general_info(self):
        """Load general information about the program."""
        general_info = [
            {
                "content": "The Computer Science (CS) program duration is typically 4 years, consisting of 8 semesters. The program is divided into 8 levels, with each level corresponding to one semester.",
                "source": "general_info",
                "chunk_type": "program_info",
                "metadata": {"category": "duration", "language": "en"}
            },
            {
                "content": "مدة برنامج علوم الحاسب (CS) هي عادة 4 سنوات، وتتكون من 8 فصول دراسية. ينقسم البرنامج إلى 8 مستويات، حيث يمثل كل مستوى فصلاً دراسياً واحداً.",
                "source": "general_info",
                "chunk_type": "program_info",
                "metadata": {"category": "duration", "language": "ar"}
            }
        ]
        
        for info in general_info:
            chunk = ContextChunk(
                content=info["content"],
                source=info["source"],
                chunk_type=info["chunk_type"],
                metadata=info["metadata"]
            )
            self.chunks.append(chunk)
        
    def classify_query(self, query: str) -> QueryType:
        """Classify the type of query to optimize retrieval."""
        query_lower = query.lower()
        
        # Course prerequisite patterns
        if any(word in query_lower for word in ['prerequisite', 'متطلب', 'requires', 'يتطلب', 'before taking']):
            return QueryType.COURSE_PREREQUISITE
            
        # Academic calendar patterns  
        if any(word in query_lower for word in ['deadline', 'date', 'when', 'registration', 'exam', 'تسجيل', 'موعد', 'تاريخ']):
            return QueryType.ACADEMIC_CALENDAR
            
        # GPA/grades patterns
        if any(word in query_lower for word in ['gpa', 'grade', 'معدل', 'درجة', 'probation', 'إنذار', 'appeal', 'object', 'اعتراض']):
            return QueryType.GPA_GRADES
            
        # Withdrawal patterns
        if any(word in query_lower for word in ['withdraw', 'drop', 'انسحاب', 'حذف', 'اعتذار']):
            return QueryType.WITHDRAWAL
            
        # Course info patterns
        # Check if any specific course codes exist in the query
        if any(word in query_lower.split() for word in ['cs001', 'cs230', 'cs231', 'cs240', 'cs241', 'cs242', 'cs243', 'cs350', 'cs351', 'cs352', 'cs353', 'cs360', 'cs361', 'cs362', 'cs363', 'cs364']):
            return QueryType.COURSE_INFO
            
        # Default to GENERAL_ADVICE if no other type matches
        return QueryType.GENERAL_ADVICE
        
    def retrieve_context(self, query: str, max_chunks: int = 10, filter_metadata: Dict[str, Any] = None) -> List[ContextChunk]:
        """Retrieve most relevant context chunks for the query."""
        # Check if index or embedding model is missing
        if self.embeddings_matrix is None or not self.embeddings_model:
            # Log warning if components are missing
            logger.warning("Vector index or embedding model not available")
            return []
            
        # Classify query type
        # Determine the type of the query
        query_type = self.classify_query(query)
        
        # Encode the query string into a vector
        query_embedding = self.embeddings_model.encode([query])
        
        # Normalize query embedding
        query_norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
        query_norm[query_norm == 0] = 1
        query_embedding = query_embedding / query_norm
        
        # Search vector index (Cosine Similarity via Dot Product)
        # Calculate dot product between query and all embeddings
        # shape: (1, dim) @ (dim, num_chunks) -> (1, num_chunks)
        scores = np.dot(query_embedding, self.embeddings_matrix.T)[0]
        
        # Argpartition to get top k indices (unsorted)
        k = min(max_chunks * 2, len(scores))
        if k == 0:
            return []
            
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        
        relevant_chunks = []
        for idx in top_indices:
            score = scores[idx]
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                chunk.relevance_score = float(score)
                
                # Apply type-specific filtering
                if self._is_chunk_relevant(chunk, query_type, query):
                    # STRICT METADATA FILTERING
                    if filter_metadata:
                        match = True
                        for key, value in filter_metadata.items():
                            if chunk.metadata.get(key) != value:
                                # If mismatch, set match to False
                                match = False
                                # Break the loop
                                break
                        # If no match, skip this chunk
                        if not match:
                            continue
                            
                    relevant_chunks.append(chunk)
                    
        relevant_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_chunks[:max_chunks]
        
    def _is_chunk_relevant(self, chunk: ContextChunk, query_type: QueryType, query: str) -> bool:
        """Check if chunk is relevant for the query type."""
        # Course prerequisite queries
        if query_type == QueryType.COURSE_PREREQUISITE:
            return chunk.chunk_type in ['course_info'] or 'prerequisite' in chunk.content.lower()
            
        # Calendar queries
        if query_type == QueryType.ACADEMIC_CALENDAR:
            return chunk.chunk_type in ['calendar_event', 'deadline']
            
        # Always include high-relevance chunks
        # Return true if score is above threshold regardless of type
        return chunk.relevance_score > 0.3
        
    def get_course_prerequisites(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get specific course prerequisite information from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT course_code, course_name_en, credits, prerequisites 
            FROM course_prerequisites 
            WHERE course_code = ?
        """, (course_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'course_code': result[0],
                'course_name': result[1],
                'credits': result[2],
                'prerequisites': result[3] or 'None'
            }
        return None
        
    def build_response_context(self, query: str, filter_metadata: Dict[str, Any] = None) -> str:
        """Build comprehensive context for response generation."""
        relevant_chunks = self.retrieve_context(query, filter_metadata=filter_metadata)
        
        if not relevant_chunks:
            return "No relevant information found in University knowledge base."
            
        context_parts = []
        context_parts.append("RELEVANT UNIVERSITY INFORMATION:")
        context_parts.append("=" * 50)
        
        for i, chunk in enumerate(relevant_chunks[:5], 1):
            context_parts.append(f"\n{i}. Source: {chunk.source}")
            context_parts.append(f"   Content: {chunk.content}")
            if chunk.metadata:
                relevant_metadata = {k: v for k, v in chunk.metadata.items() 
                                   if k in ['course_code', 'event', 'category', 'status']}
                # If relevant metadata exists, add it to context
                if relevant_metadata:
                    context_parts.append(f"   Metadata: {relevant_metadata}")
            context_parts.append(f"   Relevance: {chunk.relevance_score:.3f}")
            
        # Add specific course info if query mentions course codes
        # Find all course codes in the query
        course_codes = re.findall(r'CS\d+', query.upper())
        # Iterate over found course codes
        for code in course_codes:
            course_info = self.get_course_prerequisites(code)
            # If course info exists
            if course_info:
                context_parts.append(f"\nSPECIFIC INFO for {code}:")
                context_parts.append(f"Name: {course_info['course_name']}")
                context_parts.append(f"Credits: {course_info['credits']}")
                context_parts.append(f"Prerequisites: {course_info['prerequisites']}")
                
        return "\n".join(context_parts)
        
    def _load_course_mapping(self):
        """Load course name to code mapping from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Execute SQL to select course codes and names
            cursor.execute("SELECT course_code, course_name_en, course_name_ar FROM course_prerequisites")
            rows = cursor.fetchall()
            conn.close()
            
            for code, name_en, name_ar in rows:
                # Map full English name
                if name_en:
                    # Map lowercase English name to code
                    self.course_mapping[name_en.lower()] = code
                    # Map "Senior Project 1" from "Senior Project 1 in Computer Science"
                    if "senior project" in name_en.lower():
                        match = re.search(r'(senior project \d+|senior project [iv]+)', name_en.lower())
                        # If a match is found
                        if match:
                            # Map the matched string to the code
                            self.course_mapping[match.group(1)] = code
                
                # Map Arabic name
                # Check if Arabic name exists
                if name_ar:
                    # Map lowercase Arabic name to code
                    self.course_mapping[name_ar.lower()] = code
                    
        except Exception as e:
            print(f"Error loading course mapping: {e}")

    def generate_instruction_block(self, query: str, history: List[Dict[str, str]] = None) -> str:
        """Generate instruction block for the LLM with relevant context."""
        # Enhance query with history if needed
        enhanced_query = query
        filter_metadata = {}
        
        # Dynamic mapping for course names (Enhance query for retrieval)
        query_lower = query.lower()
        for name, code in self.course_mapping.items():
            if name in query_lower:
                # Avoid duplicates if code is already in query
                if code not in enhanced_query.upper():
                    # Append the course code to the enhanced query
                    enhanced_query += f" ({code})"
        
        if history:
            # Look for course codes in recent history if current query is vague
            if len(query.split()) < 5 or "what else" in query.lower() or "tell me more" in query.lower():
                for msg in reversed(history):
                    if msg['role'] == 'user':
                        # Check for explicit course codes using regex
                        codes = re.findall(r'CS\d+', msg['content'].upper())
                        
                        # If no codes found, check for course names
                        if not codes:
                            msg_lower = msg['content'].lower()
                            for name, code in self.course_mapping.items():
                                if name in msg_lower:
                                    codes.append(code)
                                    # Break after finding the first match
                                    break
                        
                        # If codes were found
                        if codes:
                            enhanced_query = f"{query} regarding {codes[0]}"
                            # STRICT FILTERING: Only show chunks related to this course
                            # Set filter metadata to the found course code
                            filter_metadata = {"course_code": codes[0]}
                            # Break the loop as we found the context
                            break
                            
        # Check for course codes in query (or enhanced query)
        # Find all course codes in the enhanced query
        course_codes = re.findall(r'CS\d+', enhanced_query.upper())
        valid_courses = []
        invalid_courses = []
        
        # Iterate over found course codes
        for code in course_codes:
            if self.get_course_prerequisites(code):
                valid_courses.append(code)
            else:
                invalid_courses.append(code)
                
        # If query is about an invalid course, force a denial response
        if invalid_courses:
            return f"""
You are the Academic Advisor for the University.
The student asked about {', '.join(invalid_courses)}, but these are NOT valid courses in the University program.
State clearly that "{', '.join(invalid_courses)}" does not exist in the University curriculum.
Do NOT invent information.
Do NOT describe the course based on its name or number.
Simply state it is not a valid course.
"""

        context = self.build_response_context(enhanced_query, filter_metadata)
        
        # Check for brevity constraints (including typos)
        brevity_keywords = ['briefly', 'brief', 'short', 'concise', 'summarize', 'summary', 'breifly', 'breif']
        is_brief = any(word in query.lower() for word in brevity_keywords)
        
        brevity_instruction = ""
        # If brevity is requested
        if is_brief:
            brevity_instruction = "Keep your response extremely concise (maximum 3-4 sentences). Get straight to the point."

        if len(query.split()) <= 2 and is_brief and history:
            last_real_query = None
            for msg in reversed(history):
                if msg['role'] == 'user' and len(msg['content'].split()) > 2:
                    last_real_query = msg['content']
                    # Break the loop
                    break
            
            # If a previous real query was found
            if last_real_query:
                enhanced_query = f"{last_real_query} (Answer briefly)"
                # Re-run context retrieval for the original query
                # We need to re-extract course codes from the original query to ensure correct context
                # Find course codes in the last real query
                course_codes = re.findall(r'CS\d+', last_real_query.upper())
                if "senior project 1" in last_real_query.lower() or "senior project i" in last_real_query.lower():
                    course_codes.append("CS479")
                if "senior project 2" in last_real_query.lower() or "senior project ii" in last_real_query.lower():
                    course_codes.append("CS489")
                    
                # If course codes found
                if course_codes:
                     filter_metadata = {"course_code": course_codes[0]}
                
                # Re-build context with the updated query and filter
                context = self.build_response_context(enhanced_query, filter_metadata)

        # Construct the final instruction block
        instruction = f"""
You are the Academic Advisor for the University.
You must ONLY answer questions related to academic matters, courses, university policies, and student services.
If the user asks about general topics (e.g., general knowledge, jokes, food, cars, capitals, weather), politely refuse and state that you can only help with university-related inquiries.

Answer based ONLY on the provided context.
{brevity_instruction}

GUIDELINES:
1. Direct & Professional: Get straight to the answer. No filler.
2. SINGLE SOURCE OF TRUTH: Provide the details ONCE. Do NOT summarize and then list details. Do NOT list details and then summarize.
3. NO REPETITION: If you have already stated the credits/prerequisites in the response, DO NOT state them again.
4. Structure: Use bullet points for lists.
5. Context Only: If the context is missing info, say "I don't have that information in the University context."
6. No Hallucinations: Do NOT invent information.
7. Policies: Quote specific policies for attendance, grades, or rights.

Context:
{context}

Question: {enhanced_query}
"""
        return instruction

# Example usage and integration
def integrate_with_fastapi(app, rag_system: UltimateRAGSystem):
    """Integration function for FastAPI application."""
    
    @app.middleware("http")
    async def add_rag_context(request, call_next):
        request.state.rag = rag_system
        response = await call_next(request)
        return response
        
    def enhanced_send_message(chat_id: int, user_message: str):
        """Enhanced message handler with RAG context."""
        
        instruction_block = rag_system.generate_instruction_block(user_message)
        
        messages = [
            {"role": "system", "content": instruction_block},
            {"role": "user", "content": user_message}
        ]
        
        # ... (existing LLM integration code)
        
        return "Enhanced response with RAG context"

if __name__ == "__main__":
    workspace_path = Path(__file__).parent.absolute()
    rag_system = UltimateRAGSystem(workspace_path)
    
    # Test queries
    test_queries = [
