from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.security import get_current_user, check_keyword_limit
from models.db_models import User, Keyword
from models.schemas import KeywordCreate, KeywordResponse, KeywordListResponse

router = APIRouter(prefix="/api/keywords", tags=["keywords"])

@router.post("", response_model=KeywordResponse)
async def add_keyword(
    data: KeywordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_keyword_limit(current_user, db)
    
    existing = db.query(Keyword).filter(
        Keyword.user_id == current_user.id,
        Keyword.keyword == data.keyword
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    
    keyword = Keyword(user_id=current_user.id, keyword=data.keyword)
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword

@router.get("", response_model=KeywordListResponse)
async def get_keywords(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keywords = db.query(Keyword).filter(Keyword.user_id == current_user.id).all()
    limit = None if current_user.role == "admin" or current_user.subscription_type == "premium" else 5
    return {"keywords": keywords, "count": len(keywords), "limit": limit}

@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keyword = db.query(Keyword).filter(
        Keyword.id == keyword_id,
        Keyword.user_id == current_user.id
    ).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    db.delete(keyword)
    db.commit()
    return {"message": "Keyword deleted"}
