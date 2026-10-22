from pydantic import BaseModel, EmailStr

from app.modules.auth.models import UserRole


class CitizenRegisterInput(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    zone_sector: str = "Rimac Centro"


class LoginInput(BaseModel):
    email: EmailStr
    password: str
    expected_role: UserRole


class CitizenRegisterOutput(BaseModel):
    id: int
    full_name: str
    role: UserRole
    sector: str


class LoginOutput(BaseModel):
    user_id: int
    full_name: str
    role: UserRole
    eco_points: int
