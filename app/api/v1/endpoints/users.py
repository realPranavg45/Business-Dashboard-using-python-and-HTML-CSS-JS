"""
app/api/v1/endpoints/users.py
------------------------------
User API endpoints for CRUD operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_current_active_admin
from app.core.security import get_password_hash
from sqlalchemy import cast, String

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user

@router.get("/", response_model=PaginatedResponse[UserResponse])
def get_users(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    sort_by: str = "id",
    sort_order: str = "desc",
    segment: Optional[str] = None
):
    """List users with pagination, search, and segment filtering."""
    query = db.query(User).filter(User.is_active == True)
    
    if segment:
        query = query.filter(User.segment == segment)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_filter)) | 
            (User.email.ilike(search_filter))
        )
        
    total = query.count()
    
    # Sorting
    sort_attr = getattr(User, sort_by, User.id)
    if sort_order == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())
        
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": users,
        "page": (skip // limit) + 1,
        "limit": limit
    }


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Create a new user."""
    # Check if email exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    # We actively hash the password here using passlib
    user_data = user_in.model_dump()
    password = user_data.pop("password")
    hashed_pass = get_password_hash(password)
    db_user = User(**user_data, hashed_password=hashed_pass)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Update user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(user, "hashed_password", get_password_hash(value))
            continue
        setattr(user, field, value)
        
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Deactivate user by ID (soft delete)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = False
    db.commit()
    return None

