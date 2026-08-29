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
    customer_id         bigint,
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

-- Customer spend in EUR materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_customer_spend_eur AS
SELECT
    oc.customer_id,
    max(oc.customer_email) AS customer_email,
    round(
        sum(
            CASE
                WHEN oc.currency = 'EUR' THEN oc.line_total
                ELSE oc.line_total / fx.rate
            END
        ), 2
    ) AS total_spend_eur,
    count(*) AS order_count
FROM orders_clean oc
LEFT JOIN lateral (
    SELECT fx.rate
    FROM fx_rates fx
    WHERE fx.currency = oc.currency
      AND fx.rate_date <= oc.fx_reference_date
    ORDER BY fx.rate_date DESC
    LIMIT 1
) fx ON oc.currency <> 'EUR'
WHERE oc.is_flagged = false AND oc.status <> 'refunded'
GROUP BY oc.customer_id;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_customer_spend_eur ON mv_customer_spend_eur(customer_id);

-- Country revenue for Books/Electronics, >€40k, ranked
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_country_category_revenue AS
WITH per_order_eur AS (
    SELECT
        oc.country,
        CASE
            WHEN oc.currency = 'EUR' THEN oc.line_total
            ELSE oc.line_total / fx.rate
        END AS eur_amount
    FROM orders_clean oc
    LEFT JOIN lateral (
        SELECT fx.rate
        FROM fx_rates fx
        WHERE fx.currency = oc.currency
          AND fx.rate_date <= oc.fx_reference_date
        ORDER BY fx.rate_date DESC
        LIMIT 1
    ) fx ON oc.currency <> 'EUR'
    WHERE oc.category IN ('Books', 'Electronics')
      AND oc.is_flagged = false AND oc.status <> 'refunded'
)
SELECT
    country,
    round(sum(eur_amount), 2) AS revenue_eur,
    rank() OVER (ORDER BY sum(eur_amount) DESC) AS revenue_rank
FROM per_order_eur
GROUP BY country
HAVING sum(eur_amount) > 40000
ORDER BY revenue_eur DESC;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_country_category_revenue ON mv_country_category_revenue(country);