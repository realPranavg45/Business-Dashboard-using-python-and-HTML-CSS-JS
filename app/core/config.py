"""
app/core/config.py
------------------
Centralized application configuration using Pydantic BaseSettings.

WHY: Instead of hardcoding values or scattering os.getenv() calls everywhere,
we use a single Settings class. Pydantic validates types automatically and loads
from the .env file. This is the industry-standard approach (12-Factor App principle).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "Smart Business Analytics Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str

    # --- JWT Security ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- Gemini AI ---
    GEMINI_API_KEY: str = ""
    GENAI_MODEL: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a single, importable instance used throughout the app.
# Usage: from app.core.config import settings
settings = Settings()

