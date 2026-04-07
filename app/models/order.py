"""
app/models/order.py
-------------------
SQLAlchemy ORM model for the Order entity.

Design decisions:
- `OrderStatus` Enum — Using an enum for status is safer than free-text strings.
  It prevents invalid values (e.g., "shiped" typos) at the application layer.
- Foreign keys to both User and Product — This is the classic many-to-many bridge
  (simplified here: one order = one product line, which is fine for a portfolio project).
- `total_price` is stored, not calculated dynamically — WHY: product price can change
  over time, so we snapshot it at order creation. This is standard in e-commerce.
"""
import enum
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class OrderStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    SHIPPED   = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id          = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity    = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)  # Snapshot of price at time of order
    status      = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    notes       = Column(String(500), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships for easy nav: order.customer.email, order.product.name
    customer = relationship("User",    back_populates="orders")
    product  = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<Order id={self.id} customer_id={self.customer_id} status={self.status}>"
