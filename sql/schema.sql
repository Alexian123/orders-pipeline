-- Raw storage
CREATE TABLE IF NOT EXISTS orders_raw (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    text GENERATED ALWAYS AS (raw_data ->> 'order_id') STORED,
    raw_data    jsonb NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_orders_raw_order_id
    ON orders_raw(order_id);