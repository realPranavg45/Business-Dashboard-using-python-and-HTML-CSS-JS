"""
app/schemas/product.py
----------------------
Pydantic schemas for the Product entity.

WHY: Same separation principle as User schemas.
- Validators enforce business rules (price > 0, stock >= 0) at the API layer
  BEFORE the data hits the database. This is "fail fast" design — better to
  return a 422 error immediately than a DB constraint error later.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Base ─────────────────────────────────────────────────────────────────────
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, example="Wireless Mouse")
    description: Optional[str] = Field(None, example="Ergonomic wireless mouse with USB receiver")
    price: float = Field(..., gt=0, example=29.99)  # gt=0: must be greater than 0
    stock_quantity: int = Field(0, ge=0, example=100)  # ge=0: must be >= 0
    category: Optional[str] = Field(None, max_length=100, example="Electronics")
    sku: Optional[str] = Field(None, max_length=100, example="WM-001-BLK")


# ─── Create ───────────────────────────────────────────────────────────────────
class ProductCreate(ProductBase):
    pass  # Inherits everything from base — no extra fields needed on create


# ─── Update (PATCH: all optional) ─────────────────────────────────────────────
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    sku: Optional[str] = None
    is_active: Optional[bool] = None


# ─── Response ─────────────────────────────────────────────────────────────────
class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
