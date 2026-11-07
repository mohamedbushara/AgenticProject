from database import Base
from sqlalchemy import Column, Integer, String


class User(Base):
  __tablename__ = "Users"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  username = Column(String(100), unique=True, index=True, nullable=False)
  email = Column(String(255), unique=True, index=True, nullable=False)
  phone = Column(String(50), nullable=True)
  password = Column(String(255), nullable=False)