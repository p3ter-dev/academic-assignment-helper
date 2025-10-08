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

git clone https://github.com/p3ter-dev/academic-assignment-helper <br>
cd academic-assignment-helper <br>
cp .env.example .env

## Run with Docker

docker compose up -d --build

## Services:

backend → FastAPI <br>

n8n → Workflow automation <br>

postgres → Database <br>

pgadmin → DB UI

## API Usage
Register Student <br>
POST /register <br>
{
  "full_name": "Peter Kinfe",
  "email": "peter@example.com",
  "password": "password123"
}

Submit Assignment <br>
POST /assignments/submit
{
  "student_id": 1,
  "text": "What is photosynthesis?"
}
This triggers an n8n workflow and sends the data to the RAG service for analysis.

## n8n Workflow

Open n8n UI → http://localhost:5678 <br>

Import workflows/assignment_analysis_workflow.json <br>

Ensure webhook path = /webhook-test/assignment <br>

Activate workflow

## RAG Workflow

Embeds data from data/sample_academic_sources.json <br>

Stores in PostgreSQL using pgvector <br>

On submission: <br>

Retrieves similar documents <br>

Combines with query for contextual AI response <br>

Returns suggestions

## Database

students
| id | full_name | email | hashed_password |

assignments
| id | student_id | text | similarity_score |

## Video Demo

Demo 1:
https://www.loom.com/share/ec0e514e23e143c3858dc7169016a2b2?sid=f3929bbf-9f9b-42c0-add7-2aa650130d21

Demo 2:
https://www.loom.com/share/b908889c0f2845b3b5373b8f86c33a9f?sid=eb7ea1cd-80f3-41d0-8902-e48ce1d0aa32