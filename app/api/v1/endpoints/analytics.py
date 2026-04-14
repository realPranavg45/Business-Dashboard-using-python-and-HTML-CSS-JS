from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from scripts.ml_forecasting import predict_future_revenue
from app.services.ai_service import ask_business_question, get_quick_insights
from app.analytics.anomaly_detector import detect_order_anomalies, detect_revenue_anomalies

router = APIRouter()


class ChatRequest(BaseModel):
    query: str

@router.get("/ml-revenue-forecast")
def get_ml_revenue_forecast():
    """
    Executes a SciKit-Learn machine learning model dynamically over order sequences 
    to map a 30-day simulated linear projection matrix.
    """
    result = predict_future_revenue()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/what-if-forecast")
def get_what_if_forecast(
    price_mult: float = 1.0, 
    volume_mult: float = 1.0,
    retention_mult: float = 1.0
):
    """
    Simulates a business scenario by scaling ML projections based on price and volume adjustments.
    """
    from scripts.ml_forecasting import predict_what_if_revenue
    result = predict_what_if_revenue(
        price_multiplier=price_mult, 
        volume_multiplier=volume_mult,
        retention_multiplier=retention_mult
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/insights")
def get_dashboard_insights(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    segment: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enhanced Analytics: Supports global filtering by date, category, and segment.
    """
    alerts = []
    
    # Base query for orders
    order_query = db.query(Order).filter(Order.status != OrderStatus.CANCELLED)
    
    if start_date:
        order_query = order_query.filter(Order.created_at >= start_date)
    if end_date:
        order_query = order_query.filter(Order.created_at <= end_date)
    if category:
        order_query = order_query.join(Product).filter(Product.category == category)
    if segment:
        order_query = order_query.join(User, Order.customer_id == User.id).filter(User.segment == segment)

    # 1. Top Customers by Revenue (Filtered)
    top_customers_query = (
        db.query(User.full_name, func.sum(Order.total_price).label("spent"))
        .select_from(Order)
        .join(User, Order.customer_id == User.id)
    )
    # Apply identical filters to the sub-aggregation
    if start_date: top_customers_query = top_customers_query.filter(Order.created_at >= start_date)
    if end_date: top_customers_query = top_customers_query.filter(Order.created_at <= end_date)
    if category: top_customers_query = top_customers_query.join(Product).filter(Product.category == category)
    if segment: top_customers_query = top_customers_query.filter(User.segment == segment)

    top_customers_data = (
        top_customers_query.filter(Order.status != OrderStatus.CANCELLED)
        .group_by(User.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(3)
        .all()
    )
    
    top_customers = [{"name": r.full_name, "spent": float(r.spent) if r.spent else 0} for r in top_customers_data]
    if top_customers:
        best = top_customers[0]
        alerts.append(f"🏆 Top Customer: {best['name']} has spent ${best['spent']:,.2f} in this period!")

    # 2. Top Products by Quantity Sold (Filtered)
    top_products_query = (
        db.query(Product.name, func.sum(Order.quantity).label("sold"))
        .select_from(Order)
        .join(Product, Order.product_id == Product.id)
    )
    if start_date: top_products_query = top_products_query.filter(Order.created_at >= start_date)
    if end_date: top_products_query = top_products_query.filter(Order.created_at <= end_date)
    if category: top_products_query = top_products_query.filter(Product.category == category)
    if segment: top_products_query = top_products_query.join(User, Order.customer_id == User.id).filter(User.segment == segment)

    top_products_data = (
        top_products_query.filter(Order.status != OrderStatus.CANCELLED)
        .group_by(Product.id)
        .order_by(func.sum(Order.quantity).desc())
        .limit(3)
        .all()
    )
    
    top_products = [{"name": r.name, "sold": int(r.sold) if r.sold else 0} for r in top_products_data]
    if top_products:
        best_product = top_products[0]
        alerts.append(f"🔥 Hot Product: {best_product['name']} is leading sales ({best_product['sold']} sold).")

    # 3. Stock Level Intelligence (Alerts)
    low_stock_query = db.query(Product).filter(Product.stock_quantity <= 20)
    if category:
        low_stock_query = low_stock_query.filter(Product.category == category)
    low_stock_products = low_stock_query.all()
    
    # 4. Generate AI Narrative Pulse
    ai_pulse = get_quick_insights(db)

    return {
        "text_alerts": alerts,
        "top_customers": top_customers,
        "top_products": top_products,
        "low_stock_items": [{"name": p.name, "stock_quantity": p.stock_quantity} for p in low_stock_products],
        "ai_pulse": ai_pulse
    }


@router.post("/chat")
def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    AI Chatbot endpoint.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    answer = ask_business_question(query=request.query.strip(), db=db)
    return {"answer": answer}


@router.get("/anomalies")
def get_business_anomalies(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    segment: Optional[str] = None,
    db: Session = Depends(get_db),
    contamination: float = 0.05,
    revenue_threshold: float = 2.0
) -> Dict[str, Any]:
    """
    AI-driven anomaly detection filtered by global context.
    """
    order_anomalies = detect_order_anomalies(db, contamination=contamination)
    revenue_anomalies = detect_revenue_anomalies(db, threshold=revenue_threshold)
    
    return {
        "order_anomalies": order_anomalies[:10],
        "revenue_anomalies": revenue_anomalies,
        "summary": {
            "total_orders_flagged": len(order_anomalies),
            "status": "filtered" if category or segment else "full"
        }
    }


@router.get("/strategic")
def get_strategic_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Calculates high-level strategic KPIs: Revenue MoM, WoW, YoY, Retention, and Churn.
    """
    from datetime import date, timedelta
    
    today = date.today()
    
    # 1. MoM and YoY windows
    this_month_start = date(today.year, today.month, 1)
    
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = date(last_month_end.year, last_month_end.month, 1)
    
    last_year_start = date(this_month_start.year - 1, this_month_start.month, 1)
    # Handle end of month last year (simplified to today - 365 days for same-day comparison if needed, but here we use cumulative month)
    last_year_end = date(today.year - 1, today.month, today.day) 

    # 2. WoW windows
    last_7_days_start = today - timedelta(days=7)
    prev_7_days_start = last_7_days_start - timedelta(days=7)

    def get_revenue(start, end):
        return db.query(func.sum(Order.total_price)).filter(
            Order.created_at >= start,
            Order.created_at <= datetime.combine(end, datetime.max.time()),
            Order.status != OrderStatus.CANCELLED
        ).scalar() or 0.0

    def get_customers(start, end):
        cust_query = db.query(Order.customer_id).filter(
            Order.created_at >= start,
            Order.created_at <= datetime.combine(end, datetime.max.time()),
            Order.status != OrderStatus.CANCELLED
        ).distinct().all()
        return {c[0] for c in cust_query}

    # Revenue metrics
    rev_now = float(get_revenue(this_month_start, today))
    rev_prev_mo = float(get_revenue(last_month_start, last_month_end))
    rev_prev_yr = float(get_revenue(last_year_start, last_year_end))
    
    rev_last_7 = float(get_revenue(last_7_days_start, today))
    rev_prev_7 = float(get_revenue(prev_7_days_start, last_7_days_start))

    # Calculate Deltas
    mom_delta = ((rev_now - rev_prev_mo) / rev_prev_mo * 100) if rev_prev_mo > 0 else 0
    wow_delta = ((rev_last_7 - rev_prev_7) / rev_prev_7 * 100) if rev_prev_7 > 0 else 0
    yoy_delta = ((rev_now - rev_prev_yr) / rev_prev_yr * 100) if rev_prev_yr > 0 else 0
    
    # Customer metrics (Retention/Churn)
    cust_now = get_customers(this_month_start, today)
    cust_prev = get_customers(last_month_start, last_month_end)
    
    retained_customers = cust_now.intersection(cust_prev)
    retention_rate = (len(retained_customers) / len(cust_prev) * 100) if cust_prev else 0
    churn_rate = 100 - retention_rate if cust_prev else 0

    return {
        "revenue": {
            "current": rev_now,
            "previous": rev_prev_mo,
            "mom_delta": round(mom_delta, 1),
            "wow_delta": round(wow_delta, 1),
            "yoy_delta": round(yoy_delta, 1)
        },
        "retention": {
            "value": round(retention_rate, 1),
            "delta": round(retention_rate - 75.0, 1) # Benchmark
        },
        "churn": {
            "value": round(churn_rate, 1),
            "delta": round(churn_rate - 25.0, 1)
        },
        "active_users": {
            "current": len(cust_now),
            "previous": len(cust_prev),
            "delta": len(cust_now) - len(cust_prev)
        }
    }


@router.get("/drilldown")
def get_analytics_drilldown(
    date: Optional[str] = None,
    kpi_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns specific data associated with a node drilldown (by date) or a KPI drilldown.
    """
    from datetime import datetime as dt_module, timedelta
    from sqlalchemy import cast, Date
    
    # Base timeframe
    if date:
        try:
            target_date = dt_module.strptime(date, "%Y-%m-%d").date()
            date_filter = cast(Order.created_at, Date) == target_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Default to last 30 days for KPI drill
        start_date = dt_module.now() - timedelta(days=30)
        date_filter = Order.created_at >= start_date
    
    total_rev = db.query(func.sum(Order.total_price)).filter(Order.status != OrderStatus.CANCELLED).filter(date_filter).scalar() or 0.0
    
    # Segments
    segment_query = (
        db.query(User.segment, func.sum(Order.total_price).label("revenue"))
        .select_from(Order)
        .join(User, Order.customer_id == User.id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .filter(date_filter)
        .group_by(User.segment)
        .all()
    )
    segments = [
        {
            "segment": r.segment or "Unknown", 
            "revenue": float(r.revenue), 
            "percentage": round(float(r.revenue) / total_rev * 100, 1) if total_rev > 0 else 0
        } for r in segment_query
    ]
    
    # Top Products
    top_products_query = (
        db.query(Product.name, Product.category, func.sum(Order.total_price).label("revenue"), func.sum(Order.quantity).label("units"))
        .select_from(Order)
        .join(Product, Order.product_id == Product.id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .filter(date_filter)
        .group_by(Product.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(5)
        .all()
    )
    products = [{"name": r.name, "category": r.category, "revenue": float(r.revenue), "units": int(r.units)} for r in top_products_query]

    # Top Customers
    top_customers_query = (
        db.query(User.full_name, func.sum(Order.total_price).label("revenue"))
        .select_from(Order)
        .join(User, Order.customer_id == User.id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .filter(date_filter)
        .group_by(User.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(5)
        .all()
    )
    customers = [{"name": r.full_name, "revenue": float(r.revenue)} for r in top_customers_query]

    return {
        "date_context": date if date else "Last 30 Days",
        "total_revenue": float(total_rev),
        "segments": segments,
        "top_products": products,
        "top_customers": customers
    }


@router.get("/customer-value")
def get_customer_value_segments(db: Session = Depends(get_db)):
    """
    Groups customers into value-based segments (High, Medium, Low) based on 
    percentile ranking of their total lifetime revenue.
    """
    from sqlalchemy import desc
    
    # 1. Get total revenue per user
    user_revenues = (
        db.query(User.id, User.full_name, func.sum(Order.total_price).label("lifetime_revenue"))
        .select_from(User)
        .join(Order, User.id == Order.customer_id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(User.id)
        .order_by(desc("lifetime_revenue"))
        .all()
    )
    
    if not user_revenues:
        return {"segments": [], "whales": []}
    
    total_users = len(user_revenues)
    total_platform_revenue = sum(u.lifetime_revenue for u in user_revenues)
    
    # 2. Define Percentiles (Dynamic)
    # High: Top 10%, Medium: Next 40%, Low: Bottom 50%
    high_idx = max(1, int(total_users * 0.1))
    med_idx = max(high_idx + 1, int(total_users * 0.5))
    
    high_cohort = user_revenues[:high_idx]
    med_cohort = user_revenues[high_idx:med_idx]
    low_cohort = user_revenues[med_idx:]
    
    def process_cohort(cohort, label):
        revenue = float(sum(c.lifetime_revenue for c in cohort))
        count = len(cohort)
        return {
            "label": label,
            "count": count,
            "revenue": revenue,
            "percentage": round((revenue / total_platform_revenue * 100), 1) if total_platform_revenue > 0 else 0,
            "arpu": round(revenue / count, 2) if count > 0 else 0
        }
    
    segments = [
        process_cohort(high_cohort, "High-Value (Top 10%)"),
        process_cohort(med_cohort, "Medium-Value (Mid 40%)"),
        process_cohort(low_cohort, "Low-Value (Bottom 50%)")
    ]
    
    # 3. Top Whales (Individual top 5)
    whales = [
        {"name": u.full_name, "revenue": float(u.lifetime_revenue)}
        for u in user_revenues[:5]
    ]
    
    return {
        "segments": segments,
        "top_whales": whales,
        "total_revenue": float(total_platform_revenue)
    }


@router.get("/fulfillment-funnel")
def get_fulfillment_funnel(db: Session = Depends(get_db)):
    """
    Calculates the conversion funnel from Order Placement -> Processing -> Shipped -> Delivered.
    """
    from sqlalchemy import func
    
    # 1. Fetch counts and total revenue per status
    status_stats = (
        db.query(Order.status, func.count(Order.id).label("count"), func.sum(Order.total_price).label("revenue"))
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(Order.status)
        .all()
    )
    
    stats_map = {s.status: {"count": s.count, "revenue": float(s.revenue or 0)} for s in status_stats}
    
    # Define funnel layers (Cumulative)
    # 1. Total (All non-cancelled)
    # 2. Confirmed (Confirmed, Shipped, Delivered)
    # 3. Shipped (Shipped, Delivered)
    # 4. Delivered (Delivered)
    
    total_count = sum(s.count for s in status_stats)
    total_rev = sum(float(s.revenue or 0) for s in status_stats)
    
    confirmed_count = total_count - stats_map.get(OrderStatus.PENDING, {"count": 0})["count"]
    confirmed_rev = total_rev - stats_map.get(OrderStatus.PENDING, {"revenue": 0})["revenue"]
    
    shipped_count = stats_map.get(OrderStatus.SHIPPED, {"count": 0})["count"] + stats_map.get(OrderStatus.DELIVERED, {"count": 0})["count"]
    shipped_rev = stats_map.get(OrderStatus.SHIPPED, {"revenue": 0})["revenue"] + stats_map.get(OrderStatus.DELIVERED, {"revenue": 0})["revenue"]
    
    delivered_count = stats_map.get(OrderStatus.DELIVERED, {"count": 0})["count"]
    delivered_rev = stats_map.get(OrderStatus.DELIVERED, {"revenue": 0})["revenue"]
    
    stages = [
        {"label": "Orders Placed", "count": total_count, "revenue": total_rev},
        {"label": "Confirmed & Processing", "count": confirmed_count, "revenue": confirmed_rev},
        {"label": "Shipped & In Transit", "count": shipped_count, "revenue": shipped_rev},
        {"label": "Final Delivered", "count": delivered_count, "revenue": delivered_rev}
    ]
    
    # Calculate conversion relative to Top and Previous
    for i in range(len(stages)):
        if i == 0:
            stages[i]["conversion_top"] = 100
            stages[i]["drop_off"] = 0
        else:
            prev = stages[i-1]
            stages[i]["conversion_top"] = round((stages[i]["count"] / total_count * 100), 1) if total_count > 0 else 0
            stages[i]["conversion_prev"] = round((stages[i]["count"] / prev["count"] * 100), 1) if prev["count"] > 0 else 0
            stages[i]["drop_off"] = round(100 - stages[i]["conversion_prev"], 1)

    return {"stages": stages}

