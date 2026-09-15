-- MART: Revenue by signup cohort and months since signup
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.REVENUE_COHORTS AS
WITH cust AS (
  SELECT
    customer_id,
    signup_date,
    DATE_TRUNC('month', signup_date) AS cohort_month
  FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(*) AS cohort_size FROM cust GROUP BY 1
),
rev AS (
  SELECT
    c.cohort_month,
    DATEDIFF('month', c.signup_date, t.txn_date) AS months_since_signup,
    SUM(t.amount) AS revenue,
    COUNT(DISTINCT t.customer_id) AS paying_customers,
    COUNT(*) AS txn_count
  FROM CUSTOMER_INSIGHTS.RAW.TRANSACTIONS t
  JOIN cust c ON t.customer_id = c.customer_id
  WHERE t.status = 'succeeded'
    AND DATEDIFF('month', c.signup_date, t.txn_date) >= 0
  GROUP BY 1, 2
)
SELECT
  r.cohort_month,
  r.months_since_signup,
  r.revenue,
  r.paying_customers,
  r.txn_count,
  cs.cohort_size,
  ROUND(r.revenue / NULLIF(cs.cohort_size, 0), 2) AS revenue_per_customer
FROM rev r
JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
ORDER BY 1, 2;
