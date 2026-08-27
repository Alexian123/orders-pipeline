from src.ingest_raw import fetch_orders, load_orders_raw
from sqlalchemy import text
from src.db import engine

def test_fetch_orders(monkeypatch):
    # Mock the requests.get function to return a predefined response
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception("HTTP Error")

    def mock_get(*args, **kwargs):
        return MockResponse([{"order_id": 1}, {"order_id": 2}], 200)

    monkeypatch.setattr("requests.get", mock_get)

    orders = fetch_orders()
    assert isinstance(orders, list)
    assert len(orders) == 2
    assert orders[0]["order_id"] == 1
    assert orders[1]["order_id"] == 2

def test_load_orders_raw():
    # Prepare test data
    test_orders = [{"order_id": 1, "item": "Widget"}, {"order_id": 2, "item": "Gadget"}]

    # Load orders into the database
    n = load_orders_raw(test_orders)

    # Verify that the correct number of rows were loaded
    assert n == len(test_orders)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM orders_raw"))
        count = result.scalar()
        assert count >= len(test_orders)  # Ensure at least the test orders are present