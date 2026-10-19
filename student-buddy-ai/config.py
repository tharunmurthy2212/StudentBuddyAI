"""
Configuration module for Student Buddy AI.

Reads settings from Streamlit secrets (.streamlit/secrets.toml) when available,
and falls back to safe defaults. Controls which AI provider is active and
whether MySQL persistence is enabled.
"""

import os
from typing import Optional


# ---------------------------------------------------------------------------
# AI Provider configuration
# ---------------------------------------------------------------------------

def _read_secret(section: str, key: str, default: str = "") -> str:
    """Read a value from Streamlit secrets, falling back to *default*.

    Streamlit secrets are only available when the app runs inside
    ``streamlit run``.  Outside of that context (e.g. during tests) we
    simply return the default.
    """
    try:
        import streamlit as st  # noqa: F811
        return st.secrets.get(section, {}).get(key, default)
    except Exception:
        return default


def get_ai_provider() -> str:
    """Return the configured AI provider name.

    Valid values: ``"mock"`` (default), ``"xai"``.
    """
    provider = os.environ.get("AI_PROVIDER", "")
    if not provider:
        provider = _read_secret("ai", "provider", "mock")
    provider = provider.strip().lower()
    if provider not in ("mock", "xai"):
        provider = "mock"
    return provider


def get_xai_api_key() -> Optional[str]:
    """Return the xAI API key if configured, otherwise ``None``."""
    key = os.environ.get("XAI_API_KEY", "")
    if not key:
        key = _read_secret("xai", "api_key", "").strip()
    if not key or key.startswith("REPLACE"):
        return None
    return key


def get_xai_model() -> str:
    """Return the xAI model name to use."""
    model = os.environ.get("XAI_MODEL", "")
    if not model:
        model = _read_secret("xai", "model", "grok-2").strip()
    return model or "grok-2"


def get_xai_base_url() -> str:
    """Return the API endpoint base URL (OpenAI-compatible)."""
    base_url = os.environ.get("XAI_BASE_URL", "")
    if not base_url:
        base_url = _read_secret("xai", "base_url", "https://api.x.ai/v1").strip()
    return base_url.rstrip("/") or "https://api.x.ai/v1"


# ---------------------------------------------------------------------------
# MySQL configuration
# ---------------------------------------------------------------------------

def get_mysql_config() -> Optional[dict]:
    """Return MySQL connection parameters if configured, else ``None``.

    Expected secrets.toml section::

        [mysql]
        host = "localhost"
        port = 3306
        user = "student_buddy"
        password = "your_password"
        database = "student_buddy_ai"

    Environment variables ``MYSQL_HOST``, ``MYSQL_PORT``, ``MYSQL_USER``,
    ``MYSQL_PASSWORD``, ``MYSQL_DATABASE`` are checked as a fallback so that
    tests and non‑Streamlit runners can also configure the database.
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        mysql_section = st.secrets.get("mysql", {})
        if mysql_section:
            return {
                "host": mysql_section.get("host", "localhost"),
                "port": int(mysql_section.get("port", 3306)),
                "user": mysql_section.get("user", ""),
                "password": mysql_section.get("password", ""),
                "database": mysql_section.get("database", "student_buddy_ai"),
            }
    except Exception:
        pass

    # Fallback: environment variables
    host = os.environ.get("MYSQL_HOST", "")
    if host:
        return {
            "host": host,
            "port": int(os.environ.get("MYSQL_PORT", 3306)),
            "user": os.environ.get("MYSQL_USER", ""),
            "password": os.environ.get("MYSQL_PASSWORD", ""),
            "database": os.environ.get("MYSQL_DATABASE", "student_buddy_ai"),
        }

    return None


def is_mysql_enabled() -> bool:
    """Return ``True`` when MySQL credentials have been supplied."""
    cfg = get_mysql_config()
    return cfg is not None and bool(cfg.get("user"))


# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------

APP_TITLE = "Student Buddy AI"
APP_SUBTITLE = "Your Personal Coding Learning Assistant"
APP_VERSION = "1.1.0"
SUPPORTED_LANGUAGES = ["Python", "C++", "Java", "JavaScript", "C"]
MAX_HINT_LEVEL = 4

