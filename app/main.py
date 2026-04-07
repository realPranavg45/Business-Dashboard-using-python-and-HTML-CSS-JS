"""
app/main.py
-----------
The FastAPI application entry point.

WHY: This is where we create the FastAPI app instance, configure middleware,
include all our routers, and add startup/shutdown events. Keeping this file
clean (only wiring, no logic) is a critical design principle — it makes the
app easy to understand at a glance.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import users, products, orders, auth, analytics

# ─── App Instance ────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A Mini ERP + Analytics Dashboard built with FastAPI",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc UI at /redoc
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
# WHY: Needed if the Streamlit dashboard (different port/origin) talks to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, list your specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routers ──────────────────────────────────────────────────────────────
# WHY: Versioning (/api/v1/...) is industry standard. When you ship
# breaking changes, you create /api/v2/ without removing v1 for existing clients.
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router,     prefix=f"{API_V1_PREFIX}",          tags=["Auth"])
app.include_router(users.router,    prefix=f"{API_V1_PREFIX}/users",    tags=["Users"])
app.include_router(products.router, prefix=f"{API_V1_PREFIX}/products", tags=["Products"])
app.include_router(orders.router,   prefix=f"{API_V1_PREFIX}/orders",   tags=["Orders"])
app.include_router(analytics.router,prefix=f"{API_V1_PREFIX}/analytics",tags=["Analytics"])

# ─── Root Health Check ────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check endpoint — confirms the API is alive."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
