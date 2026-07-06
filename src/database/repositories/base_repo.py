"""Shared DB access for all repositories."""
from ..connection import DatabaseConnection


class BaseRepository:
    """Provides self.db = singleton DatabaseConnection to subclasses."""

    def __init__(self, db: DatabaseConnection = None):
        self.db = db or DatabaseConnection.get_instance()
