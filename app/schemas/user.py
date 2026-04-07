"""
app/schemas/user.py
-------------------
Pydantic schemas for the User entity.

WHY Pydantic / WHY separate schemas from models?
- ORM models (SQLAlchemy) describe the DATABASE structure.
- Pydantic schemas describe the API contract (what comes IN, what goes OUT).
- Keeping them separate prevents accidental data leaks (e.g., hashed_password
  must NEVER appear in an API response — UserResponse excludes it by design).

Schema breakdown:
- UserBase      : Shared fields between create/update
- UserCreate    : Input schema for POST /users (includes raw password)
- UserUpdate    : Input for PATCH /users/{id} (all optional)
- UserResponse  : Output schema — safe to return to the client
- UserInDB      : Internal schema including hashed_password (never sent to client)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ─── Base ─────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="john@example.com")


# ─── Create ───────────────────────────────────────────────────────────────────
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="Str0ngP@ssword")


# ─── Update (all optional for PATCH semantics) ────────────────────────────────
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


# ─── Response (safe to return to client) ──────────────────────────────────────
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Allows ORM model -> Pydantic auto-conversion


# ─── Internal ─────────────────────────────────────────────────────────────────
class UserInDB(UserResponse):
    hashed_password: str  # Used internally, NEVER returned by any endpoint
