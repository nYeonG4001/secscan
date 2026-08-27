from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthenticatedUserResponse(BaseModel):
    email: EmailStr
    role: str
