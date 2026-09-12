# -*- coding: utf-8 -*-
"""
Script so sánh tự động: Đối chiếu kết quả trích xuất thực tế với Ground Truth (docs/EXTRACTION_REPORT_CASE_*.md)
Hỗ trợ phân biệt đúng modality (ultrasound vs mri) và chuẩn hóa so sánh None / NaN.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_latest_csv(case_num: int) -> str:
    pattern = f"results/extracted_case_{case_num:02d}_*.csv"
    files = glob.glob(pattern)
    if not files:
        fallback = f"results/extracted_case_{case_num:02d}.csv"
        if os.path.exists(fallback):
            return fallback
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def compare_case(case_num: int, gt_dict: dict):
    csv_file = get_latest_csv(case_num)
    if not csv_file:
        print(f"[LỖI] Chưa có file CSV kết quả cho Case {case_num}")
        return

    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    print(f"\n{'='*105}")
    print(f"BẢNG ĐỐI CHIẾU KẾT QUẢ TRÍCH XUẤT CASE {case_num:02d} (File: {csv_file})")
    print(f"{'='*105}")
    print(f"{'Modality':<12} | {'Field Name':<28} | {'Extracted (Regex)':<18} | {'Ground Truth':<18} | {'Đánh giá':<15}")
    print(f"{'-'*12}-+-{'-'*28}-+-{'-'*18}-+-{'-'*18}-+-{'-'*15}")

    total_fields = 0
    matched_fields = 0

    for _, row in df.iterrows():
        mod = str(row["modality"])
        feat = str(row["feature_name"])
        val = row["extracted_value"]
        
        # Lấy ground truth theo key (modality, feature)
        gt_val = gt_dict.get((mod, feat), gt_dict.get(feat, "N/A"))

        # Chuẩn hóa giá trị None / NaN
        val_is_none = pd.isna(val) or str(val).strip().lower() in ["none", "nan", ""]
        gt_is_none = pd.isna(gt_val) or str(gt_val).strip().lower() in ["none", "nan", ""]

        is_match = False
        if gt_val == "N/A":
            status = "CHƯA XÁC THỰC"
        elif val_is_none and gt_is_none:
            is_match = True
            status = "✅ KHỚP (None)"
            val_str = "None"
            gt_str = "None"
        elif val_is_none != gt_is_none:
            is_match = False
            status = "❌ SAI"
            val_str = "None" if val_is_none else str(val)
            gt_str = "None" if gt_is_none else str(gt_val)
        else:
            val_str = str(val)
            gt_str = str(gt_val)
            if val_str.strip().lower() == gt_str.strip().lower():
                is_match = True
                status = "✅ KHỚP"
            else:
                try:
                    if float(val_str) == float(gt_str):
                        is_match = True
                        status = "✅ KHỚP"
                    else:
                        status = "❌ SAI"
                except (ValueError, TypeError):
                    status = "❌ SAI"

        total_fields += 1
        if is_match:
            matched_fields += 1

        print(f"{mod:<12} | {feat:<28} | {val_str:<18} | {gt_str:<18} | {status:<15}")

    acc = (matched_fields / total_fields) * 100 if total_fields > 0 else 0
    print(f"{'-'*105}")
    print(f"TỔNG KẾT CASE {case_num:02d}: Khớp {matched_fields}/{total_fields} trường ({acc:.1f}%)")
    print(f"{'='*105}\n")


# Ground Truth chuẩn từ docs/EXTRACTION_REPORT_CASE_01.md
GT_CASE_01 = {
    ("tabular", "age"): 18, ("tabular", "menopause"): 0, ("tabular", "pregnancy_status"): 0, ("tabular", "bilateral_lesion"): 1,
    ("tabular", "months_detection_to_surgery"): 3.0, ("tabular", "prior_ovarian_surgery"): 0, ("tabular", "other_cancer_history"): 0,
    ("tabular", "other_cancer_primary_site"): None, ("tabular", "oncology_center_flag"): 1,
    ("tabular", "CA125"): 772.4, ("tabular", "HE4"): 39.7, ("tabular", "AFP"): 2000.0, ("tabular", "beta_hCG"): 5.0, ("tabular", "ROMA"): 5.61,
    ("ultrasound", "lesion_max_diameter_mm"): 185.0, ("ultrasound", "solid_max_diameter_mm"): 185.0, ("ultrasound", "papillary_count"): None,
    ("ultrasound", "more_than_10_locules"): None, ("ultrasound", "acoustic_shadow"): 0, ("ultrasound", "ascites"): 1, ("ultrasound", "doppler_score"): 3,
    ("ultrasound", "morphology_class"): 5, ("ultrasound", "laterality"): "right", ("ultrasound", "solid_component_present"): 1,
    ("ultrasound", "multilocular"): None, ("ultrasound", "irregular_wall_or_septa"): 1, ("ultrasound", "vascularity_description"): "mức độ 3",
    ("ultrasound", "iota_adnex_available"): 1,
    ("mri", "solid_component"): 1, ("mri", "solid_max_diameter_mm"): 137.0, ("mri", "TIC"): 1, ("mri", "restricted_diffusion"): 1,
    ("mri", "thick_septa"): 1, ("mri", "ascites_mri"): 1, ("mri", "morphology_class_mri"): 5, ("mri", "o_rads_mri"): 3,
    ("ground_truth", "cancer_label"): 1
}

# Ground Truth chuẩn từ docs/EXTRACTION_REPORT_CASE_02.md
GT_CASE_02 = {
    ("tabular", "age"): 58, ("tabular", "menopause"): 1, ("tabular", "pregnancy_status"): 0, ("tabular", "bilateral_lesion"): 1,
    ("tabular", "months_detection_to_surgery"): None, ("tabular", "prior_ovarian_surgery"): 0, ("tabular", "other_cancer_history"): 0,
    ("tabular", "other_cancer_primary_site"): None, ("tabular", "oncology_center_flag"): 1,
    ("tabular", "CA125"): 54.5, ("tabular", "HE4"): 36.9, ("tabular", "AFP"): 2.16, ("tabular", "beta_hCG"): 8.03, ("tabular", "ROMA"): 19.61,
    ("ultrasound", "lesion_max_diameter_mm"): 91.0, ("ultrasound", "solid_max_diameter_mm"): 91.0, ("ultrasound", "papillary_count"): None,
    ("ultrasound", "more_than_10_locules"): None, ("ultrasound", "acoustic_shadow"): 1, ("ultrasound", "ascites"): 1, ("ultrasound", "doppler_score"): 3,
    ("ultrasound", "morphology_class"): 5, ("ultrasound", "laterality"): "left", ("ultrasound", "solid_component_present"): 1,
    ("ultrasound", "multilocular"): None, ("ultrasound", "irregular_wall_or_septa"): 1, ("ultrasound", "vascularity_description"): "mức độ 3",
    ("ultrasound", "iota_adnex_available"): 1,
    ("mri", "solid_component"): 1, ("mri", "solid_max_diameter_mm"): 88.0, ("mri", "TIC"): 1, ("mri", "restricted_diffusion"): 1,
    ("mri", "thick_septa"): 1, ("mri", "ascites_mri"): 1, ("mri", "morphology_class_mri"): 5, ("mri", "o_rads_mri"): 3,
    ("ground_truth", "cancer_label"): 0
}

# Ground Truth chuẩn từ docs/EXTRACTION_REPORT_CASE_03.md (Held-out test)
GT_CASE_03 = {
    ("tabular", "age"): 46, ("tabular", "menopause"): 0, ("tabular", "pregnancy_status"): 0, ("tabular", "bilateral_lesion"): 0,
    ("tabular", "months_detection_to_surgery"): None, ("tabular", "prior_ovarian_surgery"): 1, ("tabular", "other_cancer_history"): 0,
    ("tabular", "other_cancer_primary_site"): None, ("tabular", "oncology_center_flag"): 1,
    ("tabular", "CA125"): 23.4, ("tabular", "HE4"): 48.8, ("tabular", "AFP"): 4.26, ("tabular", "beta_hCG"): 5.0, ("tabular", "ROMA"): 14.94,
    ("ultrasound", "lesion_max_diameter_mm"): 188.0, ("ultrasound", "solid_max_diameter_mm"): 55.0, ("ultrasound", "papillary_count"): 4,
    ("ultrasound", "more_than_10_locules"): 1, ("ultrasound", "acoustic_shadow"): 0, ("ultrasound", "ascites"): 0, ("ultrasound", "doppler_score"): 1,
    ("ultrasound", "morphology_class"): 3, ("ultrasound", "laterality"): None, ("ultrasound", "solid_component_present"): 1,
    ("ultrasound", "multilocular"): 1, ("ultrasound", "irregular_wall_or_septa"): 1, ("ultrasound", "vascularity_description"): "mức độ 1",
    ("ultrasound", "iota_adnex_available"): 1,
    ("mri", "solid_component"): 1, ("mri", "solid_max_diameter_mm"): 30.0, ("mri", "TIC"): 1, ("mri", "restricted_diffusion"): 1,
    ("mri", "thick_septa"): 1, ("mri", "ascites_mri"): 0, ("mri", "morphology_class_mri"): 3, ("mri", "o_rads_mri"): 3,
    ("ground_truth", "cancer_label"): 0
}

if __name__ == "__main__":
    compare_case(1, GT_CASE_01)
    compare_case(2, GT_CASE_02)
    compare_case(3, GT_CASE_03)

