from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from core.database import get_db
from core.security import get_current_user
from models.db_models import User, Thread, Message
from models.schemas import QueryRequest, QueryResponse
from services.llama_service import llama_service
from scripts.check_and_crawl import check_and_crawl

router = APIRouter(prefix="/api/query", tags=["query"])

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

@router.post("/{thread_id}", response_model=QueryResponse)
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
    
    # Kiểm tra và crawl nếu cần (chỉ cho ngày hôm nay)
    from datetime import date
    today = datetime.now().date()
    if thread.date == today:
        try:
            crawl_result = check_and_crawl()
            if crawl_result["status"] == "error":
                print(f"⚠️ Cảnh báo: {crawl_result['message']}")
        except Exception as e:
            print(f"⚠️ Lỗi khi kiểm tra/crawl: {e}")
    
    # Load documents for thread's date
    # Thử format mới trước: {YYYY}năm{MM}tháng{DD}ngày
    date_str = thread.date.strftime("%Ynăm%mtháng%dngày")
    try:
        llama_service.load_documents(date_str)
    except FileNotFoundError:
        # Thử format cũ: {YYYY}年{MM}月{DD}日
        date_str = thread.date.strftime("%Y年%m月%d日")
        try:
            llama_service.load_documents(date_str)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="News data not available for this date")
    
    # Save user message
    user_msg = Message(thread_id=thread.id, role="user", content=data.question)
    db.add(user_msg)
    db.flush()
    
    # Chat với LlamaIndex (có conversation history)
    try:
        answer = llama_service.chat(thread_id, data.question, date_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying: {str(e)}")
    
    # Save assistant response
    assistant_msg = Message(
        thread_id=thread.id,
        role="assistant",
        content=answer,
        meta_data={"sources": []}
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    # Xóa cache chat engine sau khi lưu message để đảm bảo history được cập nhật lần sau
    llama_service.clear_chat_engine_cache(thread_id)
    
    # Increment rate limit counter
    increment_query_count(current_user)
    
    return {"answer": answer, "sources": [], "message_id": assistant_msg.id}
