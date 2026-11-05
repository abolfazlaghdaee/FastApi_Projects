from db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text,DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid
from datetime import datetime








class Posts(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index =True)
    caption = Column(Text)
    url = Column(String, nullable = False)
    file_type  = Column(String, nullable = False)
    file_name = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable = False)


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key= True, index= True)
    first_name = Column(String, nullable = False)
    last_name = Column(String, nullable = False)
    user_name = Column(String, unique=True, nullable = False)
    email = Column(String, unique=True, nullable = False)
    hash_password = Column(String, nullable = False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    



class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)


    
