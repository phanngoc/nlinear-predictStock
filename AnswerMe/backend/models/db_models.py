from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    fullname = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    subscription_type = Column(String(50), default="free")
    subscription_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    keywords = relationship("Keyword", back_populates="user", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="user", cascade="all, delete-orphan")

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="keywords")
    
    __table_args__ = (UniqueConstraint("user_id", "keyword", name="uq_user_keyword"),)

class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    thread = relationship("Thread", back_populates="messages")
