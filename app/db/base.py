"""
app/db/base.py
--------------
Central import point for all models.

WHY: Alembic needs to "see" all your models to generate migrations.
By importing them here, we guarantee that when Alembic runs, it has
a complete picture of the schema. This pattern is critical for avoiding
"table not found" migration errors.
"""
from app.db.database import Base  # noqa: F401

# Import all models below so Alembic can detect them
from app.models.user import User          # noqa: F401
from app.models.product import Product    # noqa: F401
from app.models.order import Order        # noqa: F401
