"""Run independent LOOCV for the three real-data expert modalities."""

import os
import sys
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import LeaveOneOut

sys.path.insert(0, os.path.abspath("."))

from config.schema_config import MODALITY_NAMES
from models.mri_expert import MRIExpert
from models.tabular_expert import TabularExpert
from models.ultrasound_expert import UltrasoundExpert
from scripts.build_real_dataset import load_all_real_samples
from scripts.prepare_real_expert_datasets import build_expert_dataset


MODEL_TYPES = ("logistic", "random_forest", "lightgbm")
DEMO_THRESHOLD = 0.5
WARNING_TEXT = (
    "N rất nhỏ, kết quả LOOCV này CHỈ để kiểm tra pipeline chạy đúng, "
    "KHÔNG có ý nghĩa thống kê, KHÔNG được báo cáo như kết quả hiệu năng thật "
    "cho người hướng dẫn/bệnh viện."
)
FEATURE_WARNING = (
    "Tabular/Ultrasound: Logistic/RF chỉ dùng numeric features; LightGBM dùng "
    "thêm categorical features, nên so sánh model_type không hoàn toàn công bằng."
)

EXPERT_CLASSES = {
    "tabular": TabularExpert,
    "ultrasound": UltrasoundExpert,
    "mri": MRIExpert,
}


def calculate_metrics(y_true: np.ndarray, probabilities: np.ndarray) -> Dict[str, object]:
    predictions = (probabilities >= DEMO_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    n_positive = int(np.sum(y_true == 1))
    n_negative = int(np.sum(y_true == 0))

    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else np.nan,
        "specificity": float(tn / (tn + fp)) if tn + fp else np.nan,
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "n_positive": n_positive,
        "n_negative": n_negative,
        "n_samples": len(y_true),
    }


def run_loocv(
    modality_name: str,
    model_type: str,
    X: pd.DataFrame,
    y: pd.Series,
    patient_ids: List[str],
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    expert_class = EXPERT_CLASSES[modality_name]
    probabilities = np.full(len(y), np.nan, dtype=float)
    feature_counts = []

    for train_indices, test_indices in LeaveOneOut().split(X):
        y_train = y.iloc[train_indices]
        if y_train.nunique() < 2:
            raise ValueError(
                f"Fold không hợp lệ: {modality_name}/{model_type}, "
                "tập train chỉ còn một lớp nhãn."
            )

        expert = expert_class(model_type=model_type, random_state=42)
        expert.fit(X.iloc[train_indices], y_train)
        probabilities[test_indices[0]] = expert.predict_proba(X.iloc[test_indices])[0]
        feature_counts.append(len(expert.feature_names))

    if np.isnan(probabilities).any():
        raise RuntimeError(f"Có prediction NaN trong {modality_name}/{model_type}.")

    prediction_rows = [
        {
            "expert": modality_name,
            "model_type": model_type,
            "patient_id": patient_ids[index],
            "label": int(y.iloc[index]),
            "p_cancer": float(probabilities[index]),
            "predicted_label": int(probabilities[index] >= DEMO_THRESHOLD),
            "n_features_used": int(feature_counts[index]),
        }
        for index in range(len(y))
    ]
    metrics = calculate_metrics(y.to_numpy(), probabilities)
    metrics.update(
        {
            "expert": modality_name,
            "model_type": model_type,
            "n_features_used_min": min(feature_counts),
            "n_features_used_max": max(feature_counts),
            "warning": WARNING_TEXT,
            "feature_comparison_warning": FEATURE_WARNING,
        }
    )
    return prediction_rows, metrics


def main() -> None:
    print("REAL EXPERTS - LOOCV")
    print(f"WARNING: {WARNING_TEXT}")
    print(f"FEATURE NOTE: {FEATURE_WARNING}")

    samples = load_all_real_samples()
    all_predictions = []
    all_metrics = []

    for modality_name in MODALITY_NAMES:
        X, y, patient_ids = build_expert_dataset(samples, modality_name)
        print(
            f"{modality_name}: N={len(y)}, malignant={int(y.sum())}, "
            f"non_cancer={int((y == 0).sum())}"
        )
        if len(y) < 2 or y.nunique() < 2:
            raise ValueError(f"Không đủ hai lớp để chạy LOOCV cho {modality_name}.")

        for model_type in MODEL_TYPES:
            print(f"  {model_type}: {len(y)} folds", end=" ... ", flush=True)
            predictions, metrics = run_loocv(
                modality_name, model_type, X, y, patient_ids
            )
            all_predictions.extend(predictions)
            all_metrics.append(metrics)
            print(
                f"done, AUC={metrics['roc_auc']:.4f}, "
                f"Brier={metrics['brier_score']:.4f}"
            )

    os.makedirs("results", exist_ok=True)
    predictions_path = "results/real_experts_loocv_predictions.csv"
    metrics_path = "results/real_experts_loocv_metrics.csv"
    pd.DataFrame(all_predictions).to_csv(predictions_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(all_metrics).to_csv(metrics_path, index=False, encoding="utf-8-sig")

    print("\nLOOCV metrics:")
    print(
        pd.DataFrame(all_metrics)[
            ["expert", "model_type", "n_samples", "roc_auc", "sensitivity", "specificity", "f1", "brier_score"]
        ].to_string(index=False)
    )
    print(f"\nSaved predictions: {predictions_path} ({len(all_predictions)} rows)")
    print(f"Saved metrics: {metrics_path} ({len(all_metrics)} rows)")
    print(f"WARNING: {WARNING_TEXT}")


if __name__ == "__main__":
    main()
