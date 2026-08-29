from sqlalchemy import text
from src.db import engine

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(text("refresh materialized view concurrently mv_customer_spend_eur"))
    print("Materialized views refreshed")