"""
app/schemas/order.py
--------------------
Pydantic schemas for the Order entity.

Design decisions:
- `OrderCreate` takes `customer_id` and `product_id` as input (the API consumer
  provides these IDs, not the full nested objects).
- `OrderResponse` returns nested `customer` and `product` objects (enriched data
  is more useful to the consumer than raw IDs — this is standard REST design).
- The enum is imported from the model to keep the source of truth in one place.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.order import OrderStatus  # Reuse the same enum
from app.schemas.user import UserResponse
from app.schemas.product import ProductResponse


# ─── Create ───────────────────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    customer_id: int = Field(..., gt=0, example=1)
    product_id: int = Field(..., gt=0, example=3)
    quantity: int = Field(1, gt=0, example=2)
    notes: Optional[str] = Field(None, max_length=500, example="Leave at door")


# ─── Update ───────────────────────────────────────────────────────────────────
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = Field(None, max_length=500)


# ─── Response (summary — no nested objects) ───────────────────────────────────
class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_id: int
    quantity: int
    total_price: float
    status: OrderStatus
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Detailed Response (with nested objects, for GET /orders/{id}) ────────────
class OrderDetailResponse(OrderResponse):
    customer: UserResponse
    product: ProductResponse
