# Academic Plagiarism & RAG Assistant - System Manual

This document provides a comprehensive overview of the application flow, database architecture, and step-by-step documentation on how to interact with every single microservice (Database, FastAPI Backend, Gemini RAG, and n8n).

---

## System Architecture & Workflow

The platform operates as a massive real-time event pipeline composed of containerized microservices:

1. **User Interaction:** A user interacts with the Swagger UI (`http://localhost:8000/docs`) or a custom frontend to submit an assignment submission.
2. **Plagiarism Vectorization (Backend):** Upon submission, the FastAPI backend passes the text to the Google Gemini Embeddings API to generate a `3072-dimensional` vector.
3. **Similarity Engine (Database):** The backend executes raw `pgvector` SQL cosine-distance queries against the PostgreSQL database to compare the exact semantic structure of the new text against all historical texts in the `assignments` table.
4. **Research Augmentation (RAG Service):** The backend asynchronously fires an HTTP request to the isolated **RAG Service** container on port 8001. The RAG service retrieves contextual study material from the `academic_sources` table and prompts `Gemini-1.5-Flash` to generate specific citations.
5. **Data Storing:** Plagiarism scores, matched sections, and RAG study suggestions are permanently stored in the `analysis_results` SQL table.  
6. **Background Automation (N8N):** Completing the loop, the Backend triggers an invisible HTTP network webhook ping to the **N8N** container. N8N kicks off its visual node workflow, parsing the payload, checking data branches, and theoretically sending a final email/Slack alert asynchronously.

---

## Database Access (PostgreSQL & pgvector)

The entire application state is stored locally inside your Docker instance volume using Postgres 15. Your tables include `students`, `assignments`, `analysis_results`, and `academic_sources`. 

### 1. View The Database via Terminal
You can dive directly into the SQL shell of the running database container without installing any local DB management software down:
```bash
docker exec -it academic_postgres psql -U student -d academic_helper
```
*(Type `\dt` once inside to view all tables. Type `SELECT * FROM assignments;` to see data. Type `\q` to exit.)*

### 2. View The Database via GUI (PgAdmin/DBeaver)
If you prefer a visual database viewer (like DBeaver or PgAdmin), you can connect to it on your host machine using the following credentials:
- **Host:** `localhost`
- **Port:** `5432` 
- **Database Name:** `academic_helper`
- **Username:** `student`
- **Password:** `studentpassword` *(per your configuration)*

---

## API Interaction Guide

### 1. Core Endpoints (FastAPI Backend)
Accessible visually via Swagger at: **http://localhost:8000/docs**

*   **`POST /auth/register`**: Registers a new human student in the SQL database.
*   **`POST /auth/login`**: Accepts basic JSON credentials and yields a secure JWT `access_token`. You inject this token into the Swagger "Authorize" keyhole to unlock protected endpoints.
*   **`POST /assignments/submit`**: The flagship protected route. Accepts assignment text, detects plagiarism similarity via vectors, and passes it forward to the RAG sequence. 
*   **`GET /assignments/my-assignments`**: Protected route for users to view their historical scores and generated RAG suggestions.

### 2. RAG Microservice Endpoints
Normally, this isolated service is only pinged internally by the backend, but it's bound locally for manual administration.
Accessible visually via Swagger at: **http://localhost:8001/docs**

*   **`POST /rag/embed-sources`**: Reads the local `/data/sample_academic_sources.json` file, generates context embeddings, and saves them into the SQL `academic_sources` table. You only need to run this once to populate your knowledge base!
*   **`POST /rag/query`**: Queries internal context for generative text. The main Backend triggers this automatically!

---

## N8N Automation Integrations

N8N runs your background worker logic based on visual flowchart nodes.

### 1. Accessing the Dashboard:
Open your browser to: **http://localhost:5678**
*(Login using the `N8N_BASIC_AUTH_USER` and `PASSWORD` defined in your `.env` file.)*

### 2. Setting Up The Primary Workflow:
1. Navigate to the **Workflows** panel.
2. If omitted, click **Import Sequence** and upload the file located at:
   `c:\Users\peter\academic-assignment-helper\workflows\assignment_analysis_workflow.json`
3. Inside the visual builder, you will see the **Webhook** trigger node. This node is actively listening at `http://n8n:5678/webhook/assignment-analysis`.
4. Ensure the workflow is marked as **Active** via the top right toggle.

### 3. Monitoring Results
Once the workflow is active, you don't actually interact with n8n directly! You simply submit assignments in your user-facing backend API endpoint, and your workflow will passively trigger and glow green in the n8n **Executions** tab, successfully moving semantic variables forward across external nodes.
