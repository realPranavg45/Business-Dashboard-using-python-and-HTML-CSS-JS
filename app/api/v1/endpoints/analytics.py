from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.db.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/insights")
def get_dashboard_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Phase 4 & 6: The Analytics and Intelligence Engine.
    Executes complex native SQL queries to generate raw insights and human-readable alerts.
    """
    alerts = []
    
    # 1. Top Customers by Revenue (Complex Group By & Join)
    # SELECT users.full_name, sum(orders.total_price) as spent FROM ... GROUP BY users.id ORDER BY spent DESC LIMIT 3
    top_customers_query = (
        db.query(User.full_name, func.sum(Order.total_price).label("spent"))
        .join(Order, User.id == Order.customer_id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(User.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(3)
        .all()
    )
    
    top_customers = [{"name": r.full_name, "spent": float(r.spent) if r.spent else 0} for r in top_customers_query]
    if top_customers:
        best = top_customers[0]
        alerts.append(f"🏆 Top Customer: {best['name']} has spent a total of ${best['spent']:,.2f}!")

    # 2. Top Products by Quantity Sold (Group By)
    top_products_query = (
        db.query(Product.name, func.sum(Order.quantity).label("sold"))
        .join(Order, Product.id == Order.product_id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(Product.id)
        .order_by(func.sum(Order.quantity).desc())
        .limit(3)
        .all()
    )
    
    top_products = [{"name": r.name, "sold": int(r.sold) if r.sold else 0} for r in top_products_query]
    if top_products:
        best_product = top_products[0]
        alerts.append(f"🔥 Hot Product: {best_product['name']} is flying off the shelves ({best_product['sold']} sold).")

    # 3. Stock Level Intelligence (Alerts)
    low_stock_products = db.query(Product).filter(Product.stock_quantity <= 20).all()
    if low_stock_products:
        alerts.append(f"⚠️ Critical Stock Alert: {len(low_stock_products)} product(s) have critically low inventory (< 20 units). Restock recommended.")
    
    # Return fully aggregated analytics JSON
    return {
        "text_alerts": alerts,
        "top_customers": top_customers,
        "top_products": top_products
    }
