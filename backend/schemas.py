from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth

class StudentRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StudentOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

# Assignments

class AssignmentSubmit(BaseModel):
    text: str
    topic: Optional[str] = None
    academic_level: Optional[str] = None
    filename: Optional[str] = None

class FlaggedMatch(BaseModel):
    assignment_id: int
    similarity_score: float
    text_preview: str

class PlagiarismResult(BaseModel):
    assignment_id: int
    plagiarism_score: float           # highest similarity found (0.0–1.0)
    is_plagiarized: bool              # True if score >= threshold
    flagged_matches: List[FlaggedMatch]
    rag_suggestions: Optional[str]    # context-aware suggestions from RAG

class AssignmentOut(BaseModel):
    id: int
    student_id: int
    original_text: str
    topic: Optional[str]
    academic_level: Optional[str]
    word_count: Optional[int]
    uploaded_at: Optional[datetime]

    class Config:
        from_attributes = True

# RAG

class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class SourceResult(BaseModel):
    title: str
    authors: Optional[str]
    publication_year: Optional[int]
    source_type: Optional[str]
    similarity: float

class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceResult]
