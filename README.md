# orders-pipeline

## Environment
- Venv
```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Dependencies
```bash
pip install -r requirements.txt
pip install -e .    # install project module as editable
```

- Env vars
```bash
cp .env.example .env
# make changes in .env
source .env
```

## Database
- Ensure psql is available:
```bash
psql --version
```

- If using docker for test database:
```bash
docker-compose up -d
```

- Apply schema:
```bash
psql "$DATABASE_URL" -f sql/schema.sql
# also run for $TEST_DATABASE_URL
```

- Interactive mode:
```bash
psql "$DATABASE_URL"
# Then inside the prompt:
#   \i sql/schema.sql       -- run the file
#   \dt                     -- list tables
#   \d [some_table]         -- describe a table
#   \dm                     -- list materialized views
#   \q                      -- quit
```

## Tests
- Run tests:
```bash
pytest
```

## Pipeline

### Individual Steps
1. **Ingest**: fetch raw entries from the endpoint and store them in orders_raw along with some metadata
```bash
python ./src/ingest_raw.py

# run profiling queries to inspect the raw data
psql "$DATABASE_URL" -f sql/profile_raw_orders.sql > logs/raw_orders_profiling.txt
```

2. **Clean**: resolve inconsistencies from orders_raw and store the resulting entries in orders_clean
- Detected inconsistencies and their resolutions:
    - trailing whitespace inconsistencies -> values will be trimmed (or parsed if numeric)
    - case inconsistencies -> will be normalized
    - missing customer_id -> will be excluded and flagged
    - unit_price of '999999' -> will be excluded and flagged
    - order_ts as ISO string OR unix epoch seconds -> will be converted to timestamptz
    - negative or zero qty/unit_price -> will be excluded and flagged
    - status "test" -> will be excluded and flagged
    - duplicate order_id -> will keep most recent by order_ts
    - missing category field on some entries -> will be set to "Misc"
    - SKU format inconsistencies -> will converted to "SKU-XX-XXX"
```bash
# inspect logs/raw_orders_profiling.txt for profiling results
python ./src/clean_orders.py

# run profiling queries to inspect the cleaned data
psql "$DATABASE_URL" -f sql/profile_clean_orders.sql > logs/clean_orders_profiling.txt
# inspect logs/clean_orders_profiling.txt for profiling results
```

3. **Exchange rates**: fetch exchange rates from earliest fx_reference_date to the latest fx_reference_date (or today)
- Rates are only needed for RON to EUR exchange, based on the profiling results from orders_raw
```base
python src/pull_fx_rates.py
# this should be re-run daily to pull the latest rates
```

4. **Customer spend in EUR**: refresh materialized view of total amount spent in EUR for each customer
```base
# make sure to fetch the latest fx rates
python src/refresh_views.py
```