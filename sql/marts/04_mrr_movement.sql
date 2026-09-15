-- MART: Monthly MRR / ARR snapshot with new vs churned MRR
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.MRR_MOVEMENT AS
WITH months AS (
  SELECT DATEADD('month', SEQ4(), '2022-01-01'::DATE) AS month_start
  FROM TABLE(GENERATOR(ROWCOUNT => 60))
  WHERE month_start <= (SELECT MAX(as_of_date) FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS)
),
active AS (
  SELECT
    m.month_start,
    c.customer_id,
    c.mrr
  FROM months m
  JOIN CUSTOMER_INSIGHTS.RAW.CUSTOMERS c
    ON c.signup_date <= LAST_DAY(m.month_start)
   AND (c.is_churned = 0 OR c.churn_date > LAST_DAY(m.month_start))
   AND c.mrr > 0
),
new_cust AS (
  SELECT DATE_TRUNC('month', signup_date) AS month_start, customer_id, mrr
  FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS
  WHERE mrr > 0
),
churned AS (
  SELECT DATE_TRUNC('month', churn_date) AS month_start, customer_id, mrr
  FROM CUSTOMER_INSIGHTS.RAW.CUSTOMERS
  WHERE is_churned = 1
)
SELECT
  TO_CHAR(m.month_start, 'YYYY-MM') AS month,
  COUNT(DISTINCT a.customer_id) AS active_customers,
  ROUND(COALESCE(SUM(a.mrr), 0), 2) AS mrr,
  ROUND(COALESCE(SUM(a.mrr), 0) * 12, 2) AS arr,
  (SELECT COUNT(*) FROM new_cust n WHERE n.month_start = m.month_start) AS new_customers,
  (SELECT ROUND(COALESCE(SUM(n.mrr), 0), 2) FROM new_cust n WHERE n.month_start = m.month_start) AS new_mrr,
  (SELECT COUNT(*) FROM churned ch WHERE ch.month_start = m.month_start) AS churned_customers,
  (SELECT ROUND(COALESCE(SUM(ch.mrr), 0), 2) FROM churned ch WHERE ch.month_start = m.month_start) AS churned_mrr
FROM months m
LEFT JOIN active a ON a.month_start = m.month_start
GROUP BY m.month_start
ORDER BY 1;
