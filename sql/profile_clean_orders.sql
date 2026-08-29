-- !!! Run with psql !!!

\echo '=== CLEAN ORDERS PROFILING ==='


-- Row count
\echo ''
\echo '=== TOTAL RECORDS ==='

SELECT COUNT(*) AS total_records
FROM orders_clean;


-- Duplicate order IDs
\echo ''
\echo '=== DUPLICATE ORDER IDS ==='

SELECT
    COUNT(*) AS duplicate_order_ids
FROM (
    SELECT order_id
    FROM orders_clean
    GROUP BY order_id
    HAVING COUNT(*) > 1
) duplicates;


-- Missing required fields
\echo ''
\echo '=== MISSING FIELDS ==='

SELECT
    COUNT(*) AS total_records,

    SUM(CASE
        WHEN order_id IS NULL OR TRIM(order_id) = ''
        THEN 1 ELSE 0
    END) AS missing_order_id,

    SUM(CASE
        WHEN customer_id IS NULL OR TRIM(customer_id::text) = ''
        THEN 1 ELSE 0
    END) AS missing_customer_id,

    SUM(CASE
        WHEN customer_email IS NULL OR TRIM(customer_email) = ''
        THEN 1 ELSE 0
    END) AS missing_customer_email,

    SUM(CASE
        WHEN order_ts IS NULL
        THEN 1 ELSE 0
    END) AS missing_order_ts,

    SUM(CASE
        WHEN status IS NULL OR TRIM(status) = ''
        THEN 1 ELSE 0
    END) AS missing_status,

    SUM(CASE
        WHEN channel IS NULL OR TRIM(channel) = ''
        THEN 1 ELSE 0
    END) AS missing_channel,

    SUM(CASE
        WHEN sku IS NULL OR TRIM(sku) = ''
        THEN 1 ELSE 0
    END) AS missing_sku,

    SUM(CASE
        WHEN product_name IS NULL OR TRIM(product_name) = ''
        THEN 1 ELSE 0
    END) AS missing_product_name,

    SUM(CASE
        WHEN category IS NULL OR TRIM(category) = ''
        THEN 1 ELSE 0
    END) AS missing_category,

    SUM(CASE
        WHEN qty IS NULL
        THEN 1 ELSE 0
    END) AS missing_qty,

    SUM(CASE
        WHEN unit_price IS NULL
        THEN 1 ELSE 0
    END) AS missing_unit_price,

    SUM(CASE
        WHEN currency IS NULL OR TRIM(currency) = ''
        THEN 1 ELSE 0
    END) AS missing_currency,

    SUM(CASE
        WHEN country IS NULL OR TRIM(country) = ''
        THEN 1 ELSE 0
    END) AS missing_country,

    SUM(CASE
        WHEN fx_reference_date IS NULL
        THEN 1 ELSE 0
    END) AS missing_fx_reference_date

FROM orders_clean;


-- Flagged records
\echo ''
\echo '=== FLAGGED RECORDS ==='

SELECT
    COUNT(*) AS total_flagged,

    SUM(CASE
        WHEN is_flagged = TRUE
        THEN 1 ELSE 0
    END) AS flagged_by_boolean,

    SUM(CASE
        WHEN flag_reason IS NOT NULL
        THEN 1 ELSE 0
    END) AS flagged_with_reason

FROM orders_clean;


-- Flag reason distribution
\echo ''
\echo '=== FLAG REASON DISTRIBUTION ==='

SELECT
    flag_reason,
    COUNT(*) AS count
FROM orders_clean
WHERE flag_reason IS NOT NULL
GROUP BY flag_reason
ORDER BY count DESC;


-- Check consistency between is_flagged and flag_reason
\echo ''
\echo '=== FLAG CONSISTENCY ==='

SELECT
    COUNT(*) AS inconsistent_flags
FROM orders_clean
WHERE
       (is_flagged = TRUE AND flag_reason IS NULL)
    OR (is_flagged = FALSE AND flag_reason IS NOT NULL);


-- Non-positive quantities
\echo ''
\echo '=== NON-POSITIVE QUANTITIES ==='

SELECT
    COUNT(*) AS count
FROM orders_clean
WHERE qty <= 0;


-- Non-positive prices
\echo ''
\echo '=== NON-POSITIVE PRICES ==='

SELECT
    COUNT(*) AS count
FROM orders_clean
WHERE unit_price <= 0;


-- Non-positive customer IDs
\echo ''
\echo '=== NON-POSITIVE CUSTOMER IDS ==='

SELECT
    COUNT(*) AS count
FROM orders_clean
WHERE customer_id IS NOT NULL
  AND customer_id::numeric <= 0;


-- Invalid / malformed SKUs
\echo ''
\echo '=== SKU FORMAT ISSUES ==='

SELECT
    COUNT(*) AS count
FROM orders_clean
WHERE sku IS NOT NULL
  AND sku !~ '^SKU-[A-Z0-9]{2}-[A-Z0-9]{3}$';


-- SKU distribution
\echo ''
\echo '=== SKU DISTRIBUTION ==='

SELECT
    sku,
    COUNT(*) AS occurrences
FROM orders_clean
GROUP BY sku
ORDER BY occurrences DESC;


-- Check product/category consistency per SKU
\echo ''
\echo '=== SKUs WITH DIFFERENT PRODUCT NAMES ==='

SELECT
    COUNT(*) AS count
FROM (
    SELECT sku
    FROM orders_clean
    WHERE sku IS NOT NULL
    GROUP BY sku
    HAVING COUNT(DISTINCT TRIM(product_name)) > 1
) inconsistent_skus;


\echo ''
\echo '=== SKUs WITH DIFFERENT CATEGORIES ==='

SELECT
    COUNT(*) AS count
FROM (
    SELECT sku
    FROM orders_clean
    WHERE sku IS NOT NULL
    GROUP BY sku
    HAVING COUNT(DISTINCT TRIM(category)) > 1
) inconsistent_skus;


-- Whitespace inconsistencies
\echo ''
\echo '=== WHITESPACE INCONSISTENCIES ==='

SELECT
    COUNT(*) AS count
FROM orders_clean
WHERE
       order_id       IS DISTINCT FROM TRIM(order_id)
    OR customer_email IS DISTINCT FROM TRIM(customer_email)
    OR status         IS DISTINCT FROM TRIM(status)
    OR channel        IS DISTINCT FROM TRIM(channel)
    OR sku            IS DISTINCT FROM TRIM(sku)
    OR product_name   IS DISTINCT FROM TRIM(product_name)
    OR category       IS DISTINCT FROM TRIM(category)
    OR currency       IS DISTINCT FROM TRIM(currency)
    OR country        IS DISTINCT FROM TRIM(country);


-- Case consistency
\echo ''
\echo '=== CASE NORMALIZATION ISSUES ==='

SELECT
    SUM(CASE WHEN customer_email IS NOT NULL
                  AND customer_email <> LOWER(customer_email)
             THEN 1 ELSE 0 END) AS email_not_lowercase,

    SUM(CASE WHEN status IS NOT NULL
                  AND status <> LOWER(status)
             THEN 1 ELSE 0 END) AS status_not_lowercase,

    SUM(CASE WHEN channel IS NOT NULL
                  AND channel <> LOWER(channel)
             THEN 1 ELSE 0 END) AS channel_not_lowercase,

    SUM(CASE WHEN currency IS NOT NULL
                  AND currency <> UPPER(currency)
             THEN 1 ELSE 0 END) AS currency_not_uppercase,

    SUM(CASE WHEN country IS NOT NULL
                  AND country <> UPPER(country)
             THEN 1 ELSE 0 END) AS country_not_uppercase

FROM orders_clean;


-- Category defaults
\echo ''
\echo '=== MISC CATEGORY ==='

SELECT
    COUNT(*) AS misc_category_count
FROM orders_clean
WHERE category = 'Misc';


-- Invalid dates
\echo ''
\echo '=== INVALID / MISSING DATES ==='

SELECT
    COUNT(*) AS invalid_order_ts
FROM orders_clean
WHERE order_ts IS NULL;


-- Line total validation
\echo ''
\echo '=== LINE TOTAL VALIDATION ==='

SELECT
    COUNT(*) AS incorrect_line_totals
FROM orders_clean
WHERE line_total IS DISTINCT FROM
      ROUND(ABS(qty) * ABS(unit_price), 2);


-- Null line totals
\echo ''
\echo '=== NULL LINE TOTALS ==='

SELECT
    COUNT(*) AS null_line_totals
FROM orders_clean
WHERE line_total IS NULL;


-- Currency distribution
\echo ''
\echo '=== CURRENCY DISTRIBUTION ==='

SELECT
    currency,
    COUNT(*) AS count
FROM orders_clean
GROUP BY currency
ORDER BY count DESC;


-- Status distribution
\echo ''
\echo '=== STATUS DISTRIBUTION ==='

SELECT
    status,
    COUNT(*) AS count
FROM orders_clean
GROUP BY status
ORDER BY count DESC;


-- Channel distribution
\echo ''
\echo '=== CHANNEL DISTRIBUTION ==='

SELECT
    channel,
    COUNT(*) AS count
FROM orders_clean
GROUP BY channel
ORDER BY count DESC;


-- Category distribution
\echo ''
\echo '=== CATEGORY DISTRIBUTION ==='

SELECT
    category,
    COUNT(*) AS count
FROM orders_clean
GROUP BY category
ORDER BY count DESC;


-- Country distribution
\echo ''
\echo '=== COUNTRY DISTRIBUTION ==='

SELECT
    country,
    COUNT(*) AS count
FROM orders_clean
GROUP BY country
ORDER BY count DESC;


-- Unflagged bad records
\echo ''
\echo '=== UNFLAGGED BAD RECORDS ==='

SELECT COUNT(*) AS unflagged_bad_records
FROM orders_clean
WHERE
    (
        customer_id IS NULL
        OR TRIM(customer_id::text) = ''
        OR qty <= 0
        OR unit_price <= 0
        OR unit_price > 100000
        OR LOWER(status) = 'test'
    )
    AND is_flagged = FALSE;


-- Incorrectly flagged records
\echo ''
\echo '=== FLAGGED RECORDS WITH NO FLAGGABLE CONDITION ==='

SELECT COUNT(*) AS incorrectly_flagged
FROM orders_clean
WHERE is_flagged = TRUE
  AND NOT (
        customer_id IS NULL
        OR TRIM(customer_id::text) = ''
        OR qty <= 0
        OR unit_price <= 0
        OR unit_price > 100000
        OR LOWER(status) = 'test'
  );