from sqlalchemy import text
from src.db import engine

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(text("refresh materialized view concurrently mv_customer_spend_eur"))
        conn.execute(text("refresh materialized view concurrently mv_country_category_revenue"))
    print("Materialized views refreshed")