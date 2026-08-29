import logging
from sqlalchemy import text
from src.db import engine

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Refreshing materialized views")
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_spend_eur"))
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_category_revenue"))
    logger.info("Materialized views refreshed")