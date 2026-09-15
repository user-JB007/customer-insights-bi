"""Train a real customer churn classifier on synthetic feature mart.

Saves model artifact, metrics JSON, feature importance, and holdout predictions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "seats",
    "mrr",
    "tenure_days",
    "monthly_active_days",
    "support_tickets_90d",
    "nps_score",
    "feature_adoption_score",
    "payment_failures_90d",
    "lifetime_revenue",
    "txn_count",
    "total_tickets",
    "customer_health_score",
]
CATEGORICAL = ["segment", "region", "plan", "acquisition_channel"]
TARGET = "is_churned"


def build_pipeline(model_name: str = "gbt") -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ]
    )
    if model_name == "rf":
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
    else:
        clf = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            min_samples_leaf=10,
            random_state=42,
        )
    return Pipeline([("prep", pre), ("clf", clf)])


def feature_importance(pipe: Pipeline, feature_frame: pd.DataFrame) -> pd.DataFrame:
    pre: ColumnTransformer = pipe.named_steps["prep"]
    clf = pipe.named_steps["clf"]
    cat_names = list(pre.named_transformers_["cat"].get_feature_names_out(CATEGORICAL))
    names = NUMERIC + cat_names
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
    else:
        imp = np.abs(clf.coef_[0])
    return (
        pd.DataFrame({"feature": names, "importance": imp})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, default=Path("data/processed/churn_features.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--model", choices=["gbt", "rf"], default="gbt")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.features)
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe = build_pipeline(args.model)
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "model": "GradientBoostingClassifier" if args.model == "gbt" else "RandomForestClassifier",
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "churn_rate_train": float(y_train.mean()),
        "churn_rate_test": float(y_test.mean()),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "classification_report": classification_report(y_test, pred, output_dict=True),
    }

    cv = cross_val_score(build_pipeline(args.model), X_train, y_train, cv=5, scoring="roc_auc")
    metrics["cv_roc_auc_mean"] = float(cv.mean())
    metrics["cv_roc_auc_std"] = float(cv.std())

    fpr, tpr, thr = roc_curve(y_test, proba)
    roc_df = pd.DataFrame({"fpr": fpr, "tpr": tpr, "threshold": thr})

    imp = feature_importance(pipe, X_train)
    preds_out = X_test.copy()
    preds_out["customer_id"] = df.loc[X_test.index, "customer_id"].values
    preds_out["y_true"] = y_test.values
    preds_out["y_pred"] = pred
    preds_out["churn_probability"] = proba

    joblib.dump(pipe, args.out_dir / "churn_model.joblib")
    with open(args.out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    imp.to_csv(args.out_dir / "feature_importance.csv", index=False)
    roc_df.to_csv(args.out_dir / "roc_curve.csv", index=False)
    preds_out.to_csv(args.out_dir / "holdout_predictions.csv", index=False)

    # Human-readable summary
    summary = f"""# Churn Model Evaluation

| Metric | Value |
|--------|------:|
| Model | {metrics['model']} |
| Train / Test | {metrics['n_train']:,} / {metrics['n_test']:,} |
| Test churn rate | {metrics['churn_rate_test']:.1%} |
| Accuracy | {metrics['accuracy']:.3f} |
| Precision | {metrics['precision']:.3f} |
| Recall | {metrics['recall']:.3f} |
| F1 | {metrics['f1']:.3f} |
| ROC-AUC | {metrics['roc_auc']:.3f} |
| 5-fold CV ROC-AUC | {metrics['cv_roc_auc_mean']:.3f} ± {metrics['cv_roc_auc_std']:.3f} |

## Top features
{imp.head(10).to_markdown(index=False)}

## Confusion matrix (rows=actual, cols=predicted)
```
{confusion_matrix(y_test, pred)}
```
"""
    (args.out_dir / "EVALUATION.md").write_text(summary)

    print(json.dumps({k: metrics[k] for k in ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "cv_roc_auc_mean"]}, indent=2))
    print(f"Artifacts → {args.out_dir}")


if __name__ == "__main__":
    main()
