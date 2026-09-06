# -*- coding: utf-8 -*-
"""
Module parser chuyên dụng: Đọc và bóc tách dữ liệu từ các tệp báo cáo Ground Truth chuẩn hóa
(docs/EXTRACTION_REPORT_CASE_01.md -> CASE_12.md) thành cấu trúc sample chuẩn của hệ thống.

NGUYÊN TẮC QUAN TRỌNG:
1. Thứ tự và tên biến tuân thủ 100% MODALITY_FEATURES trong config/schema_config.py.
2. Xử lý PENDING_CONFIRMATION: Mọi trường đang chờ bác sĩ xác nhận (ví dụ: bilateral_lesion ở Case 02, Case 11)
   BẮT BUỘC parse thành None (không lấy giá trị tạm thời), đồng thời ghi lại vào pending_fields.
3. Xử lý Missing: Giá trị 'None', 'null', 'MISSING_NULL', 'CHUA RO / CAN BAC SI XAC NHAN' -> parse thành None.
4. Ép kiểu chuẩn: int, float, str hoặc None.
5. Giá trị và trạng thái pending được lưu theo (modality, field), không gộp US/MRI.
"""

import os
import re
from typing import Dict, Any, List, Tuple, Optional

from config.schema_config import MODALITY_FEATURES, MODALITY_NAMES


INTEGER_FIELDS = {
    "age", "menopause", "pregnancy_status", "bilateral_lesion",
    "prior_ovarian_surgery", "other_cancer_history", "oncology_center_flag",
    "papillary_count", "more_than_10_locules", "acoustic_shadow", "ascites",
    "doppler_score", "morphology_class", "solid_component_present", "multilocular",
    "irregular_wall_or_septa", "iota_adnex_available",
    "solid_component", "TIC", "restricted_diffusion", "thick_septa",
    "ascites_mri", "morphology_class_mri", "o_rads_mri", "cancer_label"
}

FLOAT_FIELDS = {
    "months_detection_to_surgery", "CA125", "HE4", "AFP", "beta_hCG", "ROMA",
    "lesion_max_diameter_mm", "solid_max_diameter_mm"
}

STRING_FIELDS = {
    "laterality", "vascularity_description", "other_cancer_primary_site"
}


def _clean_str(text: str) -> str:
    """Làm sạch ký tự markdown, khoảng trắng thừa."""
    return text.strip("`* \"'").strip()


def _field_key(field_name: str, modality: Optional[str]) -> Tuple[Optional[str], str]:
    """Resolve schema scope; a shared field requires an explicit modality."""
    candidates = [name for name, features in MODALITY_FEATURES.items() if field_name in features]
    if not candidates:
        return None, field_name  # Ground truth and non-feature report metadata.
    if modality is not None:
        if modality not in candidates:
            raise ValueError(f"Field {field_name} không thuộc modality {modality}")
        return modality, field_name
    if len(candidates) > 1:
        raise ValueError(f"Field {field_name} thiếu modality; không thể phân biệt {candidates}")
    return candidates[0], field_name


def parse_gt_report_to_dict(report_path: str) -> Dict[str, Any]:
    """
    Đọc 1 file EXTRACTION_REPORT_CASE_XX.md và trả về dict chứa:
    - patient_id
    - modality_values: {tabular: {...}, ultrasound: {...}, mri: {...}}
    - ground_truth_label: int (0 hoặc 1) hoặc None
    - ground_truth_source: str
    - pending_fields: List[Dict[str, str]] ghi lại các trường PENDING_CONFIRMATION
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Không tìm thấy file Ground Truth: {report_path}")

    # 1. Xác định patient_id từ tên file hoặc nội dung
    basename = os.path.basename(report_path)
    case_match = re.search(r'CASE_(\d+)', basename, re.IGNORECASE)
    if case_match:
        case_num = int(case_match.group(1))
        patient_id = f"case_{case_num:02d}"
    else:
        patient_id = basename.replace(".md", "")

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Tìm danh sách các trường PENDING_CONFIRMATION trong Mục 2
    pending_fields_set = set()
    pending_notes = []

    # Tìm phần 2: Trường cần bác sĩ xác nhận (PENDING_CONFIRMATION)
    sec2_match = re.search(r'## 2\.\s*Trường cần bác sĩ xác nhận.*?(?=(?:\n## |\Z))', content, re.DOTALL | re.IGNORECASE)
    if sec2_match:
        sec2_text = sec2_match.group(0)
        # Bắt các bullet point dạng: * `field_name`: [PENDING_CONFIRMATION] hoặc * field_name:
        for line in sec2_text.splitlines():
            line_s = line.strip()
            if line_s.startswith("*") or line_s.startswith("-"):
                # Bắt tên field trong bullet point
                f_match = re.search(r'[*\-]\s*`?([a-zA-Z0-9_]+)(?:\s*\(([^)]+)\))?`?\s*:', line_s)
                if f_match:
                    f_name = f_match.group(1)
                    if "PENDING_CONFIRMATION" in line_s or "chưa rõ" in line_s.lower() or "cần bs" in line_s.lower() or "cần bác sĩ" in line_s.lower():
                        scope = f_match.group(2)
                        scope = scope.strip().lower() if scope else None
                        pending_fields_set.add(_field_key(f_name, scope))
                        pending_notes.append({"field": f_name, "note": line_s})

    # 3. Bóc tách từng bảng Markdown
    raw_extracted = {}
    current_modality = None

    for line in content.splitlines():
        line_s = line.strip()
        if line_s.startswith("#"):
            # Both report templates name their modality in the table heading.
            # Reset at every heading so unrelated tables cannot inherit a scope.
            current_modality = next(
                (name for name in MODALITY_NAMES
                 if re.search(rf"\b{re.escape(name)}\b", line_s, re.IGNORECASE)),
                None,
            )
            continue
        if not line_s.startswith("|"):
            continue
        parts = [p.strip() for p in line_s.split("|")]
        if len(parts) >= 3:
            field_name = _clean_str(parts[1])
            raw_val = _clean_str(parts[2])

            if "cancer_label" in field_name.lower():
                field_name = "cancer_label"

            # Bỏ qua header bảng
            if field_name in ["Field", "Tên biến", "Biến (Feature Name)", "Biến trong Schema", "Biến", "Hạng mục", "---", ""]:
                continue
            key = _field_key(field_name, current_modality)
            # Kiểm tra nếu field nằm trong danh sách pending hoặc dòng chứa nhãn PENDING_CONFIRMATION / CẦN BÁC SĨ XÁC NHẬN
            is_pending = (
                key in pending_fields_set or
                "PENDING_CONFIRMATION" in line_s.upper() or
                "CAN BAC SI XAC NHAN" in line_s.upper() or
                "CẦN BÁC SĨ XÁC NHẬN" in line_s.upper() or
                "CHƯA RÕ" in line_s.upper()
            )

            if is_pending:
                raw_extracted[key] = None
                if key not in pending_fields_set:
                    pending_fields_set.add(key)
                    pending_notes.append({"field": field_name, "note": f"Ghi nhận PENDING_CONFIRMATION/CHƯA RÕ cho {field_name}: '{line_s}'"})
                continue

            # Parse giá trị
            parsed_val = None
            raw_upper = raw_val.upper()

            if (
                raw_upper in ["NONE", "NULL", "MISSING_NULL", "CHUA RO", "CHƯA RÕ", "ABSENT", ""] or
                "CAN BAC SI XAC NHAN" in raw_upper or
                "CẦN BÁC SĨ XÁC NHẬN" in raw_upper or
                "CHƯA RÕ" in raw_upper
            ):
                parsed_val = None
            elif raw_upper in ["TRUE"]:
                parsed_val = 1
            elif raw_upper in ["FALSE"]:
                parsed_val = 0
            elif field_name in STRING_FIELDS:
                if raw_val.lower() in ["none", "null", "chưa rõ"]:
                    parsed_val = None
                else:
                    parsed_val = raw_val.lower()
            elif field_name == "cancer_label":
                # Nhãn chỉ nhận 0 hoặc 1 nếu đã chốt rõ ràng; nếu có chữ "cần xác nhận / chưa rõ" -> đã bị bắt ở is_pending trên
                num_m = re.search(r'[-+]?\d+', raw_val)
                if num_m and "CHƯA RÕ" not in raw_upper and "CẦN" not in raw_upper:
                    parsed_val = int(num_m.group(0))
                else:
                    parsed_val = None
            elif field_name in INTEGER_FIELDS:
                num_m = re.search(r'[-+]?\d+', raw_val)
                if num_m:
                    parsed_val = int(num_m.group(0))
                else:
                    parsed_val = None
            elif field_name in FLOAT_FIELDS:
                num_m = re.search(r'[-+]?\d*\.?\d+', raw_val)
                if num_m:
                    parsed_val = float(num_m.group(0))
                else:
                    parsed_val = None
            else:
                parsed_val = raw_val

            raw_extracted[key] = parsed_val

    # 4. Gói dữ liệu theo đúng cấu trúc MODALITY_FEATURES
    modality_values = {}

    for mod_name in MODALITY_NAMES:
        mod_dict = {}
        for feat in MODALITY_FEATURES[mod_name]:
            mod_dict[feat] = raw_extracted.get((mod_name, feat), None)
        modality_values[mod_name] = mod_dict

    # Lấy ground_truth_label
    gt_label = raw_extracted.get((None, "cancer_label"), None)

    return {
        "patient_id": patient_id,
        "modality_values": modality_values,
        "ground_truth_label": gt_label,
        "ground_truth_source": "pathology_report_post_surgery",
        "pending_fields": pending_notes,
    }
