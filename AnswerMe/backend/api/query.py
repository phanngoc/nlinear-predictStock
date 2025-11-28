from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from core.database import get_db
from core.security import get_current_user
from models.db_models import User, Thread, Message
from models.schemas import QueryRequest, QueryResponse
from services.llama_service import llama_service

router = APIRouter(prefix="/api/threads", tags=["query"])

# Simple in-memory rate limiting (use Redis in production)
query_counts: dict = {}

def check_rate_limit(user: User):
    if user.role == "admin" or user.subscription_type == "premium":
        return
    
    today = datetime.utcnow().date().isoformat()
    key = f"{user.id}:{today}"
    count = query_counts.get(key, 0)
    
    if count >= 10:
        raise HTTPException(
            status_code=429,
            detail="Daily query limit reached (10/day). Upgrade to premium for unlimited queries."
        )

def increment_query_count(user: User):
    if user.role == "admin" or user.subscription_type == "premium":
        return
    
    today = datetime.utcnow().date().isoformat()
    key = f"{user.id}:{today}"
    query_counts[key] = query_counts.get(key, 0) + 1

@router.post("/{thread_id}/query", response_model=QueryResponse)
async def query_thread(
    thread_id: int,
    data: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate thread ownership
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check rate limit
    check_rate_limit(current_user)
    
    # Load documents for thread's date
    date_str = thread.date.strftime("%Y年%m月%d日")
    try:
        llama_service.load_documents(date_str)
    except FileNotFoundError:
        date_str = thread.date.strftime("%Y-%m-%d")
        try:
            llama_service.load_documents(date_str)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="News data not available for this date")
    
    # Save user message
    user_msg = Message(thread_id=thread.id, role="user", content=data.question)
    db.add(user_msg)
    db.flush()
    
    # Query LlamaIndex
    try:
        answer = llama_service.query(data.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying: {str(e)}")
    
    # Save assistant response
    assistant_msg = Message(
        thread_id=thread.id,
        role="assistant",
        content=answer,
        metadata={"sources": []}
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    # Increment rate limit counter
    increment_query_count(current_user)
    
    return {"answer": answer, "sources": [], "message_id": assistant_msg.id}
