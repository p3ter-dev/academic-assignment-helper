# Academic Assignment Helper

An AI-powered platform that helps students analyze assignments, detect plagiarism, and get contextually relevant academic resources using **Retrieval-Augmented Generation (RAG)**.  
Built with **FastAPI**, **PostgreSQL (pgvector)**, **n8n**, and **OpenAI**, fully containerized with **Docker**.

---

## Features
- **JWT Authentication** for secure student access  
- **RAG Service** for context-aware academic suggestions  
- **Plagiarism Detection** using vector similarity  
- **n8n Workflow Automation** for assignment analysis  
- **pgvector Integration** for semantic search  
- **Dockerized Deployment** with PostgreSQL + FastAPI + n8n  

---

## Setup

### Clone & Configure
```bash
git clone https://github.com/p3ter-dev/academic-assignment-helper
cd academic-assignment-helper
cp .env.example .env

# Run with Docker
docker compose up -d --build

# Services:

backend → FastAPI app

n8n → Workflow automation

postgres → Database

pgadmin → DB UI

# API Usage
Register Student
POST /register
{
  "full_name": "Peter Kinfe",
  "email": "peter@example.com",
  "password": "password123"
}

Submit Assignment
POST /assignments/submit
{
  "student_id": 1,
  "text": "What is photosynthesis?"
}
This triggers an n8n workflow and sends the data to the RAG service for analysis.

# n8n Workflow

Open n8n UI → http://localhost:5678

Import workflows/assignment_analysis_workflow.json

Ensure webhook path = /webhook-test/assignment

Activate workflow

# RAG Workflow

Embeds data from data/sample_academic_sources.json

Stores in PostgreSQL using pgvector

On submission:

Retrieves similar documents

Combines with query for contextual AI response

Returns suggestions + plagiarism score

# Database

students
| id | full_name | email | hashed_password |

assignments
| id | student_id | text | similarity_score |

Video Demo

 Demo 1:
https://www.loom.com/share/ec0e514e23e143c3858dc7169016a2b2?sid=f3929bbf-9f9b-42c0-add7-2aa650130d21

 Demo 2:
https://www.loom.com/share/b908889c0f2845b3b5373b8f86c33a9f?sid=eb7ea1cd-80f3-41d0-8902-e48ce1d0aa32