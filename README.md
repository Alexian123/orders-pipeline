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
    - missing customer_id -> will try to determine from the email, otherwise will be excluded and flagged
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


5. **Country/category breakdown**: refresh materialized view of country revenue for Books/Electronics over €40k
```base
# make sure to fetch the latest fx rates
python src/refresh_views.py
```

### Run Full Pipeline
- Run all steps from above in one command
```base
# Run once locally after making sure the tables/views exist and are empty
python src/run_all.py
```


## Summary


### Data issues encountered and how they were handled

Profiling of `orders_raw` identified several data quality issues. Trailing whitespace was found in multiple text fields, so values are trimmed before being stored in the cleaned table. Case inconsistencies are normalized to consistent casing.

Some orders were missing a `customer_id`. When an email address was available, I used other records with the same email to infer the customer ID. If no matching customer ID could be found, the order remains flagged as having a missing customer ID and is excluded from the analytical views. This avoids assigning an unreliable customer ID.

There were also invalid values such as extremely high unit prices (`999999`) and non-positive quantities or prices. These records are flagged and excluded from analytical calculations because they would otherwise distort revenue and customer-spend results. Orders with status `test` are handled similarly.

Timestamps appeared both as ISO-formatted strings and Unix epoch seconds, so they are parsed and converted to PostgreSQL-compatible timestamps. Duplicate `order_id` values were found, so only the most recent record according to `order_ts` is retained.

Missing categories are normally filled using the category associated with another record having the same SKU. If no category can be inferred, the value is set to `Misc`. SKU formatting inconsistencies are normalized to the standard `SKU-XX-XXX` format.

For the analytical materialized views, refunded orders are excluded because they should not contribute to customer spend or revenue. Currency conversion is performed using the historical EUR/RON exchange rate applicable on or before the order's reference date.

Profiling of `orders_clean` proves the resolution of the data inconsistencies mentioned above as well as the flagging of bad records.

### Production monitoring

The daily FX refresh is automated using a GitHub Actions scheduled workflow. The pipeline uses Python logging instead of relying only on `print()` statements, with information written to both the console and a log file.

If the daily job silently failed, I would detect it through the GitHub Actions workflow status and logs. A failed Python command causes the workflow to exit with a non-zero status, making the workflow appear as failed in GitHub Actions. The logs can then be inspected to identify where the failure occurred. In addition, GitHub notifies me via email in case an automated workflow fails.

For a production system, I would improve this further by adding data-quality checks after each run, such as verifying that new FX rates were loaded and that the materialized views were successfully refreshed.

### AI usage

I used AI assistance during development for SQL queries, environment and project setup, and configuring the GitHub Actions workflow. I also used it to help structure parts of the data-cleaning and testing code.

I did not blindly use the generated solutions. I compared the suggestions with the results of my own profiling and changed the implementation where necessary. For example, the cleaning rules for customer ID inference, invalid prices, duplicate orders, SKU normalization, missing categories, and refunded orders were based on the issues I actually found in the dataset. The final decisions and business rules were therefore determined by the profiling results and the requirements of the assignment rather than by AI suggestions alone.

In addition, I used AI to help structure and improve readability of this very text, with the core ideas composed by myself.

The following LLM's were used: OpenAI's GPT-5.6 Luna and Anthropic's Claude Sonnet 5.