import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
ORDERS_ENDPOINT = os.environ["ORDERS_ENDPOINT"]