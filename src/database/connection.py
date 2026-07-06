"""Database connection management.
- Ensures only one database connection exists throughout the application.
- Thread-safe (for single-threaded Qt main thread usage).
"""

import sqlite3
import os
from threading import Lock


class DatabaseConnection:
    """Global database connection (one per process).

    Usage:
        db = DatabaseConnection.get_instance()
        db.execute("SELECT * FROM courses")
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        if db_path is None:
            # Default to project root
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "pdptool.db"
            )
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._initialized = True

    @classmethod
    def get_instance(cls, db_path: str = None) -> "DatabaseConnection":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = DatabaseConnection(db_path)
        return cls._instance

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the underlying sqlite3 connection."""
        return self._conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement."""
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        self._conn.commit()
        return cursor

    def execute_many(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        cursor = self._conn.cursor()
        cursor.executemany(sql, params_list)
        self._conn.commit()
        return cursor

    def fetch_all(self, sql: str, params: tuple = ()) -> list:
        """Fetch all rows from a query."""
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def fetch_one(self, sql: str, params: tuple = ()):
        """Fetch a single row from a query."""
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()

    @classmethod
    def reset_instance(cls):
        """Reset the singleton (mainly for testing)."""
        if cls._instance:
            cls._instance._conn.close()
        cls._instance = None

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
        DatabaseConnection._instance = None
        self._initialized = False
