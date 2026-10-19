"""
Optional MySQL persistence layer for Student Buddy AI.

The application works perfectly without MySQL.  When MySQL credentials
are supplied (via ``.streamlit/secrets.toml`` or environment variables),
this module stores interaction history in the database so it persists
across browser sessions.

All queries use parameterized statements — user input is **never**
concatenated into SQL strings.
"""

import datetime
import uuid
from typing import Dict, List, Optional

import config

# mysql-connector-python is optional — import lazily
_mysql_connector = None


def _get_connector():
    """Lazy‑import ``mysql.connector`` so the app doesn't crash if it's
    not installed."""
    global _mysql_connector
    if _mysql_connector is None:
        try:
            import mysql.connector  # type: ignore
            _mysql_connector = mysql.connector
        except ImportError:
            _mysql_connector = False  # Mark as unavailable
    return _mysql_connector if _mysql_connector else None


class DatabaseConnection:
    """Manages a MySQL connection and interaction‑history CRUD operations."""

    def __init__(self) -> None:
        self._connection = None
        self._available = False
        self._error_message: str = ""

        if not config.is_mysql_enabled():
            self._error_message = "MySQL is not configured. Running in session‑only mode."
            return

        connector = _get_connector()
        if connector is None:
            self._error_message = (
                "mysql-connector-python is not installed. "
                "Install it with: pip install mysql-connector-python"
            )
            return

        try:
            cfg = config.get_mysql_config()
            self._connection = connector.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                connection_timeout=10,
            )
            self._available = True
            self._ensure_tables()
        except Exception as exc:
            self._error_message = f"MySQL connection failed: {exc}"
            self._connection = None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str:
        return self._error_message

    # ------------------------------------------------------------------
    # Table setup
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create the interaction‑history table if it doesn't exist."""
        if not self._available:
            return
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    session_id  VARCHAR(64)   NOT NULL,
                    action      VARCHAR(50)   NOT NULL,
                    language    VARCHAR(20)   NOT NULL DEFAULT 'Python',
                    question    TEXT          NOT NULL,
                    response    MEDIUMTEXT    NOT NULL,
                    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self._connection.commit()
            cursor.close()
        except Exception as exc:
            self._error_message = f"Table creation failed: {exc}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save_interaction(
        self,
        session_id: str,
        action: str,
        language: str,
        question: str,
        response: str,
    ) -> bool:
        """Persist a single interaction.  Returns ``True`` on success."""
        if not self._available:
            return False
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                INSERT INTO interaction_history
                    (session_id, action, language, question, response, created_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    action,
                    language,
                    question[:5000],        # Truncate very long inputs
                    response[:50000],
                    datetime.datetime.now(),
                ),
            )
            self._connection.commit()
            cursor.close()
            return True
        except Exception:
            return False

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve recent interactions for *session_id*."""
        if not self._available:
            return []
        try:
            cursor = self._connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT action, language, question, response, created_at
                FROM   interaction_history
                WHERE  session_id = %s
                ORDER  BY created_at DESC
                LIMIT  %s
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Exception:
            return []

    def clear_history(self, session_id: str) -> bool:
        """Delete all history for *session_id*.  Returns ``True`` on success."""
        if not self._available:
            return False
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "DELETE FROM interaction_history WHERE session_id = %s",
                (session_id,),
            )
            self._connection.commit()
            cursor.close()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the database connection if open."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
            self._available = False


def generate_session_id() -> str:
    """Generate a unique anonymous session identifier."""
    return uuid.uuid4().hex[:16]
