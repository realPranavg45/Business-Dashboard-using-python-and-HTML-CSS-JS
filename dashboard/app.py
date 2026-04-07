import streamlit as st
import pandas as pd
import requests
import sys
import os

# Ensure the root directory is accessible so we can import scripts directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.data_analysis import run_exploratory_data_analysis

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Business Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Styling / Aesthetics ---
st.markdown("""
    <style>
    .kpi-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
        text-align: center;
    }
    .kpi-title {
        color: #6c757d;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .kpi-value {
        color: #212529;
        font-size: 28px;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)


API_BASE_URL = "http://127.0.0.1:8000"

# --- API Helper Functions ---
def get_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def fetch_from_api(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=get_headers(), timeout=2)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def post_to_api(endpoint, payload):
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, headers=get_headers(), timeout=2)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"detail": str(e)}

def patch_to_api(endpoint, payload):
    try:
        response = requests.patch(f"{API_BASE_URL}{endpoint}", json=payload, headers=get_headers(), timeout=2)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"detail": str(e)}

@st.cache_data(ttl=5)
def check_backend_status():
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=1)
        if response.status_code == 200:
            return True, response.json()
        return False, {}
    except Exception:
        return False, {}

# --- Main App Logic ---
def main():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3616/3616999.png", width=50)
    st.sidebar.title("ErpAnalytics")
    
    is_online, health_data = check_backend_status()
    if is_online:
        st.sidebar.success(f"Backend: **Online**")
    else:
        st.sidebar.error("Backend: **Offline**")
        st.warning("Cannot connect to FastAPI backend. Please run `uvicorn app.main:app`")
        return
        
    st.sidebar.markdown("---")
    
    # Check Auth
    if "token" not in st.session_state:
        render_login_page()
        return
        
    st.sidebar.button("Logout", on_click=lambda: st.session_state.pop("token"))
    
    nav_tabs = ["Dashboard", "Orders", "Products", "🧠 Intelligence"]
    if st.session_state.get("is_admin", False):
        nav_tabs.insert(3, "Users")
        
    nav_option = st.sidebar.radio("Navigation", nav_tabs)
    
    if nav_option == "Dashboard":
        render_dashboard()
    elif nav_option == "Orders":
        render_orders_page()
    elif nav_option == "Products":
        render_products_page()
    elif nav_option == "Users":
        render_users_page()
    elif nav_option == "🧠 Intelligence":
        render_intelligence_page()

def render_login_page():
    st.title("🔒 Secure Login")
    st.write("Please authenticate to access the Business Dashboard.")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            try:
                # OAuth2 expects form-encoded data, not JSON
                res = requests.post(f"{API_BASE_URL}/api/v1/login/access-token", data={"username": email, "password": password})
                if res.status_code == 200:
                    token_data = res.json()
                    st.session_state["token"] = token_data["access_token"]
                    # Fetch profile to verify Admin standing
                    user_res = requests.get(f"{API_BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token_data['access_token']}"})
                    if user_res.status_code == 200:
                        st.session_state["is_admin"] = user_res.json().get("is_admin", False)
                    else:
                        st.session_state["is_admin"] = False
                        
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            except Exception as e:
                st.error("Network error attempting to login.")



def render_dashboard():
    st.title("📊 Business Analytics Overview")
    
    # Fetch Live Data
    orders = fetch_from_api("/api/v1/orders/")
    users = fetch_from_api("/api/v1/users/")
    products = fetch_from_api("/api/v1/products/")
    
    if not orders and not users and not products:
        st.info("Your database is completely empty. Go to the Users, Products, and Orders tabs to add some data!")
        return

    # Calculate Live KPIs
    total_revenue = sum(o.get('total_price', 0) for o in orders if o.get('status') != 'cancelled')
    active_orders = sum(1 for o in orders if o.get('status') not in ('cancelled', 'delivered'))
    total_users = len(users)
    total_products = len(products)
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Total Revenue</div><div class="kpi-value">${total_revenue:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Active Orders</div><div class="kpi-value">{active_orders}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Total Users</div><div class="kpi-value">{total_users}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-container"><div class="kpi-title">Products Available</div><div class="kpi-value">{total_products}</div></div>', unsafe_allow_html=True)
        
    # Live Charts
    if orders:
        st.subheader("Live Revenue Over Time")
        revenue_data = fetch_from_api("/api/v1/orders/analytics/revenue")
        if revenue_data:
            df_rev = pd.DataFrame(revenue_data)
            df_rev.set_index("date", inplace=True)
            st.area_chart(df_rev["revenue"])
        else:
            st.info("No revenue data available yet.")

        st.subheader("Recent Order History")
        df_orders = pd.DataFrame(orders)
        st.dataframe(df_orders, width="stretch", hide_index=True)


def render_products_page():
    st.title("📦 Products Inventory")
    
    is_admin = st.session_state.get("is_admin", False)
    if is_admin:
        with st.expander("➕ Add New Product"):
            with st.form("add_product_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name = col1.text_input("Name")
                category = col2.text_input("Category")
                price = col1.number_input("Price ($)", min_value=0.01, value=10.00)
                stock = col2.number_input("Stock Quantity", min_value=0, value=100)
                sku = st.text_input("SKU")
                desc = st.text_area("Description")
                
                if st.form_submit_button("Save Product"):
                    payload = {
                        "name": name,
                        "description": desc,
                        "price": price,
                        "stock_quantity": int(stock),
                        "category": category,
                        "sku": sku
                    }
                    status, res = post_to_api("/api/v1/products/", payload)
                    if status == 201:
                        st.success("Product created successfully!")
                    else:
                        st.error(f"Failed to create product: {res}")
    else:
        st.info("Restricted Area: Please log in as an System Administrator to manage product inventory.")
            
    st.markdown("### Current Products")
    products = fetch_from_api("/api/v1/products/")
    if products:
        st.dataframe(pd.DataFrame(products), width="stretch", hide_index=True)
        
        if is_admin:
            st.markdown("### 🔄 Update Stock Quantity")
            with st.form("update_stock_form"):
                prod_options = {f"{p['name']} (Current Stock: {p['stock_quantity']})": p['id'] for p in products}
                selected_prod = st.selectbox("Select Product", options=list(prod_options.keys()))
                new_stock = st.number_input("New Stock Quantity", min_value=0, value=0)
                
                if st.form_submit_button("Update Stock"):
                    payload = {"stock_quantity": int(new_stock)}
                    status_code, res = patch_to_api(f"/api/v1/products/{prod_options[selected_prod]}", payload)
                    if status_code == 200:
                        st.success("Stock updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update stock: {res}")
    else:
        st.info("No products found.")


def render_users_page():
    st.title("👥 Users Management")
    
    with st.expander("➕ Add New User"):
        with st.form("add_user_form", clear_on_submit=True):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["customer", "admin"])
            
            if st.form_submit_button("Save User"):
                payload = {
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "role": role,
                    "is_active": True
                }
                status, res = post_to_api("/api/v1/users/", payload)
                if status == 201:
                    st.success("User created successfully!")
                else:
                    st.error(f"Failed to create user: {res}")

    st.markdown("### Current Users")
    users = fetch_from_api("/api/v1/users/")
    if users:
        df = pd.DataFrame(users)
        # Drop password hashes from UI
        if "hashed_password" in df.columns:
            df = df.drop(columns=["hashed_password"])
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No users found.")


def render_orders_page():
    st.title("🛒 Orders Processing")
    
    users = fetch_from_api("/api/v1/users/")
    products = fetch_from_api("/api/v1/products/")
    
    with st.expander("➕ Create New Order"):
        if not users or not products:
            st.warning("You must create at least one User and one Product before creating an Order.")
        else:
            with st.form("add_order_form", clear_on_submit=True):
                user_options = {f"{u['full_name']} ({u['email']})": u['id'] for u in users}
                prod_options = {f"{p['name']} (${p['price']} - {p['stock_quantity']} in stock)": p['id'] for p in products if p['stock_quantity'] > 0}
                
                if not prod_options:
                    st.error("All products are currently out of stock!")
                else:
                    selected_user = st.selectbox("Customer", options=list(user_options.keys()))
                    selected_prod = st.selectbox("Product", options=list(prod_options.keys()))
                    qty = st.number_input("Quantity", min_value=1, value=1)
                    notes = st.text_input("Order Notes")
                    
                    if st.form_submit_button("Place Order"):
                        payload = {
                            "customer_id": user_options[selected_user],
                            "product_id": prod_options[selected_prod],
                            "quantity": int(qty),
                            "notes": notes
                        }
                        status, res = post_to_api("/api/v1/orders/", payload)
                        if status == 201:
                            st.success("Order placed successfully! Stock has been updated.")
                        else:
                            st.error(f"Failed to create order: {res}")

    st.markdown("### All Orders")
    orders = fetch_from_api("/api/v1/orders/")
    if orders:
        st.dataframe(pd.DataFrame(orders), width="stretch", hide_index=True)
        
        is_admin = st.session_state.get("is_admin", False)
        if is_admin:
            st.markdown("### Update Order Status")
            with st.form("update_status_form"):
                order_options = {f"Order #{o['id']} (Current: {o.get('status', 'pending')})": o['id'] for o in orders}
                selected_order = st.selectbox("Select Order", options=list(order_options.keys()))
                new_status = st.selectbox("New Status", ["pending", "confirmed", "shipped", "delivered", "cancelled"])
                
                if st.form_submit_button("Update Status"):
                    payload = {"status": new_status}
                    status_code, res = patch_to_api(f"/api/v1/orders/{order_options[selected_order]}/status", payload)
                    if status_code == 200:
                        st.success("Order status updated! Refreshing...")
                    else:
                        st.error(f"Failed to update status: {res}")
        else:
            st.info("Restricted Area: Only Administrators can mutate order fulfillment status.")
    else:
        st.info("No orders found.")

def render_intelligence_page():
    st.title("🧠 Smart Insights Engine")
    st.write("Real-time AI-driven business intelligence directly from the native SQL database.")
    
    insights = fetch_from_api("/api/v1/analytics/insights")
    if not insights or "text_alerts" not in insights:
        st.warning("Could not gather intelligence data at this time.")
        return
        
    st.subheader("🔔 System Alerts")
    for alert in insights["text_alerts"]:
        if "Critical" in alert or "⚠️" in alert:
            st.error(alert)
        elif "🔥" in alert or "🏆" in alert:
            st.success(alert)
        else:
            st.info(alert)
            
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Customers")
        if insights["top_customers"]:
            st.dataframe(pd.DataFrame(insights["top_customers"]), width="stretch", hide_index=True)
        else:
            st.info("No customer data.")
            
    with col2:
        st.subheader("Top Products")
        if insights["top_products"]:
            st.dataframe(pd.DataFrame(insights["top_products"]), width="stretch", hide_index=True)
        else:
            st.info("No product data.")
            
    st.markdown("---")
    st.subheader("📦 Comprehensive Inventory Status")
    products = fetch_from_api("/api/v1/products/")
    if products:
        df_prod = pd.DataFrame(products)
        
        # Calculate key inventory KPIs
        total_items = df_prod['stock_quantity'].sum()
        low_stock_thresh = 20
        out_of_stock = len(df_prod[df_prod['stock_quantity'] == 0])
        low_stock = len(df_prod[(df_prod['stock_quantity'] > 0) & (df_prod['stock_quantity'] <= low_stock_thresh)])
        
        inv1, inv2, inv3 = st.columns(3)
        inv1.metric("Total Items in Stock", f"{int(total_items):,}")
        inv2.metric("Out of Stock", out_of_stock, delta="-Critical" if out_of_stock > 0 else None, delta_color="inverse")
        inv3.metric("Low Stock Items", low_stock, delta="-Warning" if low_stock > 0 else None, delta_color="inverse")
        
        st.write("**Products with Lowest Stock Levels**")
        df_lowest = df_prod.sort_values(by="stock_quantity", ascending=True).head(5)
        
        # Style dataframe rows matching low inventory logic
        def highlight_inventory(row):
            if row.stock_quantity <= 0:
                return ['background-color: #ffcccc'] * len(row)
            elif row.stock_quantity <= 20:
                return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)
            
        styled_df = df_lowest[['sku', 'name', 'category', 'price', 'stock_quantity']].style.apply(highlight_inventory, axis=1)
        st.dataframe(styled_df, width="stretch", hide_index=True)
        
        st.write("**Inventory Layout (All Products)**")
        chart_data = df_prod[['name', 'stock_quantity']].set_index('name')
        st.bar_chart(chart_data)
    else:
        st.info("No inventory data found across the system.")
        
    st.markdown("---")
    st.subheader("📈 Offline Pandas Analytics")
    st.write("Direct Data Processing logic imported from `scripts/data_analysis.py`.")
    
    with st.spinner("Crunching raw data natively..."):
        eda_results = run_exploratory_data_analysis()
        
    if eda_results and not eda_results.get("error"):
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Lifetime Revenue", f"${eda_results['total_revenue']:,.2f}")
        col_m2.metric("Top Customer", eda_results["top_customer"])
        
        growth = eda_results.get("growth_rate_pct")
        if growth is not None:
            col_m3.metric("M-o-M Growth", f"{growth:+.2f}%", delta=f"{growth:+.2f}%")
        else:
            col_m3.metric("M-o-M Growth", "N/A")
    else:
        st.error(f"Failed to run EDA: {eda_results.get('error', 'Unknown Error') if eda_results else 'Unknown'}")

if __name__ == "__main__":
    main()
