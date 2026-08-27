# orders-pipeline

## Project Setup
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

- If using docker:
```bash
docker-compose up -d
```

- Apply schema:
```bash
psql "$DATABASE_URL" -f sql/schema.sql
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