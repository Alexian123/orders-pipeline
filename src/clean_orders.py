import pandas as pd
from sqlalchemy import text
from src.db import engine

def parse_ts(value):
    if value is None:
        return pd.NaT
    s = str(value).strip()
    if s.isdigit():
        # unix epoch seconds
        return pd.to_datetime(int(s), unit="s", utc=True)
    return pd.to_datetime(s, utc=True, errors="coerce")

def parse_sku(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Remove separators
    value = value.replace("-", "").replace("_", "").replace(" ", "")

    # Remove SKU prefix, with or without a separator
    if value.startswith("SKU"):
        value = value[3:]

    # Expected underlying format: XX + XXX
    if len(value) == 5:
        return f"SKU-{value[:2]}-{value[2:]}"

    return None

def load_raw() -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT raw_data FROM orders_raw"), conn)
    return pd.json_normalize(df["raw_data"])

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Trim whitespace and normalize case for text columns
    df["order_id"] = df["order_id"].astype(str).str.strip().str.upper()
    df["customer_email"] = df["customer_email"].astype(str).str.strip().str.lower()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["channel"] = df["channel"].astype(str).str.strip().str.lower()
    df["product_name"] = df["product_name"].astype(str).str.strip().str.title()
    df["currency"] = df["currency"].astype(str).str.strip().str.upper()
    df["country"] = df["country"].astype(str).str.strip().str.upper()

    # Normalize SKU
    df["sku"] = df["sku"].apply(parse_sku)

    # Normalize category
    df["category"] = df["category"].apply(
        lambda x: x.strip().title() if isinstance(x, str) and x.strip() else None
    )

    # Build SKU -> category mapping from records that already have a category
    sku_category_map = (
        df.loc[
            df["sku"].notna() & df["category"].notna(),
            ["sku", "category"]
        ]
        .drop_duplicates()
        .groupby("sku")["category"]
        .first()
        .to_dict()
    )

    # Fill missing categories using another record with the same SKU
    missing_category = df["category"].isna()

    df.loc[missing_category, "category"] = (
        df.loc[missing_category, "sku"].map(sku_category_map)
    )

    # If no matching SKU was found, use Misc
    df["category"] = df["category"].fillna("Misc")

    # Parse timestamps
    df["order_ts"] = df["order_ts"].apply(parse_ts)
    df["fx_reference_date"] = pd.to_datetime(df["fx_reference_date"], errors="coerce").dt.date

    # Parse numeric columns, coercing errors to NaN
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Keep latest order_ts per order_id
    df = df.sort_values("order_ts").drop_duplicates("order_id", keep="last")

    flags = []
    for _, r in df.iterrows():
        reasons = []
        if pd.isna(r["customer_id"]):
            reasons.append("missing_customer_id")
        if pd.notna(r["qty"]) and r["qty"] <= 0:
            reasons.append("non_positive_qty")
        if pd.notna(r["unit_price"]) and r["unit_price"] <= 0:
            reasons.append("non_positive_unit_price")
        if pd.notna(r["unit_price"]) and r["unit_price"] > 10000:
            reasons.append("unit_price_too_high")
        if r["status"] == "test":
            reasons.append("test_order")
        flags.append(", ".join(reasons) if reasons else None)

    df["flag_reason"] = flags
    df["is_flagged"] = df["flag_reason"].notna()
    df["line_total"] = (df["qty"].abs() * df["unit_price"].abs()).round(2)

    keep_cols = [
        "order_id", "customer_id", "customer_email", "order_ts", "status", "channel",
        "sku", "product_name", "category", "qty", "unit_price", "currency", "country",
        "fx_reference_date", "line_total", "is_flagged", "flag_reason",
    ]
    return df[keep_cols]

def write_clean(df: pd.DataFrame):
    with engine.begin() as conn:
        conn.execute(text("truncate table orders_clean"))
        df.to_sql("orders_clean", conn, if_exists="append", index=False, method="multi", chunksize=500)

if __name__ == "__main__":
    raw_df = load_raw()
    clean_df = clean(raw_df)
    write_clean(clean_df)
    print(f"orders_clean: {len(clean_df)} rows, {clean_df['is_flagged'].sum()} flagged")