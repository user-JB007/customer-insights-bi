-- MART: Logo retention by signup cohort × months since signup
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.RETENTION_MONTHLY AS
WITH base AS (
  SELECT
    customer_id,
    signup_date,
    DATE_TRUNC('month', signup_date) AS cohort_month,
    is_churned,
    churn_date,
    as_of_date
  FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS
),
cohort_sizes AS (
  SELECT cohort_month, COUNT(*) AS cohort_size
  FROM base
  GROUP BY 1
),
spine AS (
  SELECT
    b.cohort_month,
    b.customer_id,
    b.signup_date,
    b.is_churned,
    b.churn_date,
    seq.VALUE::INT AS months_since_signup
  FROM base b,
       LATERAL FLATTEN(INPUT => ARRAY_GENERATE_RANGE(
         0,
         LEAST(24, DATEDIFF('month', b.cohort_month, DATE_TRUNC('month', b.as_of_date))) + 1
       )) seq
)
SELECT
  s.cohort_month,
  s.months_since_signup,
  cs.cohort_size,
  COUNT_IF(
    s.is_churned = 0
    OR s.churn_date > DATEADD('month', s.months_since_signup + 1, s.cohort_month) - 1
  ) AS customers_retained,
  ROUND(
    customers_retained / NULLIF(cs.cohort_size, 0),
    4
  ) AS retention_rate
FROM spine s
JOIN cohort_sizes cs ON s.cohort_month = cs.cohort_month
GROUP BY 1, 2, 3
ORDER BY 1, 2;
