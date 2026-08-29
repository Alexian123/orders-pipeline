import datetime as dt

import pytest
import requests
from sqlalchemy import text

from src.pull_fx_rates import (
    get_order_date_bounds,
    fetch_fx_range,
    upsert_fx,
)
from src.db import engine
from src.config import FX_BASE_CURRENCY


def test_get_order_date_bounds():
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO orders_clean (
                order_id,
                customer_id,
                customer_email,
                order_ts,
                status,
                channel,
                sku,
                product_name,
                category,
                qty,
                unit_price,
                currency,
                country,
                fx_reference_date,
                line_total,
                is_flagged,
                flag_reason
            )
            VALUES
            (
                'TEST-FX-1',
                'C001',
                'test1@example.com',
                '2024-01-10 12:00:00+00',
                'completed',
                'web',
                'SKU-AB-123',
                'Test Product',
                'Test',
                1,
                10,
                'EUR',
                'RO',
                '2024-01-05',
                10,
                FALSE,
                NULL
            ),
            (
                'TEST-FX-2',
                'C002',
                'test2@example.com',
                '2024-01-20 12:00:00+00',
                'completed',
                'web',
                'SKU-CD-456',
                'Test Product 2',
                'Test',
                1,
                20,
                'EUR',
                'RO',
                '2024-01-25',
                20,
                FALSE,
                NULL
            )
        """))

    start, end = get_order_date_bounds()

    assert start <= dt.date(2024, 1, 5)
    assert end >= dt.date(2024, 1, 25)


def test_fetch_fx_range(monkeypatch):
    expected_rates = {
        "2024-01-01": {
            "USD": 1.10,
            "GBP": 0.85,
        },
        "2024-01-02": {
            "USD": 1.09,
            "GBP": 0.86,
        },
    }

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "rates": expected_rates
            }

    def mock_get(url, params=None, timeout=None):
        assert "2024-01-01..2024-01-02" in url
        assert params["base"] == FX_BASE_CURRENCY
        assert timeout == 60

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)

    result = fetch_fx_range(
        dt.date(2024, 1, 1),
        dt.date(2024, 1, 2),
    )

    assert result == expected_rates


def test_fetch_fx_range_caps_future_date(monkeypatch):
    captured = {}

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "rates": {}
            }

    def mock_get(url, params=None, timeout=None):
        captured["url"] = url
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)

    future_date = dt.date.today() + dt.timedelta(days=30)

    fetch_fx_range(
        dt.date(2024, 1, 1),
        future_date,
    )

    assert dt.date.today().isoformat() in captured["url"]
    assert future_date.isoformat() not in captured["url"]


def test_fetch_fx_range_http_error(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            raise requests.HTTPError("API request failed")

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)

    with pytest.raises(requests.HTTPError):
        fetch_fx_range(
            dt.date(2024, 1, 1),
            dt.date(2024, 1, 2),
        )


def test_upsert_fx():
    test_date = "2099-01-01"

    rates = {
        test_date: {
            "USD": 1.10,
            "GBP": 0.85,
        }
    }

    upsert_fx(rates)

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT currency, rate
                FROM fx_rates
                WHERE rate_date = :date
                  AND base_currency = :base
                ORDER BY currency
            """),
            {
                "date": test_date,
                "base": FX_BASE_CURRENCY,
            },
        ).fetchall()

    assert len(rows) == 2

    result = {
        row.currency: float(row.rate)
        for row in rows
    }

    assert result["USD"] == 1.10
    assert result["GBP"] == 0.85


def test_upsert_fx_updates_existing_rate():
    test_date = "2099-01-02"

    upsert_fx({
        test_date: {
            "USD": 1.10,
        }
    })

    upsert_fx({
        test_date: {
            "USD": 1.25,
        }
    })

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT rate
                FROM fx_rates
                WHERE rate_date = :date
                  AND base_currency = :base
                  AND currency = 'USD'
            """),
            {
                "date": test_date,
                "base": FX_BASE_CURRENCY,
            },
        ).fetchone()

    assert row is not None
    assert float(row.rate) == 1.25