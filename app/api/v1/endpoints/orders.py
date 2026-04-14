"""
app/api/v1/endpoints/orders.py
--------------------------------
Order API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderDetailResponse
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_current_active_admin

router = APIRouter()


from sqlalchemy import func, cast, Date, String

@router.get("/analytics/revenue")
def get_revenue_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return date-wise aggregated revenue."""
    results = (
        db.query(
            cast(Order.created_at, Date).label("date"),
            func.sum(Order.total_price).label("daily_revenue")
        )
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
        .all()
    )
    return [{"date": str(r.date), "revenue": r.daily_revenue} for r in results]

@router.get("/", response_model=PaginatedResponse[OrderResponse])
def get_orders(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    segment: Optional[str] = None
):
    """List orders with pagination, sorting, and global filters."""
    query = db.query(Order).options(
        joinedload(Order.product),
        joinedload(Order.customer)
    )
    
    # ─── Global Filters ───────────────────────────────────────────────────
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    if category:
        query = query.join(Product).filter(Product.category == category)
    if segment:
        query = query.join(User, Order.customer_id == User.id).filter(User.segment == segment)
    
    # ─── Search Logic ─────────────────────────────────────────────────────
    if search:
        search_filter = f"%{search}%"
        query = query.join(Product).filter(
            (Product.name.ilike(search_filter)) | 
            (cast(Order.status, String).ilike(search_filter))
        )
        
    total = query.count()
    
    # Sorting
    sort_attr = getattr(Order, sort_by, Order.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())
        
    orders = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": orders,
        "page": (skip // limit) + 1,
        "limit": limit
    }


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new order."""
    # Find customer
    customer = db.query(User).filter(User.id == order_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Find product
    product = db.query(Product).filter(Product.id == order_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Check inventory
    if product.stock_quantity < order_in.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
        
    # Decrease stock and snapshot price
    product.stock_quantity -= order_in.quantity
    total_price = product.price * order_in.quantity
    
    db_order = Order(
        customer_id=order_in.customer_id,
        product_id=order_in.product_id,
        quantity=order_in.quantity,
        notes=order_in.notes,
        total_price=total_price,
        status=OrderStatus.PENDING
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get order by ID (with nested customer + product)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, order_in: OrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Update order status. Admin only."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order_in.status is not None:
        order.status = order_in.status
    if order_in.notes is not None:
        order.notes = order_in.notes
        
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Cancel an order and return stock. Admin only."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != OrderStatus.CANCELLED:
        order.status = OrderStatus.CANCELLED
        # Return stock
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if product:
            product.stock_quantity += order.quantity
            
    db.commit()
    return None

