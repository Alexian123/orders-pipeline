import pandas as pd
from sqlalchemy import text

from src.clean_orders import parse_ts, parse_sku, clean, write_clean
from src.db import engine


def test_parse_ts_unix_timestamp():
    result = parse_ts("1704067200")

    assert result == pd.Timestamp("2024-01-01 00:00:00", tz="UTC")


def test_parse_ts_iso_timestamp():
    result = parse_ts("2024-01-15T12:30:00Z")

    assert result == pd.Timestamp("2024-01-15 12:30:00", tz="UTC")


def test_parse_ts_with_whitespace():
    result = parse_ts(" 2024-01-15T12:30:00Z ")

    assert result == pd.Timestamp("2024-01-15 12:30:00", tz="UTC")


def test_parse_ts_invalid_value():
    result = parse_ts("not-a-date")

    assert pd.isna(result)


def test_parse_ts_none():
    result = parse_ts(None)

    assert pd.isna(result)


def test_parse_sku():
    assert parse_sku("SKUEL001") == "SKU-EL-001"


def test_parse_sku_with_existing_prefix():
    assert parse_sku("SKU-ab-123") == "SKU-AB-123"


def test_parse_sku_with_separators():
    assert parse_sku("ab_1 2-3") == "SKU-AB-123"


def test_parse_sku_with_whitespace():
    assert parse_sku("  ab123  ") == "SKU-AB-123"


def test_parse_sku_invalid():
    assert parse_sku("ABC") is None
    assert parse_sku("ABC1234") is None


def test_parse_sku_missing():
    assert parse_sku(None) is None
    assert parse_sku(float("nan")) is None


def test_clean_normalizes_text_fields():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": " TEST@EXAMPLE.COM ",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": " COMPLETED ",
            "channel": " WEB ",
            "sku": " ab-123 ",
            "product_name": " blue widget ",
            "category": " electronics ",
            "qty": "2",
            "unit_price": "10.50",
            "currency": " eur ",
            "country": " ro ",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    row = result.iloc[0]

    assert row["customer_id"] == 1
    assert row["customer_email"] == "test@example.com"
    assert row["status"] == "completed"
    assert row["channel"] == "web"
    assert row["product_name"] == "Blue Widget"
    assert row["category"] == "Electronics"
    assert row["currency"] == "EUR"
    assert row["country"] == "RO"
    assert row["sku"] == "SKU-AB-123"


def test_clean_missing_category_becomes_misc():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "001",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": None,
            "qty": 1,
            "unit_price": 10,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert result.iloc[0]["category"] == "Misc"


def test_clean_numeric_columns():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": "2",
            "unit_price": "10.50",
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert result.iloc[0]["qty"] == 2
    assert result.iloc[0]["unit_price"] == 10.50


def test_clean_invalid_numeric_values_become_nan():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": "invalid",
            "unit_price": "invalid",
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert pd.isna(result.iloc[0]["qty"])
    assert pd.isna(result.iloc[0]["unit_price"])


def test_clean_keeps_latest_order():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": 1,
            "customer_email": "old@example.com",
            "order_ts": "2024-01-01T10:00:00Z",
            "status": "pending",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 1,
            "unit_price": 10,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        },
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "new@example.com",
            "order_ts": "2024-01-02T10:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 2,
            "unit_price": 20,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-02",
        }
    ])

    result = clean(df)

    assert len(result) == 1
    assert result.iloc[0]["customer_email"] == "new@example.com"
    assert result.iloc[0]["status"] == "completed"


def test_clean_flags_missing_customer_id():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": None,
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 1,
            "unit_price": 10,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert bool(result.iloc[0]["is_flagged"])
    assert "missing_customer_id" in result.iloc[0]["flag_reason"]


def test_clean_flags_non_positive_values():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": 1,
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": -2,
            "unit_price": 0,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert bool(result.iloc[0]["is_flagged"])
    assert "non_positive_qty" in result.iloc[0]["flag_reason"]
    assert "non_positive_unit_price" in result.iloc[0]["flag_reason"]


def test_clean_flags_unit_price_too_high():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": 1,
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 1,
            "unit_price": 10001,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert bool(result.iloc[0]["is_flagged"])
    assert "unit_price_too_high" in result.iloc[0]["flag_reason"]


def test_clean_flags_test_order():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": " TEST ",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 1,
            "unit_price": 10,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert bool(result.iloc[0]["is_flagged"])
    assert "test_order" in result.iloc[0]["flag_reason"]


def test_clean_line_total():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": -2,
            "unit_price": -10.50,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    # abs() means negative values still produce a positive line total
    assert result.iloc[0]["line_total"] == 21.00


def test_clean_unflagged_order():
    df = pd.DataFrame([
        {
            "order_id": "1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": "2024-01-01T12:00:00Z",
            "status": "completed",
            "channel": "web",
            "sku": "AB123",
            "product_name": "widget",
            "category": "electronics",
            "qty": 2,
            "unit_price": 10,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": "2024-01-01",
        }
    ])

    result = clean(df)

    assert not bool(result.iloc[0]["is_flagged"])
    assert result.iloc[0]["flag_reason"] is None


def test_write_clean():
    df = pd.DataFrame([
        {
            "order_id": "TEST-1",
            "customer_id": "1",
            "customer_email": "test@example.com",
            "order_ts": pd.Timestamp("2024-01-01", tz="UTC"),
            "status": "completed",
            "channel": "web",
            "sku": "SKU-AB-123",
            "product_name": "Widget",
            "category": "Electronics",
            "qty": 2,
            "unit_price": 10.0,
            "currency": "EUR",
            "country": "RO",
            "fx_reference_date": pd.Timestamp("2024-01-01").date(),
            "line_total": 20.0,
            "is_flagged": False,
            "flag_reason": None,
        }
    ])

    write_clean(df)

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM orders_clean WHERE order_id = 'TEST-1'")
        )
        count = result.scalar()

    assert count == 1