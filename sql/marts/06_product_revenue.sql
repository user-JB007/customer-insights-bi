-- MART: Product revenue by month
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.PRODUCT_REVENUE AS
SELECT
  TO_CHAR(DATE_TRUNC('month', txn_date), 'YYYY-MM') AS txn_month,
  product,
  ROUND(SUM(amount), 2) AS revenue,
  COUNT(*) AS txn_count,
  COUNT(DISTINCT customer_id) AS customers
FROM CUSTOMER_INSIGHTS.RAW.TRANSACTIONS
WHERE status = 'succeeded'
GROUP BY 1, 2
ORDER BY 1, 2;
