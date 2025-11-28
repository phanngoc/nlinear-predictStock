from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from core.database import get_db
from core.security import hash_password, verify_password, create_access_token, get_current_user, require_admin
from models.db_models import User
from models.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, SubscriptionUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        fullname=user_data.fullname,
        password_hash=hash_password(user_data.password),
        role="user",
        subscription_type="free"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id, "role": new_user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": new_user}

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/subscription/{user_id}", response_model=UserResponse)
async def update_subscription(
    user_id: int,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot modify admin subscription")
    
    user.subscription_type = data.subscription_type.value
    if data.subscription_type.value == "premium":
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=data.duration_days)
    else:
        user.subscription_expires_at = None
    
    db.commit()
    db.refresh(user)
    return user

@router.post("/upgrade", response_model=UserResponse)
async def upgrade_to_premium(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        raise HTTPException(status_code=400, detail="Admins don't need subscription")
    
    current_user.subscription_type = "premium"
    current_user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    db.refresh(current_user)
    return current_user
