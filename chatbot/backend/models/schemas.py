from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum
from datetime import datetime
from typing import Optional, List

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class SubscriptionType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"

# Auth schemas
class UserRegister(BaseModel):
    email: EmailStr
    fullname: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6, max_length=12)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 12:
            raise ValueError('Password must be between 6 and 12 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes. Please use a shorter password.')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    fullname: str
    role: UserRole
    subscription_type: Optional[SubscriptionType] = None
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class SubscriptionUpdate(BaseModel):
    subscription_type: SubscriptionType
    duration_days: int = Field(default=30, gt=0)

# Keyword schemas
class KeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=255)

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class KeywordListResponse(BaseModel):
    keywords: List[KeywordResponse]
    count: int
    limit: Optional[int] = None

# Thread schemas
class ThreadResponse(BaseModel):
    id: int
    title: str
    date: datetime
    created_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True

class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
    total: int

# Message schemas
class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    meta_data: Optional[dict] = Field(None, serialization_alias="metadata")
    created_at: datetime
    
    class Config:
        from_attributes = True

class ThreadDetailResponse(BaseModel):
    id: int
    title: str
    date: datetime
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True

# Query schemas
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)

class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    message_id: int
