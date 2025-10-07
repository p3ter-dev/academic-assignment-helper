from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Student
from auth import router as auth_router, get_current_student
import requests
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Helper API")

app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/me")
def read_my_profile(current_student: Student = Depends(get_current_student)):
    return {
        "id": current_student.id,
        "full_name": current_student.full_name,
        "email": current_student.email
    }

@app.get('/')
def root():
    return {"msg": "rag service is online"}

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

@app.post("/assignments/submit")
def submit_assignment(student_id: int, text: str, db: Session = Depends(get_db)):
    payload = {"student_id": student_id, "text": text}

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            auth=(
                os.getenv("N8N_BASIC_AUTH_USER"),
                os.getenv("N8N_BASIC_AUTH_PASSWORD"),
            ),
        )
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger n8n: {e}")

    return {"message": "Assignment submitted and sent to n8n"}