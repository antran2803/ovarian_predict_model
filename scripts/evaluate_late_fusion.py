"""
Demo Late Fusion trên tập mock — đọc P(cancer) từ LOOCV đã tính sẵn.
Chạy: .\\venv\\Scripts\\python.exe scripts\\evaluate_late_fusion.py

LƯU Ý QUAN TRỌNG:
  Script này đọc results/loocv_results.csv (cột P_loocv_lightgbm) làm P_tabular.
  KHÔNG gọi TabularExpert.fit/predict lại — để tránh tái phạm lỗi train=test
  mà bước LOOCV đã giải quyết.

Trạng thái hiện tại:
  - Tabular Expert: CÓ (từ LOOCV)
  - US Expert:      CHƯA CÓ → P_us = None
  - MRI Expert:     CHƯA CÓ → P_mri = None
  → Fusion hiện = passthrough P_tabular (1 expert duy nhất)
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from models.late_fusion import LateFusion

DEMO_THRESHOLD = 0.5

DISCLAIMER = (
    "[DEMO PIPELINE] Kết quả Late Fusion trên mock CHỈ CHỨNG MINH KIẾN TRÚC MODULE CHẠY ĐÚNG.\n"
    "Hiện tại chỉ có 1 Expert (Tabular) → P_fusion = P_tabular (passthrough).\n"
    "Fusion thực sự có ý nghĩa khi có ≥ 2 Expert độc lập (US, MRI)."
)

LOOCV_CSV = os.path.join("results", "loocv_results.csv")


def main():
    print("=" * 70)
    print("LATE FUSION — DEMO TRÊN TẬP MOCK (ĐỌC TỪ LOOCV CSV)")
    print(DISCLAIMER)
    print("=" * 70)

    # ── 1. Đọc kết quả LOOCV ──────────────────────────────────────────
    if not os.path.exists(LOOCV_CSV):
        print(f"\n[LỖI] Không tìm thấy {LOOCV_CSV}.")
        print("  Chạy trước: .\\venv\\Scripts\\python.exe scripts\\evaluate_loocv.py")
        return

    loocv_df = pd.read_csv(LOOCV_CSV)
    print(f"\n1. Đọc {LOOCV_CSV}: {len(loocv_df)} ca.")
    print(
        "   Dùng P_loocv_lightgbm làm P_tabular vì đây là model chính theo lộ trình "
        "(khớp hướng paper Kunishima et al.)."
    )

    # ── 2. Chạy Late Fusion từng ca ───────────────────────────────────
    fuser = LateFusion()
    rows = []

    for _, row in loocv_df.iterrows():
        p_tabular = row["P_loocv_lightgbm"]
        p_tabular = None if pd.isna(p_tabular) else float(p_tabular)

        result = fuser.fuse(
            expert_probas={
                "tabular": p_tabular,
                "us": None,    # US Expert chưa có
                "mri": None,   # MRI Expert chưa có
            },
            strategy="simple_average",
        )

        p_fusion = result["P_fusion"]
        pred_label = None if p_fusion is None else int(p_fusion >= DEMO_THRESHOLD)
        no_data_flag = "KHÔNG ĐỦ DỮ LIỆU" if p_fusion is None else ""

        rows.append({
            "patient_id":   row["patient_id"],
            "label":        int(row["label"]),
            "P_tabular":    p_tabular,
            "P_us":         None,
            "P_mri":        None,
            "P_fusion":     p_fusion,
            "pred_label_fusion": pred_label,
            "experts_used": str(result["experts_used"]),
            "strategy":     result["strategy"],
            "note":         no_data_flag,
        })

    result_df = pd.DataFrame(rows)

    # ── 3. In bảng kết quả ────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("2. BẢNG KẾT QUẢ LATE FUSION (DEMO):")
    print(f"   [Ghi chú] pred_label_fusion tại threshold={DEMO_THRESHOLD} (demo, chưa tối ưu).")
    print("─" * 70)
    display_cols = ["patient_id", "label", "P_tabular", "P_fusion",
                    "pred_label_fusion", "experts_used"]
    print(result_df[display_cols].to_string(index=False))

    # Thống kê đơn giản
    n_no_data = result_df["P_fusion"].isna().sum()
    if n_no_data > 0:
        print(f"\n   [CHÚ Ý] {n_no_data} ca không đủ dữ liệu để dự đoán (P_fusion=None).")

    # ── 4. Xuất CSV với schema cố định ────────────────────────────────
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "late_fusion_results.csv")
    out_cols = ["patient_id", "label", "P_tabular", "P_us", "P_mri",
                "P_fusion", "pred_label_fusion", "experts_used", "strategy", "note"]
    result_df[out_cols].to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 70)
    print(f"ĐÃ LƯU KẾT QUẢ LATE FUSION TẠI: {csv_path}")
    print("Pipeline chạy không lỗi (exit code 0).")
    print("=" * 70)


if __name__ == "__main__":
    main()
