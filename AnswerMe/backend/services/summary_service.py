from datetime import datetime
from sqlalchemy.orm import Session
from models.db_models import Thread, Message, Keyword
from .llama_service import llama_service

class SummaryService:
    def __init__(self, db: Session):
        self.db = db
        
    def generate_daily_summary(self, user_id: int, date: datetime):
        """Generate summary for user's keywords (on-demand)"""
        # Check if thread already exists
        existing_thread = self.db.query(Thread).filter(
            Thread.user_id == user_id,
            Thread.date == date.date()
        ).first()
        
        if existing_thread:
            return existing_thread
        
        # Get user's keywords
        keywords = self.db.query(Keyword).filter(Keyword.user_id == user_id).all()
        if not keywords:
            return None
        
        # Load documents for the date
        date_str = date.strftime("%Y年%m月%d日")
        try:
            llama_service.load_documents(date_str)
        except FileNotFoundError:
            # Try alternative date format
            date_str = date.strftime("%Y-%m-%d")
            try:
                llama_service.load_documents(date_str)
            except FileNotFoundError:
                return None
        
        # Generate summaries
        summaries = llama_service.summarize_by_keywords([k.keyword for k in keywords])
        
        # Create thread
        return self._create_thread(user_id, date, summaries)
        
    def _create_thread(self, user_id: int, date: datetime, summaries: dict):
        thread = Thread(
            user_id=user_id,
            title=f"Daily Summary - {date.strftime('%Y-%m-%d')}",
            date=date.date()
        )
        self.db.add(thread)
        self.db.flush()
        
        content = self._format_summary(summaries)
        message = Message(
            thread_id=thread.id,
            role="assistant",
            content=content,
            metadata={"summaries": summaries}
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(thread)
        return thread
        
    def _format_summary(self, summaries: dict) -> str:
        lines = ["# Daily News Summary\n"]
        for keyword, summary in summaries.items():
            lines.append(f"## {keyword}\n")
            lines.append(f"{summary}\n\n")
        return "\n".join(lines)
