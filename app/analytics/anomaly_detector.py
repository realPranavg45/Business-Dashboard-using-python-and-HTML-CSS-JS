"""
app/analytics/anomaly_detector.py
----------------------------------
AI-Driven Anomaly Detection Engine.
Uses Unsupervised ML (Isolation Forest) and Statistical Methods (Z-Score)
to identify outliers in business transactions and revenue streams.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import func, cast, Date, desc
from typing import List, Dict, Any
import time

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.db.database import SessionLocal

# --- Anomaly Cache ---
_anomaly_cache = {
    "order": {"data": [], "timestamp": 0},
    "revenue": {"data": [], "timestamp": 0}
}
ANOMALY_CACHE_TTL = 300 # 5 minutes

def detect_order_anomalies(db, contamination: float = 0.05) -> List[Dict[str, Any]]:
    """
    Identifies 'strange' orders using the Isolation Forest algorithm.
    Cached for efficiency.
    """
    global _anomaly_cache
    now = time.time()
    if now - _anomaly_cache["order"]["timestamp"] < ANOMALY_CACHE_TTL and _anomaly_cache["order"]["data"]:
        return _anomaly_cache["order"]["data"]

    # 1. Fetch valid orders
    orders = db.query(Order).filter(Order.status != OrderStatus.CANCELLED).all()
    
    if len(orders) < 10:
        return []

    # 2. Prepare Feature Matrix [Quantity, Price]
    data = [[o.quantity, float(o.total_price)] for o in orders]
    X = np.array(data)

    # Calculate global statistics for explaining anomalies
    quantities = X[:, 0]
    mean_quantity = np.mean(quantities)
    std_quantity = np.std(quantities)

    # Unit prices for non-zero quantities
    unit_prices = [X[j, 1] / X[j, 0] if X[j, 0] > 0 else 0 for j in range(len(X))]
    mean_up = np.mean(unit_prices)
    std_up = np.std(unit_prices)

    # 3. Fit Isolation Forest
    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(X) 

    # 4. Filter and return anomalies
    anomalies = []
    for i, pred in enumerate(predictions):
        if pred == -1:
            order = orders[i]
            product = db.query(Product).filter(Product.id == order.product_id).first()
            user = db.query(User).filter(User.id == order.customer_id).first()
            
            unit_price = float(order.total_price) / order.quantity if order.quantity > 0 else 0
            seg_label = f" ({user.segment} Partner)" if user and user.segment else ""
            prod_label = f" for '{product.name}'" if product else ""

            # Sophisticated Reason Generation
            if order.quantity > mean_quantity + 3 * std_quantity:
                reason = f"Extreme bulk purchase{prod_label}{seg_label}. Qty {order.quantity} is significantly above average."
            elif std_up > 0 and unit_price > mean_up + 3 * std_up:
                reason = f"High-ticket transaction{prod_label}. Unit price ${unit_price:,.2f} is well above standard rates."
            elif std_up > 0 and unit_price < mean_up - 1.5 * std_up:
                reason = f"Unusually deep discount/low-tier SKU detected{prod_label}."
            else:
                reason = f"Atypical transaction profile{prod_label} for {user.segment if user else 'Customer'}"

            anomalies.append({
                "order_id": order.id,
                "customer": user.full_name if user else "Unknown",
                "product": product.name if product else "Unknown",
                "quantity": order.quantity,
                "total_price": float(order.total_price),
                "created_at": order.created_at.isoformat(),
                "reason": reason
            })
    
    _anomaly_cache["order"] = {"data": anomalies, "timestamp": now}
    return anomalies

def detect_revenue_anomalies(db, threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Identifies abnormal revenue spikes/drops and performs a localized 'root cause analysis'
    to identify dominant Segment or Category drivers.
    """
    global _anomaly_cache
    now = time.time()
    if now - _anomaly_cache["revenue"]["timestamp"] < ANOMALY_CACHE_TTL and _anomaly_cache["revenue"]["data"]:
        return _anomaly_cache["revenue"]["data"]

    # 1. Fetch valid daily aggregates
    results = (
        db.query(
            cast(Order.created_at, Date).label("date"),
            func.sum(Order.total_price).label("daily_revenue"),
            func.count(Order.id).label("order_count")
        )
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
        .all()
    )

    if len(results) < 5:
        return []

    revenues = [float(r.daily_revenue) for r in results]
    mean_rev, std_rev = np.mean(revenues), np.std(revenues)
    order_counts = [float(r.order_count) for r in results]
    mean_count, std_count = np.mean(order_counts), np.std(order_counts)

    if std_rev == 0: return []

    anomalies = []
    for r in results:
        rev = float(r.daily_revenue)
        count = float(r.order_count)
        z_score = (rev - mean_rev) / std_rev
        count_z = (count - mean_count) / std_count if std_count > 0 else 0
        
        if abs(z_score) > threshold:
            seg_drivers = (
                db.query(User.segment, func.sum(Order.total_price).label("rev"))
                .join(Order, User.id == Order.customer_id)
                .filter(cast(Order.created_at, Date) == r.date, Order.status != OrderStatus.CANCELLED)
                .group_by(User.segment)
                .order_by(desc("rev"))
                .first()
            )
            cat_drivers = (
                db.query(Product.category, func.sum(Order.total_price).label("rev"))
                .join(Order, Product.id == Order.product_id)
                .filter(cast(Order.created_at, Date) == r.date, Order.status != OrderStatus.CANCELLED)
                .group_by(Product.category)
                .order_by(desc("rev"))
                .first()
            )

            if z_score > 0:
                if seg_drivers and seg_drivers.rev > rev * 0.5:
                    reason = f"Revenue spike driven by high concentration in the '{seg_drivers.segment}' segment."
                elif cat_drivers and cat_drivers.rev > rev * 0.5:
                    reason = f"Exceptional performance in the '{cat_drivers.category}' category on this date."
                elif count_z > 2:
                    reason = "Significant surge in total order volume compared to 30-day average."
                else:
                    reason = "Revenue spike due to elevated average transaction values across categories."
            else:
                if count_z < -2:
                    reason = "Critical drop in order volume detected for this date."
                else:
                    reason = "Low transaction density/small basket sizes despite standard order counts."

            anomalies.append({
                "date": str(r.date),
                "revenue": round(rev, 2),
                "z_score": round(z_score, 2),
                "severity": "Critical" if abs(z_score) > 3 else "High" if abs(z_score) > 2 else "Medium",
                "reason": reason
            })

    _anomaly_cache["revenue"] = {"data": anomalies, "timestamp": now}
    return anomalies
