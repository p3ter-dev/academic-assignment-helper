from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER")
    pw = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    DATABASE_URL = f"postgresql://{user}:{pw}@{host}:{port}/{db}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# App
app = FastAPI(
    title="RAG Service",
    description="Retrieval-Augmented Generation using Gemini + pgvector for academic assistance",
    version="1.0.0",
)

# Schemas

class QueryRequest(BaseModel):
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

class EmbedSourcesResponse(BaseModel):
    message: str
    embedded_count: int

# Helpers

def embed_text(content: str, task_type: str = "RETRIEVAL_QUERY") -> list:
    """Embed text using Gemini gemini-embedding-001 (768 dimensions)."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=content,
        task_type=task_type,
    )
    return result["embedding"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Routes

@app.get("/", tags=["Health"])
def home():
    return {"message": "RAG Service is online!", "model": "gemini-1.5-flash + text-embedding-004"}


@app.post("/rag/query", response_model=RAGResponse, tags=["RAG"])
def rag_query(request: QueryRequest):
    """
    Full RAG pipeline:
    1. Embed the query with Gemini text-embedding-004.
    2. Retrieve top-k most similar academic sources from pgvector.
    3. Build a context-enriched prompt.
    4. Generate answer with Gemini 1.5 Flash.
    5. Return answer + source metadata.
    """
    db = SessionLocal()
    try:
        # Step 1: Embed query
        try:
            query_embedding = embed_text(request.query, task_type="RETRIEVAL_QUERY")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

        top_k = min(request.top_k or 5, 10)

        # Step 2: Retrieve top-k sources using pgvector cosine similarity
        rows = db.execute(
            text(
                """
                SELECT title, authors, publication_year, source_type, abstract, full_text,
                       1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                FROM academic_sources
                WHERE embedding IS NOT NULL
                ORDER BY similarity DESC
                LIMIT :k
                """
            ),
            {"emb": str(query_embedding), "k": top_k},
        ).fetchall()

        sources = []
        context_parts = []

        for row in rows:
            sim = float(row.similarity)
            sources.append(
                SourceResult(
                    title=row.title or "Unknown",
                    authors=row.authors,
                    publication_year=row.publication_year,
                    source_type=row.source_type,
                    similarity=round(sim, 4),
                )
            )
            # Build context from abstract + full_text
            source_text = row.abstract or ""
            if row.full_text:
                source_text += "\n" + row.full_text
            context_parts.append(
                f"[Source: {row.title} ({row.publication_year})]\n{source_text}"
            )

        # Step 3: Build prompt with retrieved context
        if context_parts:
            context = "\n\n---\n\n".join(context_parts)
            prompt = (
                f"You are an expert academic assistant helping a student with their research.\n\n"
                f"Based on the following academic sources, provide a comprehensive and accurate answer "
                f"to the student's question. Cite the sources where relevant.\n\n"
                f"=== ACADEMIC SOURCES ===\n{context}\n\n"
                f"=== STUDENT QUESTION ===\n{request.query}\n\n"
                f"=== YOUR ANSWER ===\n"
            )
        else:
            prompt = (
                f"You are an expert academic assistant. Answer the following question thoroughly: "
                f"\n\n{request.query}"
            )

        # Step 4: Generate answer with Gemini 1.5 Flash
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini generation failed: {e}")

        return RAGResponse(answer=answer, sources=sources)

    finally:
        db.close()


@app.post("/rag/embed-sources", response_model=EmbedSourcesResponse, tags=["Admin"])
def embed_academic_sources():
    """
    Seed and embed academic sources from data/sample_academic_sources.json.
    Reads the JSON file, generates Gemini embeddings for each source, and upserts into the DB.
    Call this once after initial setup (or whenever you add new sources).
    """
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_academic_sources.json")

    if not os.path.exists(data_path):
        raise HTTPException(status_code=404, detail=f"Data file not found at {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        sources = json.load(f)

    db = SessionLocal()
    embedded_count = 0

    try:
        for source in sources:
            # Build text to embed: title + abstract
            embed_content = f"{source.get('title', '')}. {source.get('abstract', '')}"
            try:
                embedding = embed_text(embed_content, task_type="RETRIEVAL_DOCUMENT")
            except Exception as e:
                continue  # skip if embedding fails for a source

            # Upsert by title
            existing = db.execute(
                text("SELECT id FROM academic_sources WHERE title = :title"),
                {"title": source.get("title")},
            ).fetchone()

            if existing:
                db.execute(
                    text(
                        """
                        UPDATE academic_sources
                        SET authors=:authors, publication_year=:year, abstract=:abstract,
                            full_text=:full_text, source_type=:source_type,
                            embedding=CAST(:emb AS vector)
                        WHERE title=:title
                        """
                    ),
                    {
                        "title": source.get("title"),
                        "authors": source.get("authors"),
                        "year": source.get("publication_year"),
                        "abstract": source.get("abstract"),
                        "full_text": source.get("full_text"),
                        "source_type": source.get("source_type"),
                        "emb": str(embedding),
                    },
                )
            else:
                db.execute(
                    text(
                        """
                        INSERT INTO academic_sources
                            (title, authors, publication_year, abstract, full_text, source_type, embedding)
                        VALUES
                            (:title, :authors, :year, :abstract, :full_text, :source_type, CAST(:emb AS vector))
                        """
                    ),
                    {
                        "title": source.get("title"),
                        "authors": source.get("authors"),
                        "year": source.get("publication_year"),
                        "abstract": source.get("abstract"),
                        "full_text": source.get("full_text"),
                        "source_type": source.get("source_type"),
                        "emb": str(embedding),
                    },
                )

            embedded_count += 1

        db.commit()
    finally:
        db.close()

    return EmbedSourcesResponse(
        message=f"Successfully embedded and stored {embedded_count} academic sources.",
        embedded_count=embedded_count,
    )
