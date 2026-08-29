import datetime as dt
import requests
from sqlalchemy import text
from src.db import engine
from src.config import FX_BASE_CURRENCY, FX_RATES_API_URL

API_URL = f"{FX_RATES_API_URL}/{{start}}..{{end}}"

def get_order_date_bounds() -> tuple[dt.date, dt.date]:
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                min(fx_reference_date) AS start_date,
                max(fx_reference_date) AS end_date
            FROM orders_clean
        """)).fetchone()
    return row.start_date, row.end_date

def fetch_fx_range(
    start: dt.date,
    end: dt.date,
    base: str = FX_BASE_CURRENCY,
) -> dict:
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

    return resp.json()["rates"]

def upsert_fx(rates: dict, base: str = FX_BASE_CURRENCY):
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

if __name__ == "__main__":
    start, end = get_order_date_bounds()
    rates = fetch_fx_range(start, end)
    upsert_fx(rates)
    print(f"Upserted FX rates for {start} .. {min(end, __import__('datetime').date.today())}")