"""
Đánh giá Tabular Expert bằng Leave-One-Out Cross-Validation (LOOCV).
Chạy: .\\venv\\Scripts\\python.exe scripts\\evaluate_loocv.py

Phạm vi:
  - CHỈ thử nghiệm trên tập 15 ca MOCK PATIENTS (không đụng vào dữ liệu thật).
  - Chạy LOOCV cho 3 mô hình: Logistic Regression, Random Forest, LightGBM.
  - ROC-AUC là chỉ số chính (không phụ thuộc threshold).
  - Sensitivity/Specificity/F1 là chỉ số phụ, tính tại DEMO_THRESHOLD=0.5.
  - Xuất kết quả chi tiết ra results/loocv_results.csv.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix

from core.sample_builder import build_patient_sample
from core.dataset_builder import build_dataframe
from data.mock.mock_samples import MOCK_PATIENTS
from models.tabular_expert import TabularExpert

DEMO_THRESHOLD = 0.5

DISCLAIMER = (
    "[DEMO PIPELINE] Kết quả LOOCV trên tập mock nhỏ (N=10) CHỈ CHỨNG MINH PIPELINE\n"
    "CHẠY ĐÚNG LOGIC — KHÔNG PHẢN ÁNH HIỆU NĂNG THỰC TẾ TRÊN DỮ LIỆU BỆNH VIỆN.\n"
    "Khi báo cáo: chỉ được nói 'Đã triển khai đúng phương pháp luận LOOCV, pipeline\n"
    "sẵn sàng áp dụng khi có đủ data thật' — KHÔNG trích số AUC/Sensitivity từ mock."
)


def get_tabular_features(df: pd.DataFrame) -> list:
    """Trích xuất các cột feature thuộc nhóm Tabular (lâm sàng + sinh hóa gộp)."""
    features = []
    for col in df.columns:
        is_tabular = col.startswith("tabular_")
        is_mask = col.endswith("_available")
        if is_tabular and not is_mask:
            features.append(col)
    return features


def compute_loocv_metrics(y_true: np.ndarray, y_proba: np.ndarray):
    """
    Tính các chỉ số từ kết quả LOOCV tổng hợp.

    - ROC-AUC: chỉ số chính, không phụ thuộc threshold.
    - Sensitivity/Specificity/F1: chỉ số phụ, tính tại DEMO_THRESHOLD=0.5.
    - In kèm số đếm thô (TP/FP/TN/FN) để tránh hiểu lầm khi N nhỏ.
    """
    n = len(y_true)
    n_pos = int(y_true.sum())
    n_neg = n - n_pos

    # ROC-AUC (chỉ số chính)
    if len(set(y_true)) < 2:
        auc = float("nan")
    else:
        auc = roc_auc_score(y_true, y_proba)

    # Chỉ số phụ tại DEMO_THRESHOLD
    y_pred = (y_proba >= DEMO_THRESHOLD).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")

    return {
        "auc": auc,
        "f1": f1,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "tp": int(tp), "fp": int(fp),
        "tn": int(tn), "fn": int(fn),
        "n_pos": n_pos, "n_neg": n_neg,
        "n": n,
    }


def format_metrics_row(model_name: str, m: dict) -> dict:
    """Tạo dòng bảng chỉ số với số đếm thô kèm %."""
    def pct_raw(numerator, denominator, fmt_pct=True):
        if denominator == 0:
            return "N/A"
        val = numerator / denominator
        if fmt_pct:
            return f"{val*100:.1f}% ({numerator}/{denominator})"
        return f"{val:.4f}"

    return {
        "Model": model_name,
        "ROC-AUC [CHỈ SỐ CHÍNH]": f"{m['auc']:.4f}" if not np.isnan(m['auc']) else "N/A",
        f"Sensitivity @{DEMO_THRESHOLD} [phụ]": pct_raw(m['tp'], m['n_pos']),
        f"Specificity @{DEMO_THRESHOLD} [phụ]": pct_raw(m['tn'], m['n_neg']),
        f"F1 @{DEMO_THRESHOLD} [phụ]": f"{m['f1']:.4f}",
        "TP/FP/TN/FN": f"{m['tp']}/{m['fp']}/{m['tn']}/{m['fn']}",
    }


def run_loocv_for_model(model_type: str, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """
    Chạy LOOCV cho 1 model_type.
    Trả về mảng xác suất P(cancer) tổng hợp, cùng thứ tự với y.
    """
    loo = LeaveOneOut()
    y_proba_all = np.zeros(len(y))
    indices = y.index.tolist()

    for train_idx, test_idx in loo.split(X):
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_test = X.iloc[test_idx]

        expert = TabularExpert(model_type=model_type, random_state=42)
        expert.fit(X_train, y_train)
        prob = expert.predict_proba(X_test)
        y_proba_all[test_idx[0]] = prob[0]

    return y_proba_all


def main():
    print("=" * 70)
    print("TABULAR EXPERT — LOOCV (Leave-One-Out Cross-Validation)")
    print(DISCLAIMER)
    print("=" * 70)

    # ── 1. Nạp tập dữ liệu MOCK_PATIENTS ──────────────────────────────
    print("\n1. Nạp tập 15 ca MOCK_PATIENTS...")
    samples = [
        build_patient_sample(
            patient_id=p["patient_id"],
            modality_values=p["modality_values"],
            ground_truth_label=p["ground_truth_label"],
            ground_truth_source=p["ground_truth_source"],
        )
        for p in MOCK_PATIENTS
    ]
    df = build_dataframe(samples)

    valid_mask = df["tabular_available"] == 1
    df_valid = df[valid_mask].copy().reset_index(drop=True)
    n = len(df_valid)
    print(f"   Tổng số ca Mock: {len(df)} | Số ca hợp lệ Tabular (N): {n}")

    if n < 2:
        print("   Không đủ mẫu để chạy LOOCV (cần ít nhất 2 ca).")
        return

    # ── 2. Tách X, y ───────────────────────────────────────────────────
    feature_cols = get_tabular_features(df_valid)
    X = df_valid[feature_cols]
    y = df_valid["label"].astype(int)

    # ── 3. Chạy LOOCV cho 3 mô hình ───────────────────────────────────
    models_to_test = ("logistic", "random_forest", "lightgbm")
    results_df = df_valid[["patient_id", "label"]].copy()
    metrics_summary = []

    print(f"\n2. Chạy LOOCV ({n} vòng × 3 mô hình = {n*3} lần fit/predict):")
    for m_type in models_to_test:
        print(f"   [{m_type.upper()}] đang chạy...", end=" ", flush=True)
        y_proba = run_loocv_for_model(m_type, X, y)
        print("xong.")

        results_df[f"P_loocv_{m_type}"] = y_proba.round(4)
        results_df[f"pred_label_loocv_{m_type}"] = (y_proba >= DEMO_THRESHOLD).astype(int)

        m = compute_loocv_metrics(y.values, y_proba)
        metrics_summary.append(format_metrics_row(m_type.upper(), m))

    # ── 4. In Bảng chỉ số tổng quan ───────────────────────────────────
    print("\n" + "─" * 70)
    print("3. BẢNG CHỈ SỐ LOOCV:")
    print(f"   [Ghi chú] Sens/Spec/F1 tính tại threshold={DEMO_THRESHOLD} (demo, chưa tối ưu).")
    print(f"   Chỉ ROC-AUC là chỉ số đáng tin cậy nhất — không phụ thuộc threshold.")
    print("─" * 70)
    metrics_df = pd.DataFrame(metrics_summary)
    print(metrics_df.to_string(index=False))
    print(f"\n   [Nhắc nhở] N={n} — mỗi % thay đổi tương ứng với 1 ca trong {n} ca.")

    # ── 5. In bảng xác suất từng ca ───────────────────────────────────
    print("\n" + "─" * 70)
    print("4. XÁC SUẤT P(cancer) LOOCV TỪNG CA:")
    print("─" * 70)
    display_cols = ["patient_id", "label",
                    "P_loocv_logistic", "pred_label_loocv_logistic",
                    "P_loocv_random_forest", "pred_label_loocv_random_forest",
                    "P_loocv_lightgbm", "pred_label_loocv_lightgbm"]
    print(results_df[display_cols].to_string(index=False))

    # ── 6. Xuất CSV ────────────────────────────────────────────────────
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "loocv_results.csv")
    results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 70)
    print(f"ĐÃ LƯU KẾT QUẢ LOOCV TẠI: {csv_path}")
    print("Pipeline chạy không lỗi (exit code 0).")
    print("=" * 70)


if __name__ == "__main__":
    main()
