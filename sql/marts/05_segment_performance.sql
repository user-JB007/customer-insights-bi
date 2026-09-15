-- MART: Performance by segment × region × plan
CREATE OR REPLACE VIEW CUSTOMER_INSIGHTS.MARTS.SEGMENT_PERFORMANCE AS
SELECT
  segment,
  region,
  plan,
  COUNT(*) AS customers,
  SUM(is_active) AS active_customers,
  SUM(is_churned) AS churned,
  ROUND(SUM(is_churned) / NULLIF(COUNT(*), 0), 4) AS churn_rate,
  ROUND(SUM(mrr), 2) AS total_mrr,
  ROUND(AVG(mrr), 2) AS avg_mrr,
  ROUND(AVG(customer_health_score), 1) AS avg_health,
  ROUND(AVG(nps_score), 1) AS avg_nps,
  ROUND(SUM(lifetime_revenue), 2) AS lifetime_revenue
FROM CUSTOMER_INSIGHTS.MARTS.CUSTOMER_360
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
