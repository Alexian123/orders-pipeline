-- Raw storage
CREATE TABLE IF NOT EXISTS orders_raw (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    text GENERATED ALWAYS AS (raw_data ->> 'order_id') STORED,
    raw_data    jsonb NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now()
);

-- Cleaned orders storage
CREATE TABLE IF NOT EXISTS orders_clean (
    order_id            text PRIMARY KEY,
    customer_id         text,
    customer_email      text,
    order_ts            timestamptz,
    status              text,
    channel             text,
    sku                 text,
    product_name        text,
    category            text,
    qty                 integer,
    unit_price          numeric(12, 2),
    currency            text,
    country             text,
    fx_reference_date   date,
    line_total          numeric(14, 2),
    is_flagged          boolean NOT NULL DEFAULT false,
    flag_reason         text,
    cleaned_at          timestamptz NOT NULL DEFAULT now()
);

-- Daily FX rates storage
CREATE TABLE IF NOT EXISTS fx_rates (
    rate_date       date NOT NULL,
    base_currency   text NOT NULL DEFAULT 'EUR',
    currency        text NOT NULL,
    rate            numeric(18,8) NOT NULL,
    fetched_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (rate_date, base_currency, currency)
);
