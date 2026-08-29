from src.ingest_raw import fetch_orders, load_orders_raw
from src.clean_orders import load_raw, clean, write_clean
from src.pull_fx_rates import get_order_date_bounds, fetch_fx_range, upsert_fx
from sqlalchemy import text
from src.db import engine

def main():
    print("Starting pipeline...")

    print("Fetching raw orders...")
    orders = fetch_orders()
    print(f"Fetched {len(orders)} orders.")
    print("Loading raw orders into database...")
    load_orders_raw(orders)
    print("Raw orders loaded.")

    print("Cleaning orders...")
    raw_df = load_raw()
    clean_df = clean(raw_df)
    write_clean(clean_df)
    print("Orders cleaned.")

    print("Fetching FX rates...")
    start, end = get_order_date_bounds()
    rates = fetch_fx_range(start, end)
    upsert_fx(rates)
    print("FX rates updated.")

    print("Refreshing materialized views...")
    with engine.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_spend_eur"))
        conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_category_revenue"))
    print("Materialized views refreshed.")

    print("Pipeline complete.")

if __name__ == "__main__":
    main()