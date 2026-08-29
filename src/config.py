import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
ORDERS_ENDPOINT = os.environ["ORDERS_ENDPOINT"]
FX_RATES_API_URL = os.environ.get("FX_RATES_API_URL", "https://api.frankfurter.dev/v1")
FX_BASE_CURRENCY = os.environ.get("FX_BASE_CURRENCY", "EUR")