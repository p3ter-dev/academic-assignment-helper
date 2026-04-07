FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    google-generativeai \
    psycopg2-binary \
    pgvector \
    sqlalchemy \
    python-dotenv \
    pydantic
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
