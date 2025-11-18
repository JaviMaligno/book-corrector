"""
Database migration script - runs automatically on startup.
Adds missing columns to existing database.
"""

import logging

from sqlalchemy import text

from .db import engine

logger = logging.getLogger(__name__)


def run_migrations():
    """Run all pending database migrations."""
    logger.info("Running database migrations...")

    with engine.connect() as conn:
        # Migration 1: Add content_backup column to document table
        try:
            conn.execute(text("ALTER TABLE document ADD COLUMN IF NOT EXISTS content_backup TEXT"))
            conn.commit()
            logger.info("✅ Migration: Added content_backup column to document table")
        except Exception as e:
            logger.warning(f"Migration content_backup: {e}")

    logger.info("✅ Database migrations complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
