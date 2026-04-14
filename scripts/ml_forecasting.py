import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sqlalchemy import func, cast, Date
from app.db.database import SessionLocal
from app.models.order import Order, OrderStatus

def predict_future_revenue() -> dict:
    """
    ML Forecasting Engine:
    1. Aggregates historical daily revenue from PostgreSQL.
    2. Fits a Linear Regression model (Scikit-Learn) to the time series.
    3. Projects 30 days of future revenue.
    """
    db = SessionLocal()
    try:
        # 1. Fetch historical aggregated revenue
        results = (
            db.query(
                cast(Order.created_at, Date).label("date"),
                func.sum(Order.total_price).label("revenue")
            )
            .filter(Order.status != OrderStatus.CANCELLED)
            .group_by(cast(Order.created_at, Date))
            .order_by(cast(Order.created_at, Date))
            .all()
        )
        
        if not results or len(results) < 2:
            return {"error": "Not enough historical data to generate a forecast. Need at least 2 days of sales."}

        # 2. Transform to Pandas for ML processing
        data = []
        for r in results:
            data.append({
                "date": r.date,
                "revenue": float(r.revenue) if r.revenue else 0.0
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # 3. Feature Engineering: Convert dates to ordinals for the regression model
        # LinearRegression requires numerical inputs
        df['date_ordinal'] = df['date'].map(datetime.toordinal)
        
        X = df[['date_ordinal']].values  # Features
        y = df['revenue'].values         # Target
        
        # 4. Train Model
        model = LinearRegression()
        model.fit(X, y)
        
        # 5. Generate 30-Day Forecast
        last_date = df['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        preds = model.predict(future_ordinals)
        preds = np.maximum(preds, 0) # Floor negative predictions to 0
        
        # 6. Format historical and forecast data for the dashboard
        historical_formatted = [
            {"date": row.date.strftime("%Y-%m-%d"), "revenue": round(row.revenue, 2)}
            for _, row in df.iterrows()
        ]
        
        forecast_formatted = [
            {"date": d.strftime("%Y-%m-%d"), "revenue": round(float(p), 2)}
            for d, p in zip(future_dates, preds)
        ]
        
        return {
            "historical_data": historical_formatted,
            "forecast_data": forecast_formatted,
            "metadata": {
                "algorithm": "Linear Regression",
                "days_forecasted": 30,
                "slope": round(float(model.coef_[0]), 4)
            }
        }

    except Exception as e:
        return {"error": f"ML Forecasting Error: {str(e)}"}
    finally:
        db.close()

def predict_what_if_revenue(price_multiplier: float = 1.0, volume_multiplier: float = 1.0, retention_multiplier: float = 1.0) -> dict:
    """
    Advanced Business Simulation:
    Project Revenue and Profit based on Price, Volume, and Retention adjustments.
    """
    base_res = predict_future_revenue()
    if "error" in base_res:
        return base_res
        
    combined_multiplier = price_multiplier * volume_multiplier * retention_multiplier
    margin_estimate = 0.30 # Default 30% margin for simulation
    
    historical_data = base_res["historical_data"]
    baseline_forecast = base_res["forecast_data"]
    
    simulated_forecast = []
    for data_point in baseline_forecast:
        simulated_forecast.append({
            "date": data_point["date"],
            "revenue": round(data_point["revenue"] * combined_multiplier, 2),
            "profit": round((data_point["revenue"] * combined_multiplier) * margin_estimate, 2)
        })
        
    return {
        "historical_data": historical_data,
        "baseline_forecast": baseline_forecast, # The original trajectory
        "simulated_forecast": simulated_forecast, # The shifted trajectory
        "metadata": {
            "algorithm": base_res["metadata"]["algorithm"],
            "days_forecasted": base_res["metadata"]["days_forecasted"],
            "scenario": {
                "price_impact": round((price_multiplier - 1) * 100, 1),
                "volume_impact": round((volume_multiplier - 1) * 100, 1),
                "retention_impact": round((retention_multiplier - 1) * 100, 1),
                "net_revenue_delta_percent": round((combined_multiplier - 1) * 100, 2)
            }
        }
    }

if __name__ == "__main__":
    # Test execution
    res = predict_future_revenue()
    if "error" in res:
        print(f"Error: {res['error']}")
    else:
        print(f"Baseline Forecast complete. First 3 days: {res['forecast_data'][:3]}")
    
    # Test what-if execution
    what_if_res = predict_what_if_revenue(price_multiplier=1.1, volume_multiplier=0.9)
    if "error" not in what_if_res:
        print(f"What-If complete. First 3 days: {what_if_res['forecast_data'][:3]}")
