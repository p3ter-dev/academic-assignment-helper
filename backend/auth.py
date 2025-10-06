from fastapi import APIRouter, HTTPException, Depends
from passlib.hash import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Student
from .database import get_db
import os

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "secret")
ALGORITHM = "HS256"

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

@router.post("/auth/register")
def register(email: str, password: str, full_name: str, db: Session = Depends(get_db)):
    hashed = bcrypt.hash(password)
    student = Student(email=email, password_hash=hashed, full_name=full_name)
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"msg": "Student registered successfully"}

@router.post("/auth/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email==email).first()
    if not student or not bcrypt.verify(password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"student_id": student.id, "email": student.email, "role": "student"})
    return {"access_token": token}
