-- MART: Customer 360 — one row per customer with revenue, support, health
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.CUSTOMER_360 AS
WITH txn AS (
  SELECT
    customer_id,
    SUM(IFF(status = 'succeeded', amount, 0)) AS lifetime_revenue,
    COUNT_IF(status = 'succeeded')            AS txn_count,
    MAX(IFF(status = 'succeeded', txn_date, NULL)) AS last_txn_date,
    MIN(IFF(status = 'succeeded', txn_date, NULL)) AS first_txn_date,
    AVG(IFF(status = 'succeeded', amount, NULL))   AS avg_txn_amount
  FROM CUSTOMER_INSIGHTS.RAW.TRANSACTIONS
  GROUP BY 1
),
sup AS (
  SELECT
    customer_id,
    COUNT(*) AS total_tickets,
    AVG(resolved_hours) AS avg_resolve_hours,
    COUNT_IF(priority = 'critical') AS critical_tickets
  FROM CUSTOMER_INSIGHTS.RAW.SUPPORT_EVENTS
  GROUP BY 1
)
SELECT
  c.*,
  COALESCE(t.lifetime_revenue, 0) AS lifetime_revenue,
  COALESCE(t.txn_count, 0)        AS txn_count,
  t.last_txn_date,
  t.first_txn_date,
  COALESCE(t.avg_txn_amount, 0)   AS avg_txn_amount,
  DATEDIFF('day', t.last_txn_date, c.as_of_date) AS days_since_last_txn,
  COALESCE(s.total_tickets, 0)    AS total_tickets,
  COALESCE(s.avg_resolve_hours, 0) AS avg_resolve_hours,
  COALESCE(s.critical_tickets, 0) AS critical_tickets,
  IFF(c.is_churned = 0 AND c.mrr > 0, 1, 0) AS is_active,
  ROUND(
      0.30 * (c.feature_adoption_score * 100)
    + 0.20 * ((LEAST(GREATEST(c.nps_score, -100), 100) + 100) / 2)
    + 0.25 * (c.monthly_active_days / 28 * 100)
    + 0.15 * (100 - (LEAST(c.support_tickets_90d, 10) * 10))
    + 0.10 * (100 - (LEAST(c.payment_failures_90d, 5) * 20))
  , 1) AS customer_health_score
FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS c
LEFT JOIN txn t ON c.customer_id = t.customer_id
LEFT JOIN sup s ON c.customer_id = s.customer_id;
