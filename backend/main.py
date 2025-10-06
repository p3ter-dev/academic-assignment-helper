from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Student
from auth import router as auth_router, get_current_student

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Academic Helper API")

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
