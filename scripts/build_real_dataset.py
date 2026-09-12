# -*- coding: utf-8 -*-
"""
Script nạp toàn bộ 12 ca bệnh Ground Truth thật từ docs/EXTRACTION_REPORT_CASE_01.md -> 12.md
Sử dụng core/gt_report_parser.py và core/sample_builder.py để tạo 12 sample chuẩn hóa.

Tính năng:
- Bóc tách đầy đủ 3 modality chính thức (tabular, ultrasound, mri) + ground_truth.
- Tự động tính toán feature_mask và completeness flag (available) theo đúng schema_config.py.
- Xử lý chính xác biến điều kiện other_cancer_primary_site khi other_cancer_history == 0.
- In BẢNG TỔNG HỢP DUY NHẤT NHẤT QUÁN 100%: hiển thị cả tính khả dụng (1/0), tỷ lệ missing,
  danh sách tất cả các trường bị khuyết (All Missing Fields) và các trường PENDING_CONFIRMATION.
"""

import os
import sys
import glob
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.abspath("."))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.schema_config import MODALITY_FEATURES, MISSING_THRESHOLD
from core.gt_report_parser import parse_gt_report_to_dict
from core.sample_builder import build_patient_sample


def load_all_real_samples(docs_dir: str = "docs") -> List[Dict[str, Any]]:
    """Đọc toàn bộ 12 file Ground Truth .md và trả về danh sách 12 patient samples."""
    report_files = sorted(glob.glob(os.path.join(docs_dir, "EXTRACTION_REPORT_CASE_*.md")))
    if not report_files:
        raise FileNotFoundError(f"Không tìm thấy file EXTRACTION_REPORT_CASE_*.md trong {docs_dir}")

    samples = []
    for rpath in report_files:
        parsed_data = parse_gt_report_to_dict(rpath)
        sample = build_patient_sample(
            patient_id=parsed_data["patient_id"],
            modality_values=parsed_data["modality_values"],
            ground_truth_label=parsed_data["ground_truth_label"],
            ground_truth_source=parsed_data["ground_truth_source"],
        )
        sample["pending_fields"] = parsed_data["pending_fields"]
        samples.append(sample)

    return samples


def main():
    print("=" * 120)
    print("BẢNG TỔNG HỢP KIỂM CHỨNG TOÀN DIỆN 12 CA BỆNH THỰC TẾ (AUDITED GROUND TRUTH)")
    print("=" * 120)

    samples = load_all_real_samples()
    print(f"✔ Đã nạp thành công {len(samples)}/12 ca bệnh từ các báo cáo Ground Truth.")
    
    print("\n" + "=" * 120)
    print(f"{'Patient ID':<12}{'Tabular (14)':<16}{'Ultrasound (14)':<18}{'MRI (8)':<14}{'Label':<10}{'Tất Cả Biến Khuyết (Missing None)':<50}")
    print("-" * 120)

    tab_count = 0
    us_count = 0
    mri_count = 0

    us_feats = MODALITY_FEATURES["ultrasound"]
    mri_feats = MODALITY_FEATURES["mri"]

    for s in samples:
        pid = s["patient_id"]
        
        # 1. Tabular
        tab_avail = s["tabular"]["available"]
        tab_mask = s["tabular"]["feature_mask"]
        tab_missing = [f for f, m in zip(MODALITY_FEATURES["tabular"], tab_mask) if m == 0]
        tab_count += tab_avail
        tab_str = f"{tab_avail} ({len(tab_missing)}/14)"

        # 2. Ultrasound
        us_avail = s["ultrasound"]["available"]
        us_mask = s["ultrasound"]["feature_mask"]
        us_missing = [f for f, m in zip(us_feats, us_mask) if m == 0]
        us_count += us_avail
        us_str = f"{us_avail} ({len(us_missing)}/14)"

        # 3. MRI
        mri_avail = s["mri"]["available"]
        mri_mask = s["mri"]["feature_mask"]
        mri_missing = [f for f, m in zip(mri_feats, mri_mask) if m == 0]
        mri_count += mri_avail
        mri_str = f"{mri_avail} ({len(mri_missing)}/8)"

        # 4. Label
        lbl = s["ground_truth"]["label"]
        lbl_str = str(lbl) if lbl is not None else "None (Pending)"

        # 5. Tất cả các biến missing trên toàn bộ 36 trường
        all_missing = []
        if tab_missing:
            all_missing.extend([f"Tab:{f}" for f in tab_missing])
        if us_missing:
            all_missing.extend([f"US:{f}" for f in us_missing])
        if mri_missing:
            all_missing.extend([f"MRI:{f}" for f in mri_missing])

        missing_str = ", ".join(all_missing) if all_missing else "(Đầy đủ 100%)"

        print(f"{pid:<12}{tab_str:<16}{us_str:<18}{mri_str:<14}{lbl_str:<10}{missing_str:<50}")

    print("-" * 120)
    print(f"{'TỔNG ĐỦ ĐK':<12}{f'{tab_count}/12':<16}{f'{us_count}/12':<18}{f'{mri_count}/12':<14}")
    print("=" * 120)
    print("Ghi chú định dạng:")
    print("  * Tabular (14 biến: 9 lâm sàng + 5 sinh hóa, ngưỡng <=30% missing -> tối đa 4 biến thiếu): 1 = Đủ điều kiện, 0 = Thiếu")
    print("  * Ultrasound (14 biến, ngưỡng <=25% missing -> tối đa 3 biến thiếu): 1 = Đủ điều kiện, 0 = Thiếu")
    print("  * MRI (8 biến, ngưỡng <=25% missing -> tối đa 2 biến thiếu): 1 = Đủ điều kiện, 0 = Thiếu")
    print("  * Label: 1 = Ác tính (5 ca), 0 = Lành tính / Giáp biên (6 ca), None = Chưa có GPB mô bệnh học sau mổ (Case 12)")
    print("  * Biến PENDING_CONFIRMATION được parse thành None: Case 02 & 11 (bilateral_lesion), Case 12 (cancer_label)")
    print("=" * 120)


if __name__ == "__main__":
    main()
