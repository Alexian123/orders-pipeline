import logging
import datetime as dt
import requests
from sqlalchemy import text
from src.db import engine
from src.config import FX_BASE_CURRENCY, FX_RATES_API_URL

API_URL = f"{FX_RATES_API_URL}/{{start}}..{{end}}"

logger = logging.getLogger(__name__)

def get_order_date_bounds() -> tuple[dt.date, dt.date]:
    logger.info("Fetching order date bounds from orders_clean table")
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                min(fx_reference_date) AS start_date,
                max(fx_reference_date) AS end_date
            FROM orders_clean
        """)).fetchone()
    logger.info(f"Order date bounds: {row.start_date} to {row.end_date}")
    return row.start_date, row.end_date

def fetch_fx_range(
    start: dt.date,
    end: dt.date,
    base: str = FX_BASE_CURRENCY,
) -> dict:
    logger.info(f"Fetching FX rates from {start} to {end} with base currency {base}")
    end_capped = min(end, dt.date.today())

    url = API_URL.format(
        start=start.isoformat(),
        end=end_capped.isoformat(),
    )

    resp = requests.get(
        url,
        params={
            "base": base,
            "symbols": "RON",
        },
        timeout=60,
    )

    resp.raise_for_status()

    logger.info(f"Fetched FX rates for {start} to {end_capped}")
    return resp.json()["rates"]

def upsert_fx(rates: dict, base: str = FX_BASE_CURRENCY):
    logger.info(f"Upserting FX rates into fx_rates table for base currency {base}")
    sql = text("""
        INSERT INTO fx_rates (rate_date, base_currency, currency, rate)
        VALUES (:rate_date, :base, :currency, :rate)
        ON CONFLICT (rate_date, base_currency, currency)
        DO UPDATE SET rate = excluded.rate, fetched_at = now()
    """)
    with engine.begin() as conn:
        for date_str, currency_map in rates.items():
            for currency, rate in currency_map.items():
                conn.execute(sql, {"rate_date": date_str, "base": base, "currency": currency, "rate": rate})
    logger.info(f"Upserted FX rates for {len(rates)} dates into fx_rates table")

if __name__ == "__main__":
    start, end = get_order_date_bounds()
    rates = fetch_fx_range(start, end)
    upsert_fx(rates)