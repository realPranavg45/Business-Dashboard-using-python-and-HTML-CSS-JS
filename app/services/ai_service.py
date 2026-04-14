"""
app/services/ai_service.py
--------------------------
AI Chatbot Service: Builds a real-time business context from the database
and uses Google Gemini to answer natural-language business queries.

Architecture:
  1. build_business_context(db) — queries live DB data and returns a structured
     text snapshot (revenue, orders, top products, inventory alerts, etc.)
  2. ask_business_question(query, db) — combines the context with the user's
     question into a rich prompt then calls the Gemini API and returns the answer.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import time

_context_cache = {"text": "", "timestamp": 0}
_pulse_cache = {"text": "", "timestamp": 0}
CACHE_TTL = 300 # Seconds (5 minutes) for better performance

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.core.config import settings


# ---------------------------------------------------------------------------
# Helper: Build a concise text snapshot of all live business data
# ---------------------------------------------------------------------------

def build_business_context(db: Session) -> str:
    """
    Queries the database and compiles a structured text context that will be
    injected into the AI prompt so Gemini can answer with real numbers.
    """
    global _context_cache
    now = time.time()
    if now - _context_cache["timestamp"] < CACHE_TTL:
        return _context_cache["text"]

    lines = []
    today = date.today()

    # ── 1. Revenue Velocity (MoM) ─────────────────────────────────────────────
    # Current Month
    first_day_current = today.replace(day=1)
    revenue_current_month = db.query(func.sum(Order.total_price)).filter(
        func.date(Order.created_at) >= first_day_current,
        Order.status != OrderStatus.CANCELLED
    ).scalar() or 0.0

    # Previous Month
    last_day_prev = first_day_current - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    revenue_prev_month = db.query(func.sum(Order.total_price)).filter(
        func.date(Order.created_at) >= first_day_prev,
        func.date(Order.created_at) <= last_day_prev,
        Order.status != OrderStatus.CANCELLED
    ).scalar() or 0.0

    mom_change = ((revenue_current_month - revenue_prev_month) / revenue_prev_month * 100) if revenue_prev_month > 0 else 0

    lines.append("=== FINANCIAL VELOCITY ===")
    lines.append(f"Current Month Revenue (MTD): ${revenue_current_month:,.2f}")
    lines.append(f"Previous Full Month Revenue: ${revenue_prev_month:,.2f}")
    lines.append(f"Revenue MoM Velocity: {mom_change:+.1f}%")

    # ── 2. Order Dynamics & AOV ───────────────────────────────────────────────
    total_revenue = db.query(func.sum(Order.total_price)).filter(Order.status != OrderStatus.CANCELLED).scalar() or 0.0
    total_orders  = db.query(func.count(Order.id)).filter(Order.status != OrderStatus.CANCELLED).scalar() or 0
    aov = total_revenue / total_orders if total_orders > 0 else 0

    lines.append(f"\n=== ORDER METRICS ===")
    lines.append(f"Average Order Value (AOV): ${aov:,.2f}")
    lines.append(f"Total Completed Orders: {total_orders}")

    # ── 3. Strategic Concentration (Risk Analysis) ───────────────────────────
    # Top 5 Customers share
    top_5_cust_revenue = (
        db.query(func.sum(Order.total_price))
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(Order.customer_id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(5)
        .all()
    )
    top_5_cust_total = sum([row[0] for row in top_5_cust_revenue]) if top_5_cust_revenue else 0
    concentration_ratio = (top_5_cust_total / total_revenue * 100) if total_revenue > 0 else 0

    lines.append(f"\n=== CONCENTRATION RATIOS ===")
    lines.append(f"Top 5 Customers Revenue Share: {concentration_ratio:,.1f}% (Risk if > 50%)")

    # ── 4. Top 5 products by revenue ──────────────────────────────────────────
    top_products = (
        db.query(Product.name, func.sum(Order.total_price).label("revenue"),
                 func.sum(Order.quantity).label("units"))
        .join(Order, Product.id == Order.product_id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(Product.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(5)
        .all()
    )
    lines.append("\n=== TOP 5 PRODUCTS BY REVENUE ===")
    for i, p in enumerate(top_products, 1):
        lines.append(f"  {i}. {p.name} — ${float(p.revenue or 0):,.2f} ({ (float(p.revenue or 0)/total_revenue*100) if total_revenue > 0 else 0 :.1f}% share)")

    # ── 5. Top 5 customers by spend ───────────────────────────────────────────
    top_customers = (
        db.query(User.full_name, User.email, func.sum(Order.total_price).label("spent"))
        .join(Order, User.id == Order.customer_id)
        .filter(Order.status != OrderStatus.CANCELLED)
        .group_by(User.id)
        .order_by(func.sum(Order.total_price).desc())
        .limit(5)
        .all()
    )
    lines.append("\n=== TOP 5 CUSTOMERS BY SPEND ===")
    for i, c in enumerate(top_customers, 1):
        lines.append(f"  {i}. {c.full_name} ({c.email}) — ${float(c.spent or 0):,.2f} total spend")

    # ── 6. Inventory overview ─────────────────────────────────────────────────
    total_sku    = db.query(func.count(Product.id)).scalar() or 0
    total_units  = db.query(func.sum(Product.stock_quantity)).scalar() or 0
    out_of_stock = db.query(Product).filter(Product.stock_quantity == 0).limit(5).all()
    low_stock    = db.query(Product).filter(Product.stock_quantity > 0, Product.stock_quantity <= 20).limit(5).all()
    
    lines.append("\n=== INVENTORY ===")
    lines.append(f"Total SKUs: {total_sku} | Total units: {total_units:,}")
    if out_of_stock:
        lines.append(f"Out-of-stock SKUs: " + ", ".join(p.name for p in out_of_stock))
    if low_stock:
        lines.append(f"Low-stock SKUs: " + ", ".join(f"{p.name} ({p.stock_quantity})" for p in low_stock))

    context = "\n".join(lines)
    _context_cache = {"text": context, "timestamp": now}
    return context


# ---------------------------------------------------------------------------
# Main entry point: ask a question
# ---------------------------------------------------------------------------

def ask_business_question(query: str, db: Session) -> str:
    """
    Builds a live business context from the DB, constructs a prompt, calls
    Gemini and returns the generated answer as plain text.
    """
    if not settings.GEMINI_API_KEY:
        return (
            "⚠️ **AI Assistant is not configured.** "
            "Please add your `GEMINI_API_KEY` to the `.env` file and restart the backend."
        )

    # Use the new google.genai SDK (google.generativeai is deprecated)
    from google import genai
    from google.genai import types
    from sqlalchemy import cast, Date

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # --- Tool Definitions ---
    def execute_sql(custom_query: str) -> str:
        """
        Executes a raw PostgreSQL SELECT query against the database and returns the results.
        Use this tool to answer ANY complex data questions about users, products, or orders.
        Only SELECT queries are allowed.
        
        Args:
            custom_query: The SQL query to execute.
        """
        if not custom_query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries are permitted."
        
        try:
            from sqlalchemy import text
            result = db.execute(text(custom_query)).fetchall()
            
            if not result:
                return "The query returned no results."
            
            # Format results
            dict_res = [dict(row._mapping) for row in result[:50]]
            return f"Success. Query returned {len(result)} rows. Top results: " + str(dict_res)
        except Exception as e:
            return f"SQL Error: {str(e)}"

    def get_inventory_alerts() -> str:
        """
        Returns a list of all out-of-stock and low-stock products.
        """
        out_of_stock = db.query(Product).filter(Product.stock_quantity == 0).limit(20).all()
        low_stock    = db.query(Product).filter(Product.stock_quantity > 0, Product.stock_quantity <= 20).limit(20).all()
        
        res = []
        if out_of_stock:
            res.append(f"Out of stock ({len(out_of_stock)}): " + ", ".join(p.name for p in out_of_stock))
        if low_stock:
            res.append(f"Low stock <=20 ({len(low_stock)}): " + ", ".join(f"{p.name} ({p.stock_quantity})" for p in low_stock))
            
        if not res:
            return "Inventory is healthy. No low-stock alerts."
        return "\n".join(res)

    # Build live snapshot
    context = build_business_context(db)
    current_date = date.today().isoformat()

    system_instruction = (
        f"You are a senior business analyst AI assistant. Today's date is {current_date}.\n"
        "--- DATABASE SCHEMA ---\n"
        "Table `users`: id (INTEGER), full_name (VARCHAR), email (VARCHAR)\n"
        "Table `products`: id (INTEGER), name (VARCHAR), price (FLOAT), stock_quantity (INTEGER)\n"
        "Table `orders`: id (INTEGER), customer_id (INTEGER, fk users.id), product_id (INTEGER, fk products.id), quantity (INTEGER), total_price (FLOAT), status (VARCHAR: pending, confirmed, shipped, delivered, cancelled), created_at (TIMESTAMP)\n"
        "--- END SCHEMA ---\n"
        "--- RESPONSE STYLE (STRICT) ---\n"
        "1. NEVER USE MARKDOWN TABLES. NEVER.\n"
        "2. Be concise and structured. Use short bullet points for lists.\n"
        "3. Only include the most relevant details (e.g., ID, Customer, Price). Avoid noise.\n"
        "4. Highlight totals or key metrics in BOLD at the start.\n"
        "5. Avoid long paragraphs. Use meaningful headings if needed.\n"
        "6. SEARCH RELIABILITY: For text searches in SQL, always use `ILIKE '%term%'` to ensure plural/singular and case-insensitive matches (e.g. matching 'trouser' with 'Trousers').\n"
        "--- END STYLE ---\n"
        "If complex aggregation is needed, use `execute_sql`. Answer accurately using only verified numbers.\n"
        "Format currency with commas and 2 decimal places (e.g. $1,234.56)."
    )

    prompt = (
        f"--- LIVE BUSINESS DATA CONTEXT ---\n"
        f"{context}\n"
        f"--- END OF CONTEXT ---\n\n"
        f"User Question: {query}"
    )

    # Robust retry with exponential backoff for transient 502/503 errors
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=settings.GENAI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[execute_sql, get_inventory_alerts]
                ),
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e).lower()
            # Retry on transient errors (502, 503, 429)
            if any(code in err_str for code in ["502", "503", "429"]) and attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + 0.5 # 0.5, 2.5, 4.5...
                print(f"[AI Retry] Transient error ({err_str[:20]}...). Attempt {attempt+1}/{max_retries}. Sleeping {sleep_time}s")
                time.sleep(sleep_time)
                continue
            
            print(f"[AI Critical Error] {str(e)}")
            return f"⚠️ AI Assistant is temporarily unavailable due to high demand (503). Please try again in a few moments."

def get_quick_insights(db: Session) -> str:
    """
    Generates a concise narrative summary of business health using Gemini.
    Cached for CACHE_TTL seconds.
    """
    global _pulse_cache
    now = time.time()
    
    if now - _pulse_cache["timestamp"] < CACHE_TTL and _pulse_cache["text"]:
        return _pulse_cache["text"]

    if not settings.GEMINI_API_KEY:
        return "AI Pulse is not configured. (Missing API Key)"

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        context = build_business_context(db)
        
        prompt = (
            "Act as a helpful business assistant. Look at the data and tell us what we should do next.\n\n"
            "SYSTEM REQUIREMENTS (VERY IMPORTANT):\n"
            "1. USE SIMPLE, EVERYDAY WORDS: Do not use business jargon like 'MoM', 'Velocity', 'Standard Deviation', 'Volatility', or 'Churn'.\n"
            "2. KEEP IT SHORT: Use very short sentences. Quickly explain what happened and exactly what action should be taken.\n"
            "3. BE CONVERSATIONAL: Write as if you are talking to a friend.\n\n"
            "RETURN A RAW JSON ARRAY OF 4 OBJECTS. NO MARKDOWN.\n"
            "Properties:\n"
            "- 'priority': 'Critical' (Big Problem), 'Warning' (Needs Attention), or 'Opportunity' (Good area to grow)\n"
            "- 'title': A short, simple heading\n"
            "- 'explanation': One short sentence saying what happened and why it matters.\n"
            "- 'metric': A simple number or percentage to prove it (e.g., '10% more sales')\n"
            "- 'action': One simple, direct thing we should do right now.\n\n"
            f"--- DATA SNAPSHOT ---\n{context}\n"
        )
        
        # Implementation of resilient exponential retry for 502/503/429 errors
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=settings.GENAI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        top_p=0.8,
                        max_output_tokens=1000,
                        response_mime_type="application/json"
                    ),
                )
                summary = response.text.strip()
                _pulse_cache = {"text": summary, "timestamp": now}
                return summary
            except Exception as e:
                err_str = str(e).lower()
                # 502/503/429 are transient errors - retry with exponential backoff
                if any(code in err_str for code in ["502", "503", "429"]) and attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + 0.5
                    print(f"[AI Pulse Retry] Transient error. Attempt {attempt+1}/{max_retries}. Sleeping {sleep_time}s")
                    time.sleep(sleep_time)
                    continue
                raise e
    except Exception as e:
        print(f"[AI Pulse Critical Error] {str(e)}")
        # Provide a safe fallback JSON so the UI doesn't crash
        import json
        fallback = [
            {
                "priority": "Warning",
                "title": "AI Insights Paused",
                "explanation": "The AI service is experiencing high demand right now.",
                "metric": "503 Error",
                "action": "Check back in 1 minute for updated business pulse."
            }
        ]
        return json.dumps(fallback)
