# Churn Model Evaluation

| Metric | Value |
|--------|------:|
| Model | GradientBoostingClassifier |
| Train / Test | 3,750 / 1,250 |
| Test churn rate | 12.2% |
| Accuracy | 0.888 |
| Precision | 0.597 |
| Recall | 0.243 |
| F1 | 0.346 |
| ROC-AUC | 0.824 |
| 5-fold CV ROC-AUC | 0.833 ± 0.018 |

## Top features
| feature                |   importance |
|:-----------------------|-------------:|
| tenure_days            |    0.251754  |
| txn_count              |    0.21175   |
| lifetime_revenue       |    0.150978  |
| customer_health_score  |    0.114563  |
| nps_score              |    0.0566355 |
| feature_adoption_score |    0.0410077 |
| payment_failures_90d   |    0.0402051 |
| monthly_active_days    |    0.0356614 |
| mrr                    |    0.0218473 |
| support_tickets_90d    |    0.0199175 |

## Confusion matrix (rows=actual, cols=predicted)
```
[[1073   25]
 [ 115   37]]
```
