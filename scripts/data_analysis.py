import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def run_exploratory_data_analysis():
    print("=" * 50)
    print("🚀 AUTOMATED EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 50)
    
    # 1. Load context
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment.")
        return {"error": "DATABASE_URL not found"}

    # 2. Connect via SQLAlchemy native engine
    print("\nConnecting to Analytics Database...")
    engine = create_engine(db_url)
    
    # 3. Read SQL directly into native pandas DataFrames
    try:
        df_orders = pd.read_sql_table("orders", con=engine)
        df_products = pd.read_sql_table("products", con=engine)
        df_users = pd.read_sql_table("users", con=engine)
    except Exception as e:
        print(f"❌ Failed to load tables: {e}")
        return {"error": f"Failed to load tables: {e}"}

    print(f"✅ Loaded {len(df_orders)} orders, {len(df_products)} products, {len(df_users)} users.")

    # 4. Clean Data
    print("\n--> Cleaning Data...")
    df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
    df_valid_orders = df_orders[df_orders['status'] != 'cancelled']

    # 5. Extract KPI Insights
    print("\n" + "*"*30)
    print("📊 KPI INSIGHTS")
    print("*"*30)
    
    results = {
        "total_revenue": 0.0,
        "top_customer": "N/A",
        "growth_rate_pct": None,
        "error": None
    }
    
    total_rev = df_valid_orders['total_price'].sum()
    results["total_revenue"] = float(total_rev)
    print(f"💰 Total Lifetime Revenue: ${total_rev:,.2f}")
    
    if not df_valid_orders.empty:
        # Group by customer
        top_customer_id = df_valid_orders.groupby('customer_id')['total_price'].sum().idxmax()
        top_customer_name = df_users.loc[df_users['id'] == top_customer_id, 'full_name'].values[0]
        results["top_customer"] = str(top_customer_name)
        print(f"👑 Top Customer: {top_customer_name}")
        
        # Growth Rate (Current Month vs Last Month)
        df_valid_orders.set_index('created_at', inplace=True)
        monthly_rev = df_valid_orders.resample('ME')['total_price'].sum()
        
        if len(monthly_rev) >= 2:
            last_month = monthly_rev.iloc[-2]
            this_month = monthly_rev.iloc[-1]
            growth = ((this_month - last_month) / last_month) * 100 if last_month > 0 else 100
            results["growth_rate_pct"] = float(growth)
            print(f"📈 M-o-M Revenue Growth: {growth:+.2f}%")
        else:
            print("📈 Not enough monthly data for growth rate yet.")
    
    print("\n✅ Analysis Complete. Consider using these metrics to augment machine learning workflows.")
    return results

if __name__ == "__main__":
    run_exploratory_data_analysis()
