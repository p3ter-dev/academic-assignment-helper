-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    student_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assignments table with embedding vector (3072-dim for Gemini)
CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    filename VARCHAR(255),
    original_text TEXT NOT NULL,
    topic VARCHAR(255),
    academic_level VARCHAR(100),
    word_count INTEGER,
    embedding vector(3072),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id),
    suggested_sources JSONB,
    plagiarism_score FLOAT,
    flagged_sections JSONB,
    research_suggestions TEXT,
    citation_recommendations TEXT,
    confidence_score FLOAT,
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- Academic sources table with embedding vector (3072-dim for Gemini)
CREATE TABLE IF NOT EXISTS academic_sources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    authors VARCHAR(500),
    publication_year INTEGER,
    abstract TEXT,
    full_text TEXT,
    source_type VARCHAR(100),
    embedding vector(3072)
);


