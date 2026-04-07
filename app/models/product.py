"""
app/models/product.py
---------------------
SQLAlchemy ORM model for the Product entity.

Design decisions:
- `stock_quantity` — Track inventory at the DB level for accurate data.
- `is_active` — Soft-delete: discontinued products should be deactivated,
  not deleted, since old Orders still reference them.
- `price` uses Float — for a production system, consider using `Numeric(10, 2)`
  (fixed-point) to avoid floating-point rounding errors in financial data.
"""
from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(200), nullable=False, index=True)
    description    = Column(Text, nullable=True)
    price          = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    category       = Column(String(100), nullable=True, index=True)
    sku            = Column(String(100), unique=True, nullable=True)  # Stock Keeping Unit
    is_active      = Column(Boolean, default=True, nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: one product appears in many order items
    order_items = relationship("Order", back_populates="product")

    def __repr__(self):
        return f"<Product id={self.id} name={self.name} price={self.price}>"
