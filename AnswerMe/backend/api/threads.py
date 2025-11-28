from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from core.database import get_db
from core.security import get_current_user
from models.db_models import User, Thread, Message
from models.schemas import ThreadResponse, ThreadListResponse, ThreadDetailResponse
from services.summary_service import SummaryService

router = APIRouter(prefix="/api/threads", tags=["threads"])

@router.get("", response_model=ThreadListResponse)
async def get_threads(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Thread).filter(Thread.user_id == current_user.id)
    
    # Free users: 30-day limit
    if current_user.role != "admin" and current_user.subscription_type != "premium":
        cutoff = datetime.utcnow().date() - timedelta(days=30)
        query = query.filter(Thread.date >= cutoff)
    
    total = query.count()
    threads = query.order_by(Thread.date.desc()).offset(skip).limit(limit).all()
    
    # Add message count
    result = []
    for thread in threads:
        msg_count = db.query(Message).filter(Message.thread_id == thread.id).count()
        thread_dict = {
            "id": thread.id,
            "title": thread.title,
            "date": thread.date,
            "created_at": thread.created_at,
            "message_count": msg_count
        }
        result.append(thread_dict)
    
    return {"threads": result, "total": total}

@router.get("/today", response_model=ThreadDetailResponse)
async def get_today_thread(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SummaryService(db)
    thread = service.generate_daily_summary(current_user.id, datetime.utcnow())
    
    if not thread:
        raise HTTPException(status_code=404, detail="No keywords configured or no data available")
    
    messages = db.query(Message).filter(Message.thread_id == thread.id).order_by(Message.created_at).all()
    return {"id": thread.id, "title": thread.title, "date": thread.date, "messages": messages}

@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Free users: check 30-day limit
    if current_user.role != "admin" and current_user.subscription_type != "premium":
        cutoff = datetime.utcnow().date() - timedelta(days=30)
        if thread.date < cutoff:
            raise HTTPException(status_code=403, detail="Upgrade to premium to access older threads")
    
    messages = db.query(Message).filter(Message.thread_id == thread.id).order_by(Message.created_at).all()
    return {"id": thread.id, "title": thread.title, "date": thread.date, "messages": messages}

@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    db.delete(thread)
    db.commit()
    return {"message": "Thread deleted"}
