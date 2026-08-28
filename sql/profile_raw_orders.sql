-- !!! Run with psql !!!

-- Missing fields
\echo '=== MISSING FIELDS ==='

SELECT 
    COUNT(*) AS total_records,
    SUM(CASE WHEN raw_data ->> 'order_id' IS NULL OR TRIM(CAST(raw_data ->> 'order_id' AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS missing_order_id,
    SUM(CASE WHEN raw_data ->> 'customer_id' IS NULL OR TRIM(CAST(raw_data ->> 'customer_id' AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS missing_customer_id,
    SUM(CASE WHEN raw_data ->> 'customer_email' IS NULL OR TRIM(raw_data ->> 'customer_email') = '' THEN 1 ELSE 0 END) AS missing_customer_email,
    SUM(CASE WHEN raw_data ->> 'order_ts' IS NULL OR TRIM(CAST(raw_data ->> 'order_ts' AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS missing_order_ts,
    SUM(CASE WHEN raw_data ->> 'status' IS NULL OR TRIM(raw_data ->> 'status') = '' THEN 1 ELSE 0 END) AS missing_status,
    SUM(CASE WHEN raw_data ->> 'channel' IS NULL OR TRIM(raw_data ->> 'channel') = '' THEN 1 ELSE 0 END) AS missing_channel,
    SUM(CASE WHEN raw_data ->> 'sku' IS NULL OR TRIM(raw_data ->> 'sku') = '' THEN 1 ELSE 0 END) AS missing_sku,
    SUM(CASE WHEN raw_data ->> 'product_name' IS NULL OR TRIM(raw_data ->> 'product_name') = '' THEN 1 ELSE 0 END) AS missing_product_name,
    SUM(CASE WHEN raw_data ->> 'category' IS NULL OR TRIM(raw_data ->> 'category') = '' THEN 1 ELSE 0 END) AS missing_category,
    SUM(CASE WHEN raw_data ->> 'qty' IS NULL THEN 1 ELSE 0 END) AS missing_qty,
    SUM(CASE WHEN raw_data ->> 'unit_price' IS NULL THEN 1 ELSE 0 END) AS missing_unit_price,
    SUM(CASE WHEN raw_data ->> 'currency' IS NULL OR TRIM(raw_data ->> 'currency') = '' THEN 1 ELSE 0 END) AS missing_currency,
    SUM(CASE WHEN raw_data ->> 'country' IS NULL OR TRIM(raw_data ->> 'country') = '' THEN 1 ELSE 0 END) AS missing_country,
    SUM(CASE WHEN raw_data ->> 'fx_reference_date' IS NULL OR TRIM(CAST(raw_data ->> 'fx_reference_date' AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS missing_fx_reference_date
FROM orders_raw;


-- Currency distribution
\echo ''
\echo '=== CURRENCY DISTRIBUTION ==='

SELECT
    raw_data ->> 'currency' AS currency,
    COUNT(*) AS count
FROM orders_raw
GROUP BY 1
ORDER BY count DESC;


-- Status distribution
\echo ''
\echo '=== STATUS DISTRIBUTION ==='

SELECT
    raw_data ->> 'status' AS status,
    COUNT(*) AS count
FROM orders_raw
GROUP BY 1
ORDER BY count DESC;


-- Channel distribution
\echo ''
\echo '=== CHANNEL DISTRIBUTION ==='

SELECT
    raw_data ->> 'channel' AS channel,
    COUNT(*) AS count
FROM orders_raw
GROUP BY 1
ORDER BY count DESC;


-- Category distribution
\echo ''
\echo '=== CATEGORY DISTRIBUTION ==='

SELECT
    raw_data ->> 'category' AS category,
    COUNT(*) AS count
FROM orders_raw
GROUP BY 1
ORDER BY count DESC;


-- Country distribution
\echo ''
\echo '=== COUNTRY DISTRIBUTION ==='

SELECT
    raw_data ->> 'country' AS country,
    COUNT(*) AS count
FROM orders_raw
GROUP BY 1
ORDER BY count DESC;

-- Timestamp examples
\echo ''
\echo '=== ORDER TIMESTAMP EXAMPLES ==='

SELECT
    raw_data ->> 'order_ts' AS order_ts
FROM orders_raw
LIMIT 20;


-- Non-positive customer IDs
\echo ''
\echo '=== NON-POSITIVE CUSTOMER IDS ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE (raw_data ->> 'customer_id')::numeric <= 0;


-- Negative / zero quantities
\echo ''
\echo '=== NON-POSITIVE QUANTITIES ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE (raw_data ->> 'qty')::numeric <= 0;


-- Negative / zero prices
\echo ''
\echo '=== NON-POSITIVE PRICES ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE (raw_data ->> 'unit_price')::numeric <= 0;


-- Duplicate orders
\echo ''
\echo '=== DUPLICATE ORDER IDS ==='

SELECT
    COUNT(*) AS duplicate_order_ids
FROM (
    SELECT order_id
    FROM orders_raw
    GROUP BY order_id
    HAVING COUNT(*) > 1
) duplicates;


-- fx-reference_date format issues
\echo ''
\echo '=== FX REFERENCE DATE FORMAT ISSUES ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE raw_data ->> 'fx_reference_date' IS NOT NULL
  AND raw_data ->> 'fx_reference_date' !~ '^\d{4}-\d{2}-\d{2}$';


-- SKU distribution
\echo ''
\echo '=== SKU DISTRIBUTION ==='

SELECT
    raw_data ->> 'sku' AS sku,
    COUNT(*) AS occurrences
FROM orders_raw
GROUP BY 1
ORDER BY occurrences DESC;


-- SKU format issues
\echo ''
\echo '=== SKU FORMAT ISSUES ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE raw_data ->> 'sku' IS NOT NULL
  AND raw_data ->> 'sku' !~ '^SKU-[A-Za-z0-9]+-[0-9]+$';


-- SKUs with different product names
\echo ''
\echo '=== SKUs WITH DIFFERENT PRODUCT NAMES ==='

SELECT
    COUNT(*) AS count
FROM (
    SELECT raw_data ->> 'sku'
    FROM orders_raw
    WHERE raw_data ->> 'sku' IS NOT NULL
    GROUP BY 1
    HAVING COUNT(DISTINCT TRIM(raw_data ->> 'product_name')) > 1
) inconsistent_skus;


-- SKUs with different categories
\echo ''
\echo '=== SKUs WITH DIFFERENT CATEGORIES ==='

SELECT
    COUNT(*) AS count
FROM (
    SELECT raw_data ->> 'sku'
    FROM orders_raw
    WHERE raw_data ->> 'sku' IS NOT NULL
    GROUP BY 1
    HAVING COUNT(DISTINCT TRIM(raw_data ->> 'category')) > 1
) inconsistent_skus;


-- SKUs with whitespace inconsistencies
\echo ''
\echo '=== TRAILING WHITESPACE INCONSISTENCIES ==='

SELECT
    COUNT(*) AS count
FROM orders_raw
WHERE
       (raw_data ->> 'order_id')          IS DISTINCT FROM TRIM(raw_data ->> 'order_id')
    OR (raw_data ->> 'customer_email')    IS DISTINCT FROM TRIM(raw_data ->> 'customer_email')
    OR (raw_data ->> 'status')            IS DISTINCT FROM TRIM(raw_data ->> 'status')
    OR (raw_data ->> 'channel')           IS DISTINCT FROM TRIM(raw_data ->> 'channel')
    OR (raw_data ->> 'sku')               IS DISTINCT FROM TRIM(raw_data ->> 'sku')
    OR (raw_data ->> 'product_name')      IS DISTINCT FROM TRIM(raw_data ->> 'product_name')
    OR (raw_data ->> 'category')          IS DISTINCT FROM TRIM(raw_data ->> 'category')
    OR (raw_data ->> 'currency')          IS DISTINCT FROM TRIM(raw_data ->> 'currency')
    OR (raw_data ->> 'country')           IS DISTINCT FROM TRIM(raw_data ->> 'country')
    OR (raw_data ->> 'fx_reference_date') IS DISTINCT FROM TRIM(raw_data ->> 'fx_reference_date');