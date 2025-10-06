from pydantic import BaseModel, EmailStr

class StudentRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
