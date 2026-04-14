"""
app/models/user.py
------------------
SQLAlchemy ORM model for the User entity.

WHY: ORM models define your database table structure in Python. SQLAlchemy
maps these classes to actual SQL tables. Using ORM means no raw SQL for CRUD —
it's safer (prevents SQL injection) and more maintainable.

Design decisions:
- `hashed_password` — NEVER store plain-text passwords. We hash them before saving.
- `is_active` — Soft-delete pattern: instead of deleting rows (which breaks FKs),
  we mark users inactive. This preserves audit history.
- `created_at` with `server_default` — DB-level default is more reliable than app-level.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    is_admin        = Column(Boolean, default=False, nullable=False)
    segment         = Column(String(50), default="Individual", index=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: one user can have many orders
    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"

