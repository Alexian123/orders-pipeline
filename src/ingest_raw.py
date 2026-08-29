import logging
import json
import requests
from sqlalchemy import text
from src.db import engine
from src.config import ORDERS_ENDPOINT

logger = logging.getLogger(__name__)

def fetch_orders() -> list[dict]:
    logger.info(f"Fetching orders from {ORDERS_ENDPOINT}")
    resp = requests.get(ORDERS_ENDPOINT, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f"Fetched {len(data)} orders")
    return data

def load_orders_raw(orders: list[dict]) -> int:
    logger.info(f"Loading {len(orders)} orders into orders_raw table")
    sql = text("""
        INSERT INTO orders_raw (raw_data)
        VALUES (:raw_data)
    """)
    with engine.begin() as conn:
        for row in orders:
            conn.execute(sql, {"raw_data": json.dumps(row)})
    logger.info(f"Loaded {len(orders)} rows into orders_raw")
    return len(orders)

if __name__ == "__main__":
    orders = fetch_orders()
    load_orders_raw(orders)