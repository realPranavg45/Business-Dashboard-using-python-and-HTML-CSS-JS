import streamlit as st
import pandas as pd
import requests
import sys
import os
import time
import plotly.express as px

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
    return {}

def fetch_from_api(endpoint, params=None):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, headers=get_headers(), timeout=5)
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

def post_to_api_slow(endpoint, payload, timeout=60):
    """Used for endpoints that may take longer (e.g. AI chat calls to Gemini)."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, headers=get_headers(), timeout=timeout)
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
    
    nav_tabs = ["Dashboard", "Orders", "Products", "Users", "🧠 Intelligence", "💬 AI Assistant", "🟢 Live War Room"]
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
    elif nav_option == "💬 AI Assistant":
        render_ai_assistant()
    elif nav_option == "🟢 Live War Room":
        render_war_room()

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
            # Implement high-definition Plotly graphing framework!
            fig = px.area(df_rev, x="date", y="revenue", title="Native Revenue Trajectories", color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available yet.")

        st.subheader("Recent Order History")
        df_orders = pd.DataFrame(orders)
        st.dataframe(df_orders, width="stretch", hide_index=True)


def render_products_page():
    st.title("📦 Products Inventory")
    
    # --- Filter UI ---
    with st.expander("🔍 Filter & Sort Products"):
        col1, col2, col3 = st.columns(3)
        
        # Get unique categories for the dropdown
        all_prods = fetch_from_api("/api/v1/products/")
        categories = sorted(list(set(p['category'] for p in all_prods if p.get('category'))))
        category_filter = col1.selectbox("Category", ["All"] + categories)
        
        sort_by = col2.selectbox("Sort By", ["name", "price", "stock_quantity", "created_at"])
        sort_order = col3.radio("Order", ["Ascending", "Descending"], horizontal=True)
        
        col4, col5 = st.columns(2)
        min_stock = col4.number_input("Min Stock", min_value=0, value=0)
        max_price = col5.number_input("Max Price ($)", min_value=0.0, value=1000.0)
        
        params = {
            "sort_by": sort_by,
            "sort_order": "asc" if sort_order == "Ascending" else "desc",
            "min_stock": min_stock,
            "max_price": max_price
        }
        if category_filter != "All":
            params["category"] = category_filter

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
            
    st.markdown("### Current Products")
    products = fetch_from_api("/api/v1/products/", params=params)
    if products:
        st.dataframe(pd.DataFrame(products), width="stretch", hide_index=True)
        
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
        st.info("No products found matching those filters.")


def render_users_page():
    st.title("👥 Users Management")
    
    # --- Filter UI ---
    with st.expander("🔍 Filter & Search Users"):
        col1, col2 = st.columns([2, 1])
        search_query = col1.text_input("Search by Name or Email")
        role_filter = col2.selectbox("Role", ["All", "Admin", "Customer"])
        
        col3, col4 = st.columns(2)
        sort_by = col3.selectbox("Sort By", ["full_name", "email", "created_at"])
        sort_order = col4.radio("Order", ["Ascending", "Descending"], horizontal=True, key="user_sort")
        
        params = {
            "search": search_query if search_query else None,
            "sort_by": sort_by,
            "sort_order": "asc" if sort_order == "Ascending" else "desc"
        }
        if role_filter == "Admin":
            params["is_admin"] = True
        elif role_filter == "Customer":
            params["is_admin"] = False

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
    users = fetch_from_api("/api/v1/users/", params=params)
    if users:
        df = pd.DataFrame(users)
        # Drop password hashes from UI
        if "hashed_password" in df.columns:
            df = df.drop(columns=["hashed_password"])
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No users found matching those filters.")


def render_orders_page():
    st.title("🛒 Orders Processing")
    
    # --- Filter UI ---
    with st.expander("🔍 Filter & Sort Orders"):
        col1, col2, col3 = st.columns(3)
        status_filter = col1.selectbox("Status", ["All", "pending", "confirmed", "shipped", "delivered", "cancelled"])
        sort_by = col2.selectbox("Sort By", ["created_at", "total_price", "id"])
        sort_order = col3.radio("Order", ["Descending", "Ascending"], horizontal=True)
        
        col4, col5 = st.columns(2)
        start_date = col4.date_input("Start Date", value=None)
        end_date = col5.date_input("End Date", value=None)
        
        params = {
            "sort_by": sort_by,
            "sort_order": "desc" if sort_order == "Descending" else "asc"
        }
        if status_filter != "All":
            params["status"] = status_filter
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
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
    orders = fetch_from_api("/api/v1/orders/", params=params)
    if orders:
        st.dataframe(pd.DataFrame(orders), width="stretch", hide_index=True)
        
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
        st.info("No orders found matches those filters.")

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
            
    low_stock = insights.get("low_stock_items", [])
    if low_stock:
        if len(low_stock) <= 2:
            st.error("⚠️ **Low Stock Alert:**")
            for item in low_stock:
                st.write(f"- **{item['name']}** (Only {item['stock_quantity']} left)")
        else:
            with st.expander(f"⚠️ Critical Stock Alert: {len(low_stock)} products need restocking!"):
                for item in low_stock:
                    st.write(f"- **{item['name']}** (Stock: {item['stock_quantity']})")
            
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
        
        st.write("**Deep Inventory Classification**")
        colA, colB = st.columns(2)
        
        # 🟢 Apply Interactivity Filters for Plotly Graphing!
        st.sidebar.markdown("### 📊 Plotly Cross-Filters")
        cat_options = list(df_prod['category'].unique())
        selected_category = st.sidebar.multiselect("Filter Inventory by Category", cat_options, default=cat_options)
        
        # Cross-filter the dataframe reactively before passing into Plotly instances
        filtered_df = df_prod[df_prod['category'].isin(selected_category)]
        
        with colA:
            if not filtered_df.empty:
                fig_bar = px.bar(filtered_df, x='name', y='stock_quantity', color='category', title="Geographic Category Distribution")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Select a category in the sidebar to render bar charts.")
            
        with colB:
            if not filtered_df.empty:
                fig_pie = px.pie(filtered_df, names='category', values='stock_quantity', hole=0.3, title="Category Volume Ratios")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Select a category in the sidebar to render pie mappings.")
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
        
    st.markdown("---")
    st.subheader("🤖 Enterprise AI Revenue Forecasting")
    st.write("This model parses raw historical revenue strings utilizing Scikit-Learn `LinearRegression` plotting 30-day algorithmic momentum grids natively onto the front-end.")
    
    with st.spinner("Executing Scikit-Learn predictions..."):
        ml_data = fetch_from_api("/api/v1/analytics/ml-revenue-forecast")
        
    if ml_data and "error" not in ml_data:
        # Create a unified pandas DataFrame bridging the past and the future together cleanly
        past = pd.DataFrame({
            "Date": ml_data["historical_dates"],
            "Historical Revenue": ml_data["historical_revenue"],
            "Forecasted Target": [None] * len(ml_data["historical_dates"])
        })
        
        future = pd.DataFrame({
            "Date": ml_data["future_dates"],
            "Historical Revenue": [None] * len(ml_data["future_dates"]),
            "Forecasted Target": ml_data["future_revenue"]
        })
        
        combined = pd.concat([past, future], ignore_index=True)
        combined["Date"] = pd.to_datetime(combined["Date"])
        combined.set_index("Date", inplace=True)
        
        st.line_chart(combined)
    else:
        st.warning("Not enough historical volatility mapping to generate a secure AI prediction.")

    st.markdown("---")
    st.subheader("🕵️ Anomaly Explorer")
    st.write("Using AI and Statistical parameters to detect suspicious behavioral metrics.")
    
    with st.spinner("Analyzing data for anomalies..."):
        anomalies_data = fetch_from_api("/api/v1/analytics/anomalies")
        
    if anomalies_data:
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("**Revenue Volatility Alerts**")
            rev_anoms = anomalies_data.get("revenue_anomalies", [])
            if rev_anoms:
                st.dataframe(pd.DataFrame(rev_anoms), use_container_width=True, hide_index=True)
            else:
                st.success("No revenue anomalies detected.")
                
        with col_a2:
            st.markdown("**Suspicious Order Flags**")
            ord_anoms = anomalies_data.get("order_anomalies", [])
            if ord_anoms:
                st.dataframe(pd.DataFrame(ord_anoms), use_container_width=True, hide_index=True)
            else:
                st.success("No suspicious orders flagged.")
    else:
        st.error("Failed to load anomaly detection data.")

def render_ai_assistant():
    st.title("💬 AI Business Assistant")
    st.markdown(
        "Ask anything about your business — sales, orders, inventory, customers, profit & loss. "
        "The AI reads your **live database** before every answer."
    )

    # ── Suggested starter questions ───────────────────────────────────────────
    SUGGESTIONS = [
        "What is today's total revenue?",
        "Which product has sold the most units?",
        "How many orders are currently active?",
        "Who are my top 3 customers by spend?",
        "Which products are low on stock?",
        "Give me a profit/loss summary.",
    ]

    st.markdown("#### 💡 Suggested Questions")
    suggestion_cols = st.columns(3)
    if "prefill_query" not in st.session_state:
        st.session_state.prefill_query = ""

    for i, suggestion in enumerate(SUGGESTIONS):
        col = suggestion_cols[i % 3]
        if col.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
            st.session_state.prefill_query = suggestion

    st.markdown("---")

    # ── Session message history ────────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hello! I'm your AI Business Analyst. I have real-time access to your "
                    "sales, orders, inventory, and customer data.\n\n"
                    "Ask me anything — like *'What were yesterday\'s sales?'* or "
                    "*'Which products are running low?'*"
                ),
            }
        ]

    # ── Render existing chat history ──────────────────────────────────────────
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Chat input (handles both typed and suggestion-prefilled) ─────────────
    prefill = st.session_state.pop("prefill_query", "") if st.session_state.get("prefill_query") else ""

    user_input = st.chat_input(
        placeholder="Ask a business question (e.g. 'What are today\'s sales?')…"
    ) or prefill

    if user_input:
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call the backend AI endpoint (60s timeout — Gemini can take a few seconds)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your business data…"):
                status_code, response = post_to_api_slow("/api/v1/analytics/chat", {"query": user_input})

            if status_code == 200 and "answer" in response:
                answer = response["answer"]
            else:
                answer = f"❌ Could not get a response from the AI. (Status: {status_code}, Detail: {response})"

            st.markdown(answer)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    # ── Clear chat button ─────────────────────────────────────────────────────
    if len(st.session_state.chat_messages) > 1:
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=False):
            st.session_state.chat_messages = []
            st.rerun()


def render_war_room():
    st.title("🟢 Active Traffic Telemetry")
    st.write("Watch as chaotic multi-threaded shoppers continuously bombard the API! Start the `scripts/traffic_simulator.py` terminal asynchronously.")
    
    # Create persistent empty containers for rewriting frame matrices dynamically
    col1, col2 = st.columns(2)
    metric_container = col1.empty()
    table_container = col2.empty()
    chart_container = st.empty()
    
    # We load standard variables to check length without destroying memory
    if "war_room_started" not in st.session_state:
        st.info("Click below to instantiate Web Sockets polling (Fast Polling Simulation).")
        if st.button("Activate Live Streaming"):
            st.session_state.war_room_started = True
            st.rerun()
    else:
        if st.button("Halt Telemetry"):
            del st.session_state.war_room_started
            st.rerun()
            
        st.success("Socket Stream Initialized! Polling Database rapidly.")
        while True:
            # We fetch all orders and just slice off the latest 30 inside Streamlit thread
            orders = fetch_from_api("/api/v1/orders/")
            if orders:
                df = pd.DataFrame(orders)
                total_transactions = len(df)
                
                # Fetch recent rolling volume (Last 50 entries)
                recent_df = df.tail(50).copy()
                
                with metric_container:
                    st.metric("Total API Requests Processed (Live)", f"{total_transactions:,}")
                    
                with table_container:
                    # Clean up matrix view natively
                    st.dataframe(recent_df[['id', 'product_id', 'quantity', 'total_price', 'status']].sort_values("id", ascending=False).head(10), width="stretch", hide_index=True)
                    
                with chart_container:
                    # Rolling transaction value over the last 50 queries
                    st.area_chart(recent_df['total_price'].reset_index(drop=True))
                    
            time.sleep(1.5)  # Pause to avoid absolute API deadlock then rerun stream!

if __name__ == "__main__":
    main()
