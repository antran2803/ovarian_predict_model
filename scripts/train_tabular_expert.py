"""
Huấn luyện và thử nghiệm Tabular Expert (Clinical + Biochemical).
Chạy: .\\venv\\Scripts\\python.exe scripts\\train_tabular_expert.py

Phạm vi thử nghiệm hiện tại:
  - CHỈ thử nghiệm trên dữ liệu 15 ca MOCK PATIENTS (không đụng vào dữ liệu thật).
  - So sánh song song 3 mô hình: Logistic Regression, Random Forest, và LightGBM.
  - Tự động xuất file CSV kết quả hoàn chỉnh vào results/tabular_expert_results.csv.
  - Chuẩn hóa thông báo chẩn đoán mô phỏng trung tính [DEMO - CHƯA VALIDATE].
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix

from core.sample_builder import build_patient_sample
from core.dataset_builder import build_dataframe
from data.mock.mock_samples import MOCK_PATIENTS
from models.tabular_expert import TabularExpert

DISCLAIMER = (
    "[DEMO PIPELINE] Chỉ số AUC/F1/Sens/Spec tính trên tập mock nhỏ CHỈ ĐỂ "
    "KIỂM TRA CODE CHẠY KHÔNG CRASH, KHÔNG CÓ GIÁ TRỊ ĐÁNH GIÁ HIỆU NĂNG Y KHOA THỰC TẾ"
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


def compute_metrics(y_true, y_proba, threshold: float = 0.5):
    """
    Tính ROC-AUC, F1-score, Sensitivity, Specificity.
    """
    n_samples = len(y_true)
    n_classes = len(set(y_true))

    if n_classes < 2:
        auc = float("nan")
    else:
        auc = roc_auc_score(y_true, y_proba)

    y_pred = (y_proba >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")

    return {
        "auc": auc,
        "f1_score": f1,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "n_samples": n_samples,
    }


def format_clinical_recommendation(prob: float, threshold: float = 0.5) -> str:
    """
    Tạo thông báo chẩn đoán mô phỏng trung tính có nhãn DEMO rõ ràng.
    """
    if prob >= threshold:
        return f"[DEMO - CHƯA VALIDATE] Mức độ nghi ngờ ác tính cao (P = {prob:.4f} >= {threshold})"
    else:
        return f"[DEMO - CHƯA VALIDATE] Mức độ nghi ngờ ác tính thấp (P = {prob:.4f} < {threshold})"


def main():
    print("=" * 70)
    print("TABULAR EXPERT — CHẠY THỬ PIPELINE TRÊN TẬP MOCK (SO SÁNH 3 MÔ HÌNH)")
    print(DISCLAIMER)
    print("=" * 70)

    # ── 1. Nạp tập dữ liệu MOCK_PATIENTS ─────────────────────
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

    # ── 2. Lọc ca hợp lệ cho Tabular Expert ────────────────────
    valid_mask = df["tabular_available"] == 1
    df_valid = df[valid_mask].copy()
    print(f"   Tổng số ca Mock: {len(df)} | Số ca hợp lệ Tabular: {len(df_valid)}")

    if len(df_valid) == 0:
        print("   Không có mẫu hợp lệ nào.")
        return

    # ── 3. Tách X, y ─────────────────────────────────────────
    feature_cols = get_tabular_features(df_valid)
    X = df_valid[feature_cols]
    y = df_valid["label"].astype(int)

    # ── 4. Huấn luyện & So sánh 3 Mô hình ────────────────────
    models_to_test = ("logistic", "random_forest", "lightgbm")
    results_df = df_valid[["patient_id", "label"]].copy()

    metrics_summary = []

    print("\n2. Huấn luyện và dự đoán P(cancer):")
    for m_type in models_to_test:
        expert = TabularExpert(model_type=m_type, random_state=42)
        expert.fit(X, y)
        probas = expert.predict_proba(X)
        
        results_df[f"P_cancer_{m_type}"] = probas.round(4)
        results_df[f"ChanDoan_{m_type}"] = [
            format_clinical_recommendation(p) for p in probas
        ]

        m_res = compute_metrics(y.values, probas, threshold=0.5)
        metrics_summary.append({
            "Model": m_type.upper(),
            "ROC-AUC": f"{m_res['auc']:.4f}" if not np.isnan(m_res['auc']) else "N/A",
            "F1-Score": f"{m_res['f1_score']:.4f}",
            "Sensitivity (Độ nhạy)": f"{m_res['sensitivity']:.4f}",
            "Specificity (Độ đặc hiệu)": f"{m_res['specificity']:.4f}",
        })

    # ── 5. In Bảng chỉ số tổng quan trên Terminal ────────────
    print("\n" + "─" * 70)
    print("3. BẢNG CHỈ SỐ THỬ NGHIỆM TỔNG QUAN (MỘT SỐ MÔ HÌNH):")
    print(DISCLAIMER)
    print("─" * 70)
    metrics_df = pd.DataFrame(metrics_summary)
    print(metrics_df.to_string(index=False))

    # ── 6. In Bảng tóm tắt kết quả chẩn đoán mô phỏng ────────
    print("\n" + "─" * 70)
    print("4. BẢNG TÓM TẮT DỰ ĐOÁN XÁC SUẤT VÀ CHẨN ĐOÁN (MOCK SAMPLES):")
    print("─" * 70)
    summary_cols = ["patient_id", "label", "P_cancer_logistic", "P_cancer_random_forest", "P_cancer_lightgbm", "ChanDoan_lightgbm"]
    print(results_df[summary_cols].to_string(index=False))

    # ── 7. Tự động xuất dữ liệu chi tiết ra file CSV ─────────
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "tabular_expert_results.csv")
    
    # Ghép cả X features và kết quả dự đoán để lưu CSV đầy đủ
    full_csv_df = pd.concat([df_valid[["patient_id", "label"]], X, results_df.drop(columns=["patient_id", "label"])], axis=1)
    full_csv_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print("\n" + "=" * 70)
    print(f"ĐÃ LƯU BÁO CÁO CSV HOÀN CHỈNH TẠI: {csv_path}")
    print("Pipeline chạy không lỗi (exit code 0).")
    print("=" * 70)


if __name__ == "__main__":
    main()
