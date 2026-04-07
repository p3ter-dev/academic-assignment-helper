# Academic Assignment Helper

An AI-powered Enterprise platform that helps educational systems analyze assignment submissions, detect plagiarism at a foundational semantic level, and append contextually relevant academic resources using **Retrieval-Augmented Generation (RAG)**.

This ecosystem is fully containerized with **Docker**, built purely on **FastAPI**, structured natively in **PostgreSQL (pgvector)**, and leverages Google's **Gemini embeddings** accompanied by powerful visual **n8n** automation nodes.

---

## Core Features
- **Semantic Plagiarism Engine:** Uses Google's `gemini-embedding-001` (3072-dimensional arrays) and `pgvector` to run exact cosine-distance correlation algorithms natively inside the database. Identifies conceptual plagiarism instantly where simple keyword matching fails.
- **RAG Microservice:** Contains a standalone RAG sequence executing `gemini-1.5-flash` natively against a custom dataset of research material. Automatically analyzes incoming assignments to append accurate citations back to the student.
- **Async Automation (n8n):** Includes pre-built automation nodes ready to accept local webhooks. As an assignment finishes plagiarism validation, n8n grabs the finalized dataset to optionally trigger emails, Discord bots, and analytics dashboards.
- **Microservices Deployment:** Separates traffic correctly amongst a Python backend, isolated Python RAG engine, Postgres database, and external nodes.

---

## Tech Stack
- **API Interfaces:** FastAPI (Automated Swagger Docs)
- **Vector Database:** PostgreSQL v15 + `pgvector`
- **AI Tooling:** Google Gemini Generative AI Python SDK 
- **Automations:** n8n Workflow platform
- **Authentication:** OAuth2 JWT standard encryption

---

## Setup & Deployment

> [!IMPORTANT]
> Because this heavily involves internal Docker networks and routing variables, you must utilize the `docker-compose` ecosystem. Running `FastAPI` standalone without local postgres/n8n services running will trigger database dropouts.

1. **Clone & Configure:**
```bash
git clone https://github.com/p3ter-dev/academic-assignment-helper.git
cd academic-assignment-helper
cp .env.example .env
```
*(Ensure you modify `.env` and paste your actual `GEMINI_API_KEY` into the file.)*

2. **Boot the Cluster:**
```bash
docker compose up -d --build
```
This triggers the following internal addresses natively:
- `http://localhost:8000` → Primary FastAPI REST backend
- `http://localhost:8001` → Independent RAG service engine
- `http://localhost:5678` → n8n Graphical dashboard
- `localhost:5432` → Postgres Data volume

---

## API Usage & Interactive Steps

We strongly recommend opening the visual Swagger interfaces shipped natively with this architecture, allowing you to hit endpoints directly in your browser without utilizing `cURL`. 

### 1. Boot up the Knowledge Base
Run the internal `rag_service` payload once to convert all sample research files into 3072-dimension tensors in Postgres.
```bash
curl -X POST http://localhost:8001/rag/embed-sources
```

### 2. Standard API Submission Flow
**A.** Register a Student Target
```json
// POST http://localhost:8000/auth/register
{
  "full_name": "Test Student",
  "email": "student@example.com",
  "password": "password123"
}
```

**B.** Capture your authentication Token
```json
// POST http://localhost:8000/auth/login
{
  "email": "student@example.com",
  "password": "password123"
}
```
*(You will receive an `"access_token"`, which you inject as an HTTP Bearer header.)*

**C.** Execute Plagiarism Logic
```json
// POST http://localhost:8000/assignments/submit
// Headers: Authorization: Bearer <token>
{
  "text": "Machine learning algorithms improve automatically through experience. Supervised learning involves training a model on labeled data...",
  "topic": "Computer Science Intro"
}
```
> [!TIP]
> The backend automatically intercepts this submission, vectors it, tests it for plagiarism, calls the RAG service, creates study suggestions, saves it, and silently fires an HTTP Payload sequence to **n8n** all in 1.4 seconds.

---

## n8n Automation Bridge

The n8n layer operates entirely independently and listens passively to Webhooks.

1. Open **http://localhost:5678** in your browser.
2. Under "Workflows", import the local file `workflows/assignment_analysis_workflow.json`.
3. Activate the module. Every time the FastApi backend identifies an assignment has successfully completed plagiarism parsing, it shoots the metrics here automatically.
