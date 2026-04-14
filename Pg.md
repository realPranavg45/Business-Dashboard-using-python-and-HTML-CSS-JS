# Business Analytics Platform 🚀

A highly resilient, high-performance, and AI-driven **Strategic Analytics Dashboard** designed to act as an executive command center. This platform provides real-time business intelligence, predictive machine learning forecasting, robust anomaly detection, and deep AI-driven conversational insights using Google Gemini.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Key Features](#key-features)
4. [API Reference & Functional Overview](#api-reference--functional-overview)
5. [Development & Setup](#development--setup)

---

## Project Overview
The Smart Business Analytics Platform transforms raw transactional data into actionable strategic intelligence. Designed for scalability, it handles high-concurrency environments while maintaining stability using advanced retry policies, graceful fallbacks, and multi-variate ML predictions. The frontend features a stunning, premium responsive user interface that switches seamlessly between light and dark themes.

---

## Architecture & Tech Stack

### Backend
*   **Framework**: FastAPI (Python)
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy
*   **AI Integration**: Google GenAI SDK (`gemini-2.0-flash` / `gemini-1.5-flash` with robust exponential backoff retry logic and fallback mechanisms)
*   **Machine Learning**: `scikit-learn` / `numpy` for predictive analytics and anomaly detection.
*   **Web Server**: Uvicorn

### Frontend
*   **Core**: Vanilla HTML5, CSS3, JavaScript (ES6)
*   **Charting**: Chart.js (Interactive Data Visualization)
*   **Icons**: Lucide Icons
*   **Design Paradigm**: Glassmorphism, 8px grid system, fully responsive UI designed for large-scale data viewing without pagination fatigue.

---

## Key Features

### 1. 🎛️ Executive Command Center (UI / UX)
A high-density card-based user interface optimized for C-level executives. 
*   **Data Explorer**: Replaced static limits with advanced server-side pagination, sorting, and multi-layered filtering.
*   **Theme Engine**: Built-in sleek dark mode and light mode, gracefully shifting DOM variables to maintain top-tier visual contrast.

### 2. 🤖 AI Chatbot & AI Pulse
Powered by Google Gemini models, the platform proactively analyzes underlying database state to surface critical business alerts.
*   **Smart Advice API**: Context-aware business insights with prioritized severities (Critical, Warning, Opportunity).
*   **Conversational Drill-downs**: Integrated AI Chatbot lets users ask live questions about real-time historical data.
*   **Resiliency**: Integrated 5-tier Exponential Backoff retry logic to handle Gemini API `503 Service Unavailable` spikes, ensuring the dashboard never crashes during API throttling.

### 3. 📈 Machine Learning Revenue Forecasting
Multi-variate ML Inference models process past revenue volume to predict forward-looking performance metrics.
*   **Scenario Simulator (What-If)**: Pluggable sliders allow executives to adjust `Price` and `Volume` adjustments to dynamically view net impact on predicted cash flows.

### 4. 🕵️ Real-time Anomaly Detection
Background intelligent routines scan streaming order velocities and cart values to detect statistical outliers.
*   **Event Log**: Highlights irregularities in payment sizes, volume throughputs, or unusual demographic concentrations.

---

## API Reference & Functional Overview

### 1. Analytics & Intelligence (`/api/v1/analytics`)
This module handles all strategic calculations.

*   `GET /strategic`:
    *   **Functionality**: Returns foundational Key Performance Indicators (KPIs) like Revenue Growth, Customer Retention, Churn Rate, and Active Customers. Includes WoW/MoM delta comparisons.
*   `GET /ml-revenue-forecast`:
    *   **Functionality**: Returns historical training data paired with future AI-predicted revenue timelines using regressors/moving averages.
*   `GET /what-if-forecast`:
    *   **Functionality**: Accepts query params `price_mult` and `volume_mult`. Uses the ML forecast pipeline to simulate strategic price hikes or volume drops.
*   `GET /fulfillment-funnel`:
    *   **Functionality**: Calculates conversion bottlenecks by tracking orders from creation, shipping, to delivery.
*   `GET /customer-value`:
    *   **Functionality**: Groups customers into tiers (Enterprise, SME, Retail) and calculates Lifetime Value (LTV) distributions.
*   `GET /insights`:
    *   **Functionality**: Hits the Gemini API to analyze the current database state and generate an 'AI Pulse' (Strategic Feed). Returns graceful JSON fallbacks if the external AI service drops.
*   `GET /anomalies`:
    *   **Functionality**: Returns a ledger of recent high-precision outliers detected by the system's statistical boundary engine for security and fraud deterrence.
*   `POST /chat`:
    *   **Functionality**: Accepts conversational user prompts and returns database-aware analytical advice based on dynamic AI function calling.

### 2. Order Management (`/api/v1/orders`)
*   `GET /`: List orders with limit, offset, sorting, and global date filters. Casts SQLAlchemy `Enum` statuses to string for robust search (`ILIKE`).
*   `POST /`: Creates new transactions, verifies product inventory stock, and automatically deducts quantities.
*   `GET /{order_id}`: Fetches specific order and its nested buyer/product associations.
*   `PATCH /{order_id}/status`: Admin endpoint to advance checkout state (e.g., pending -> shipped).
*   `DELETE /{order_id}`: Cancels an order and replenishes the system inventory lock.

### 3. Catalog Management (`/api/v1/products`)
*   `GET /`: View SKUs, names, categorical divisions, and active inventory levels.
*   `POST /`: Register new product inventory into the master registry.

### 4. Client Registry (`/api/v1/users`)
*   `GET /`: Fetches enterprise and retail user demographics.
*   `POST /`: Onboards direct accounts dynamically.

---

## Development & Setup

1. **Clone & Virtual Environment**
   \`\`\`bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   \`\`\`

2. **Dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Database**
   * Make sure PostgreSQL is running.
   * Edit \`.env\` or \`app/core/config.py\` with the correct database connection strings.
   * Make sure \`GENAI_API_KEY\` is provided in the configuration to boot up AI endpoints.

4. **Launch Backend**
   \`\`\`bash
   uvicorn app.main:app --reload
   \`\`\`

5. **Access**
   * UI Dashboard: Navigate browser to \`http://localhost:8000/frontend/index.html\`
   * API OpenAPI Docs: Navigate to \`http://localhost:8000/docs\`
