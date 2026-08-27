import json
import requests
from sqlalchemy import text
from src.db import engine
from src.config import ORDERS_ENDPOINT

def fetch_orders() -> list[dict]:
    resp = requests.get(ORDERS_ENDPOINT, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data

def load_orders_raw(orders: list[dict]) -> int:
    sql = text("""
        insert into orders_raw (raw_data)
        values (:raw_data)
    """)
    with engine.begin() as conn:
        for row in orders:
            conn.execute(sql, {"raw_data": json.dumps(row)})
    return len(orders)

if __name__ == "__main__":
    orders = fetch_orders()
    n = load_orders_raw(orders)
    print(f"Loaded/updated {n} rows into orders_raw")