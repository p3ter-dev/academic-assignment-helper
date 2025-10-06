from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import Student
from database import get_db
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from schemas import StudentRegister, StudentLogin, TokenResponse

load_dotenv()

router = APIRouter()

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decode JWT token and fetch the student from DB.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("student_id")
        if student_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise credentials_exception
    return student

@router.post("/auth/register", response_model=dict)
def register(student: StudentRegister, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(student.password)
    new_student = Student(email=student.email, password_hash=hashed, full_name=student.full_name)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"msg": "Student registered successfully"}

@router.post("/auth/login", response_model=TokenResponse)
def login(student: StudentLogin, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if not db_student or not verify_password(student.password, db_student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "student_id": db_student.id,
        "email": db_student.email,
        "role": "student"
    })
    return {"access_token": token}