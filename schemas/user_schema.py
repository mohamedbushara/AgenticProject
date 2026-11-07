from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
  username: str
  email: EmailStr
  phone: Optional[str] = None
  password: str
  confirm_password: str


class UserLogin(BaseModel):
  username: str
  password: str