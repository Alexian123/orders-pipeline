import logging
from src.ingest_raw import fetch_orders, load_orders_raw
from src.clean_orders import load_raw, clean, write_clean
from src.pull_fx_rates import get_order_date_bounds, fetch_fx_range, upsert_fx
from sqlalchemy import text
from src.db import engine

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting pipeline...")

    logger.info("Fetching raw orders...")
    orders = fetch_orders()
    logger.info(f"Fetched {len(orders)} orders.")
    logger.info("Loading raw orders into database...")
    load_orders_raw(orders)
    logger.info("Raw orders loaded.")

    logger.info("Cleaning orders...")
    raw_df = load_raw()
    clean_df = clean(raw_df)
    write_clean(clean_df)
    logger.info("Orders cleaned.")

    logger.info("Fetching FX rates...")
    start, end = get_order_date_bounds()
    rates = fetch_fx_range(start, end)
    upsert_fx(rates)
    logger.info("FX rates updated.")

    logger.info("Refreshing materialized views...")
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_spend_eur"))
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_category_revenue"))
    logger.info("Materialized views refreshed.")

    logger.info("Pipeline complete.")

if __name__ == "__main__":
    main()