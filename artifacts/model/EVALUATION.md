# Churn Model Evaluation

| Metric | Value |
|--------|------:|
| Model | GradientBoostingClassifier |
| Train / Test | 3,750 / 1,250 |
| Test churn rate | 12.2% |
| Accuracy | 0.950 |
| Precision | 0.909 |
| Recall | 0.658 |
| F1 | 0.763 |
| ROC-AUC | 0.963 |
| 5-fold CV ROC-AUC | 0.967 ± 0.007 |

## Top features
| feature                |   importance |
|:-----------------------|-------------:|
| monthly_active_days    |   0.405727   |
| txn_count              |   0.185419   |
| tenure_days            |   0.130537   |
| customer_health_score  |   0.107104   |
| lifetime_revenue       |   0.104384   |
| nps_score              |   0.0186554  |
| feature_adoption_score |   0.0140709  |
| payment_failures_90d   |   0.00972552 |
| mrr                    |   0.00704414 |
| seats                  |   0.00514514 |

## Confusion matrix (rows=actual, cols=predicted)
```
[[1088   10]
 [  52  100]]
```
