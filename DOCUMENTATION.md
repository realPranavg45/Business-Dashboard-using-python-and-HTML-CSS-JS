# 📑 Smart Business Analytics Platform: Full Documentation

## 🔍 Project Overview
The **Smart Business Analytics Platform** is a production-tier full-stack application designed to bridge the gap between traditional ERP systems and modern AI-driven intelligence. It provides a robust backend for managing business operations (Users, Products, Orders) and a high-performance frontend for data visualization, real-time telemetry, and predictive modeling.

---

## 🏗 System Architecture & Technology Stack

### Backend Architecture (FastAPI)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) – Selected for its high performance (Starlette/Pydantic) and native asynchronous support.
- **Database Architecture**: PostgreSQL managed through **SQLAlchemy 2.0 (ORM)**. 
- **Migration Strategy**: Explicit schema versioning via **Alembic**.
- **Security**: Password hashing and JWT-ready role-based provisioning.
- **Organization**: Modular Monolith structure (`/app/models`, `/app/api`, `/app/services`).

### Frontend Architecture (Streamlit)
- **Framework**: [Streamlit](https://streamlit.io/) – Used for rapid development of data-centric dashboards without sacrificing visual premium.
- **Graphics Engine**: **Plotly** – Delivers interactive, high-definition charts for revenue trajectories and inventory distributions.
- **State Management**: Session-based persistence for chat history and telemetry activation.

---

## 🚀 Feature Breakdown & Implementation Details

### 1. ⚡ Live Business Dashboard
*   **Functionality**: Provides a real-time overview of key performance indicators (KPIs) including Total Revenue, Active Orders, user base growth, and product availability.
*   **Implementation**:
    *   Aggregated KPIs are calculated server-side using SQL `func.sum` and `func.count` to minimize data transfer.
    *   Front-end uses `st.metric` with delta tracking for visual impact.

### 2. 🧠 AI Business Assistant (Gemini Integration)
*   **Functionality**: A natural-language interface allowing users to ask complex business questions (e.g., "What was my highest revenue day in March?").
*   **Approach**: 
    *   **Context Injection**: Before querying the LLM, the system generates a "Business Context" string by fetching live data snapshots from the database.
    *   **Response Generation**: Uses the `google-genai` SDK to process the question alongside the context.
*   **Technologies**: Google Gemini (Flash 1.5/2.0), FastAPI, Streamlit Chat.

### 3. 📈 Enterprise Revenue Forecasting (ML)
*   **Functionality**: Predicts the next 30 days of revenue based on historical order data.
*   **Approach**: 
    1.  Historical daily revenue is aggregated from PostgreSQL.
    2.  Data is converted into an ordinal time series.
    3.  A **Scikit-Learn Linear Regression** model is fitted natively.
    4.  The projection is extrapolated for 30 days and rendered with a Plotly area chart.
*   **Technologies**: Scikit-Learn, NumPy, Pandas.

### 4. 🕵️ AI Anomaly Detection
*   **Functionality**: Proactively flags suspicious activity in orders and revenue volatility.
*   **Multi-Dimensional Detection**: Uses **Isolation Forest** (Unsupervised Learning) to analyze `quantity` vs `total_price` clusters. Outliers that fall significantly outside normal buying patterns are flagged.
*   **Statistical Analysis**: Uses **Z-Score** (Standard Deviation) analysis to detect abnormal revenue spikes or drops.
*   **Implementation**: 
    *   Logic is encapsulated in `app/analytics/anomaly_detector.py`.
    *   Results are visualized in the "Intelligence" page with distinct "High Severity" markers.

### 5. 🟢 Live War Room & Traffic Telemetry
*   **Functionality**: Simulates and monitors high-concurrency environments.
*   **Chaos Testing**: A background script (`traffic_simulator.py`) generates multi-threaded requests mimicking hundreds of concurrent shoppers.
*   **Real-time Polling**: Streamlit uses a high-frequency polling loop to update metrics and transaction charts, simulating a real-time socket stream.

### 6. 📦 Inventory & Order Management
*   **Functionality**: Full CRUD management of the product lifecycle and sales pipeline.
*   **Implementation**:
    *   Atomic database transactions ensure that stock is deducted at the exact moment of order placement.
    *   Order status transitions are governed by a safe Enum structure to prevent data corruption.

---

## 🛠 Detailed Implementation Process

### Phase 1: Infrastructure & Database
1.  Initialized the **SQLAlchemy Base** models and defined relationships (Users, Products, Orders).
2.  Configured **PostgreSQL** connection logic and implemented dependency injection for DB sessions.
3.  Set up **Alembic** to handle automated table creation and future schema updates.

### Phase 2: Core API Layer
1.  Built the RESTful API endpoints using **FastAPI Router**.
2.  Implemented **Pydantic schemas** for request/response validation (ensuring the API is self-documenting via Swagger/Docs).
3.  Integrated business logic into dedicated service layers (`ai_service`, `insight_engine`).

### Phase 3: Intelligence & AI
1.  Integrated the **Google GenAI SDK** to bring Gemini's reasoning capabilities to the private business database.
2.  Implemented the **Linear Regression** forecasting logic as a decoupled script to prevent blocking API threads.
3.  Added the **Anomaly Detection** layer using the `IsolationForest` model to differentiate normal variance from true service anomalies.

### Phase 4: UI Development & Aesthetics
1.  Designed a custom CSS theme inside Streamlit for a "Premium" look.
2.  Implemented **Plotly Area Charts** and **Bar Charts** with cross-filtering support.
3.  Built the **Live War Room** to provide a "Mission Control" experience for business owners.

---

## 🏁 How to Run & Verify

1.  **Environment Setup**:
    *   Ensure a `.env` file exists with `DATABASE_URL` and `GOOGLE_API_KEY`.
    *   Install dependencies: `pip install -r requirements.txt`.
2.  **Launching the Platform**:
    *   Backend: `uvicorn app.main:app --reload`
    *   Frontend: `streamlit run dashboard/app.py`
3.  **Simulation**:
    *   Start heavy traffic: `python scripts/traffic_simulator.py`

---
*Documentation prepared on April 8, 2026.*

---

## 📡 API Reference

The platform exposes a versioned REST API under the `/api/v1` prefix. All sensitive endpoints require a Bearer Token obtained via the login endpoint.

### 1. Authentication (`/api/v1`)
Manage security tokens and session access.

#### `POST /login/access-token`
- **Functionality**: Authenticates a user and returns an OAuth2 compatible JWT access token.
- **Input Parameters**:
  - `username` (Form Data): User email address.
  - `password` (Form Data): User password.
- **Return Data**: JSON object containing `access_token` and `token_type` (default: `bearer`).
- **Logic**: Validates credentials against hashed passwords in PostgreSQL and generates a timed JWT.

### 2. User Management (`/api/v1/users`)
Endpoints for creating and managing platform users.

#### `GET /me`
- **Functionality**: Returns profile information for the currently authenticated user.
- **Auth**: Required (User or Admin).
- **Return Data**: `UserResponse` object (email, full_name, role, etc.).

#### `GET /`
- **Functionality**: Lists all active users in the system.
- **Auth**: **Admin only**.
- **Return Data**: Array of `UserResponse` objects.

#### `POST /`
- **Functionality**: Creates a new user account with hashed password security.
- **Auth**: **Admin only**.
- **Input Body**: `UserCreate` (email, password, full_name, role, is_active).

### 3. Inventory Management (`/api/v1/products`)
Manage the product catalog and stock levels.

#### `GET /`
- **Functionality**: Retrieves all active products in the database.
- **Return Data**: Array of `ProductResponse` objects including SKU and stock quantity.

#### `POST /`
- **Functionality**: Adds a new product to the catalog.
- **Auth**: **Admin only**.
- **Input Body**: `ProductCreate` (name, sku, price, category, stock_quantity).

### 4. Order Transactions (`/api/v1/orders`)
Handles the full lifecycle of customer purchases.

#### `POST /`
- **Functionality**: Initiates a new purchase transaction.
- **Input Body**: `OrderCreate` (customer_id, product_id, quantity).
- **Logic**: Performs an atomic check on stock levels -> deducts inventory -> snapshots current price -> creates order record.

#### `PATCH /{order_id}/status`
- **Functionality**: Transitions an order through its lifecycle (Pending -> Shipped -> Delivered).
- **Auth**: **Admin only**.
- **Input Body**: `OrderUpdate` (status).

#### `GET /analytics/revenue`
- **Functionality**: Returns date-wise aggregated revenue for timeline charting.
- **Logic**: Executes a high-performance SQL `GROUP BY` on the `created_at` timestamp.

### 5. AI & Intelligence (`/api/v1/analytics`)
Advanced data endpoints powered by Machine Learning and Generative AI.

#### `GET /insights`
- **Functionality**: Generates high-level business intelligence alerts.
- **Return Data**: Summary of top-selling products, highest-revenue customers, and critical low-stock warnings.
- **Logic**: Multi-table SQL joins and data aggregation.

#### `GET /ml-revenue-forecast`
- **Functionality**: Generates a 30-day algorithmic revenue projection.
- **Logic**: Collects historical daily revenue -> fits a **Scikit-Learn Linear Regression** model -> extrapolates future trajectories.

#### `POST /chat`
- **Functionality**: Natural language assistant interface.
- **Input Body**: `ChatRequest` (the natural language question).
- **Logic**: Retrieves relevant live database state -> injects into a prompt -> returns a reasoning-based answer from **Google Gemini**.

#### `GET /anomalies`
- **Functionality**: Detects operational and financial outliers.
- **Logic**:
  - **Orders**: Uses **Isolation Forest** (Unsupervised ML) to flag unusual quantity/price clusters.
  - **Revenue**: Uses **Z-Score** statistical analysis to detect abnormal day-over-day volatility.
