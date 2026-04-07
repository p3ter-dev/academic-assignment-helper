from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal, engine
from models import Base, Student, Assignment, AnalysisResult, AcademicSource
from auth import router as auth_router, get_current_student
from schemas import AssignmentSubmit, AssignmentOut, PlagiarismResult, FlaggedMatch
import google.generativeai as genai
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

PLAGIARISM_THRESHOLD = 0.85  # cosine similarity threshold to flag as plagiarism
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag_service:8001")

# App setup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Academic Assignment Helper API",
    description="AI-powered plagiarism detection and academic resource recommendations using Gemini + pgvector",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helpers

def embed_text(text: str) -> list[float]:
    """Embed text using Gemini gemini-embedding-001 (768 dimensions)."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="RETRIEVAL_DOCUMENT",
    )
    return result["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Routes

@app.get("/", tags=["Health"])
def root():
    return {"message": "Academic Assignment Helper API is online", "version": "1.0.0"}


@app.get("/me", tags=["Students"])
def read_my_profile(current_student: Student = Depends(get_current_student)):
    return {
        "id": current_student.id,
        "full_name": current_student.full_name,
        "email": current_student.email,
    }


@app.post("/assignments/submit", response_model=PlagiarismResult, tags=["Assignments"])
def submit_assignment(
    payload: AssignmentSubmit,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    Submit an assignment for plagiarism detection.
    1. Embed the text with Gemini.
    2. Save assignment to DB.
    3. Compare embedding against all existing assignments using pgvector cosine similarity.
    4. Store analysis result.
    5. Trigger n8n workflow (fire-and-forget).
    6. Return plagiarism score + flagged matches.
    """
    assignment_text = payload.text.strip()
    if not assignment_text:
        raise HTTPException(status_code=400, detail="Assignment text cannot be empty.")

    # Step 1: Generate embedding
    try:
        embedding = embed_text(assignment_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    word_count = len(assignment_text.split())

    # Step 2: Save assignment to DB
    assignment = Assignment(
        student_id=current_student.id,
        original_text=assignment_text,
        topic=payload.topic,
        academic_level=payload.academic_level,
        filename=payload.filename,
        word_count=word_count,
        embedding=embedding,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Step 3: Compare against all OTHER assignments using pgvector
    # Use raw SQL for vector cosine distance (1 - cosine_distance = cosine_similarity)
    similarity_rows = db.execute(
        text(
            """
            SELECT id, original_text,
                   1 - (embedding <=> CAST(:emb AS vector)) AS similarity
            FROM assignments
            WHERE id != :aid
            ORDER BY similarity DESC
            LIMIT 10
            """
        ),
        {"emb": str(embedding), "aid": assignment.id},
    ).fetchall()

    flagged_matches = []
    max_similarity = 0.0

    for row in similarity_rows:
        sim = float(row.similarity)
        if sim > max_similarity:
            max_similarity = sim
        if sim >= PLAGIARISM_THRESHOLD:
            flagged_matches.append(
                FlaggedMatch(
                    assignment_id=row.id,
                    similarity_score=round(sim, 4),
                    text_preview=row.original_text[:200] + "..." if len(row.original_text) > 200 else row.original_text,
                )
            )

    plagiarism_score = round(max_similarity, 4)
    is_plagiarized = plagiarism_score >= PLAGIARISM_THRESHOLD

    # Step 4: Get RAG suggestions from rag_service
    rag_suggestions = None
    try:
        rag_resp = requests.post(
            f"{RAG_SERVICE_URL}/rag/query",
            json={"query": assignment_text},
            timeout=30,
        )
        if rag_resp.status_code == 200:
            rag_suggestions = rag_resp.json().get("answer")
    except Exception:
        rag_suggestions = "RAG service unavailable."

    # Step 5: Store analysis result
    analysis = AnalysisResult(
        assignment_id=assignment.id,
        plagiarism_score=plagiarism_score,
        flagged_sections=json.dumps([f.dict() for f in flagged_matches]),
        research_suggestions=rag_suggestions,
        confidence_score=1.0,
    )
    db.add(analysis)
    db.commit()

    # Step 6: Fire-and-forget n8n webhook
    if N8N_WEBHOOK_URL:
        try:
            requests.post(
                N8N_WEBHOOK_URL,
                json={
                    "student_id": current_student.id,
                    "assignment_id": assignment.id,
                    "text": assignment_text[:500],
                    "plagiarism_score": plagiarism_score,
                    "is_plagiarized": is_plagiarized,
                },
                auth=(
                    os.getenv("N8N_BASIC_AUTH_USER"),
                    os.getenv("N8N_BASIC_AUTH_PASSWORD"),
                ),
                timeout=5,
            )
        except Exception:
            pass  # Don't fail the request if n8n is down

    return PlagiarismResult(
        assignment_id=assignment.id,
        plagiarism_score=plagiarism_score,
        is_plagiarized=is_plagiarized,
        flagged_matches=flagged_matches,
        rag_suggestions=rag_suggestions,
    )


@app.get("/assignments/", response_model=list[AssignmentOut], tags=["Assignments"])
def list_my_assignments(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """List all assignments submitted by the authenticated student."""
    assignments = (
        db.query(Assignment)
        .filter(Assignment.student_id == current_student.id)
        .order_by(Assignment.uploaded_at.desc())
        .all()
    )
    return assignments


@app.get("/assignments/{assignment_id}/plagiarism", tags=["Assignments"])
def get_plagiarism_result(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Get the stored plagiarism analysis result for a specific assignment."""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.student_id == current_student.id,
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    result = db.query(AnalysisResult).filter(
        AnalysisResult.assignment_id == assignment_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="No analysis result found for this assignment.")

    return {
        "assignment_id": assignment_id,
        "plagiarism_score": result.plagiarism_score,
        "is_plagiarized": result.plagiarism_score >= PLAGIARISM_THRESHOLD if result.plagiarism_score else False,
        "flagged_sections": result.flagged_sections,
        "research_suggestions": result.research_suggestions,
        "citation_recommendations": result.citation_recommendations,
        "confidence_score": result.confidence_score,
        "analyzed_at": result.analyzed_at,
    }