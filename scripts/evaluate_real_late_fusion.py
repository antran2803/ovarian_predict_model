"""Evaluate Late Fusion on out-of-fold Logistic Expert predictions."""

import os
import sys
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, confusion_matrix, f1_score, roc_auc_score

sys.path.insert(0, os.path.abspath("."))

from models.late_fusion import LateFusion


INPUT_PATH = "results/real_experts_loocv_predictions.csv"
PREDICTIONS_PATH = "results/real_late_fusion_predictions.csv"
METRICS_PATH = "results/real_late_fusion_metrics.csv"
MODEL_TYPE = "logistic"
THRESHOLD = 0.5
STRATEGIES = ("simple_average", "and", "or", "max")
WARNING = (
    "N nhỏ (9-11 ca); kết quả Late Fusion CHỈ kiểm tra pipeline, "
    "không có ý nghĩa thống kê/lâm sàng và không được báo cáo như hiệu năng thật."
)
FEATURE_WARNING = (
    "Logistic baseline dùng numeric features; LightGBM exploratory trước đó dùng "
    "thêm categorical features ở Tabular/Ultrasound."
)


def validate_fuser() -> None:
    """Check 3, 2, 1 and 0 available experts, including NaN."""
    fuser = LateFusion()
    assert fuser.fuse({"tabular": 0.2, "ultrasound": 0.6, "mri": 0.8})["experts_used"] == [
        "mri", "tabular", "ultrasound"
    ]
    assert fuser.fuse({"tabular": 0.2, "ultrasound": np.nan, "mri": None})["experts_used"] == [
        "tabular"
    ]
    empty = fuser.fuse({"tabular": np.nan, "ultrasound": None, "mri": None})
    assert empty["P_fusion"] is None and empty["experts_used"] == []
    assert fuser.fuse({"tabular": 0.2, "ultrasound": 0.8}, strategy="and")["P_fusion"] == 0.0
    assert fuser.fuse({"tabular": 0.2, "ultrasound": 0.8}, strategy="or")["P_fusion"] == 1.0
    assert fuser.fuse({"tabular": 0.2, "ultrasound": 0.8}, strategy="max")["P_fusion"] == 0.8


def calculate_metrics(frame: pd.DataFrame) -> Dict[str, object]:
    y_true = frame["label"].to_numpy(dtype=int)
    probabilities = frame["P_fusion"].to_numpy(dtype=float)
    predictions = frame["predicted_label"].to_numpy(dtype=int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "n_samples": len(frame),
        "n_malignant": int((y_true == 1).sum()),
        "n_non_cancer": int((y_true == 0).sum()),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else np.nan,
        "specificity": float(tn / (tn + fp)) if tn + fp else np.nan,
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "warning": WARNING,
        "feature_comparison_warning": FEATURE_WARNING,
    }


def main() -> None:
    validate_fuser()
    source = pd.read_csv(INPUT_PATH)
    source = source[source["model_type"] == MODEL_TYPE].copy()
    if source.empty:
        raise ValueError(f"Không có prediction cho model_type={MODEL_TYPE}")

    pivot = source.pivot(index="patient_id", columns="expert", values="p_cancer")
    labels = source.groupby("patient_id")["label"].first()
    pivot["label"] = labels
    pivot = pivot.reset_index()

    fuser = LateFusion()
    prediction_rows: List[Dict[str, object]] = []
    metric_rows: List[Dict[str, object]] = []

    print("REAL LATE FUSION - LOGISTIC OOF BASELINE")
    print(f"WARNING: {WARNING}")
    print(f"FEATURE NOTE: {FEATURE_WARNING}")
    print("\nExperts used theo tung benh nhan:")

    for _, row in pivot.iterrows():
        expert_probas = {
            expert: row.get(expert, np.nan)
            for expert in ("tabular", "ultrasound", "mri")
        }
        used_result = fuser.fuse(expert_probas, strategy="simple_average")
        print(f"  {row['patient_id']}: {used_result['experts_used']}")

        for strategy in STRATEGIES:
            result = fuser.fuse(expert_probas, strategy=strategy)
            if result["P_fusion"] is None:
                continue
            p_fusion = float(result["P_fusion"])
            prediction_rows.append(
                {
                    "patient_id": row["patient_id"],
                    "label": int(row["label"]),
                    "strategy": strategy,
                    "model_type": MODEL_TYPE,
                    "P_tabular": expert_probas["tabular"],
                    "P_ultrasound": expert_probas["ultrasound"],
                    "P_mri": expert_probas["mri"],
                    "P_fusion": p_fusion,
                    "predicted_label": int(p_fusion >= THRESHOLD),
                    "experts_used": ",".join(result["experts_used"]),
                    "n_experts_used": len(result["experts_used"]),
                    "threshold": THRESHOLD,
                }
            )

    predictions = pd.DataFrame(prediction_rows)
    for strategy in STRATEGIES:
        strategy_frame = predictions[predictions["strategy"] == strategy].copy()
        metrics = calculate_metrics(strategy_frame)
        metrics.update({"strategy": strategy, "model_type": MODEL_TYPE})
        metric_rows.append(metrics)

    os.makedirs("results", exist_ok=True)
    predictions.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8-sig")
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")

    print("\nSIMPLE_AVERAGE (probability) - ket qua rieng")
    print(metrics[metrics["strategy"] == "simple_average"].to_string(index=False))
    print("\nVOTING AND / OR / MAX - ket qua rieng")
    print(metrics[metrics["strategy"].isin(["and", "or", "max"])].to_string(index=False))
    print(f"\nSaved predictions: {PREDICTIONS_PATH} ({len(predictions)} rows)")
    print(f"Saved metrics: {METRICS_PATH} ({len(metrics)} rows)")
    print(f"WARNING: {WARNING}")


if __name__ == "__main__":
    main()
