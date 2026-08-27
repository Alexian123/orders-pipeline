from sqlalchemy import text

from src.db import engine

def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar() == 1

def test_orders_raw_table_exists():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'orders_raw'
                )
            """)
        )

        assert result.scalar() is True