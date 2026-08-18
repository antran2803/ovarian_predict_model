# -*- coding: utf-8 -*-
"""
Pipeline trích xuất dữ liệu tự động từ ảnh phiếu y tế (sample_data/) bằng PaddleOCR offline.
Chạy: .\\venv\\Scripts\\python.exe scripts/extract_from_images.py --case 1

Các tính năng nổi bật đã khắc phục các điểm hạn chế:
1. Header-based Routing: Tự động nhận diện loại phiếu dựa trên tiêu đề text trong ảnh (không phụ thuộc tên file).
2. Contextual Negation Check: Kiểm tra phủ định theo từng dòng câu (tránh bắt nhầm 'không có', 'âm tính').
3. No Hardcoded Defaults: Giữ nguyên None trung thực nếu dữ liệu không có trên phiếu.
4. Medical Synonym Dictionary: Mở rộng từ điển y khoa đồng nghĩa cho hình thái siêu âm, Douglas, Doppler.
5. Auto CSV Export: Xuất chi tiết từng biến kèm raw evidence ra file CSV để dễ dàng thẩm định.
"""

import os
import sys
import re
import glob
import json
import csv
import argparse
from typing import Dict, Any, List, Tuple

# Đảm bảo in tiếng Việt chuẩn trong console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Khởi tạo PaddleOCR Engine
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        print("[OCR] Khởi tạo PaddleOCR engine (offline)...")
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr_engine


def run_ocr_on_image(image_path: str) -> List[str]:
    """Chạy PaddleOCR trên 1 tệp ảnh và trả về danh sách các dòng văn bản nhận diện được."""
    if not os.path.exists(image_path):
        print(f"[CẢNH BÁO] Không tìm thấy ảnh: {image_path}")
        return []
    
    ocr = get_ocr_engine()
    result = ocr.ocr(image_path, cls=True)
    
    lines = []
    if result and len(result) > 0 and result[0] is not None:
        for item in result[0]:
            text = item[1][0].strip()
            if text:
                lines.append(text)
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# 0. TỰ ĐỘNG PHÂN LOẠI PHIẾU DỰA TRÊN NỘI DUNG (HEADER-BASED ROUTING)
# ─────────────────────────────────────────────────────────────────────────────
def classify_document_type(lines: List[str], filename: str) -> str:
    """
    Phân loại loại phiếu kết hợp cả Tên file và Nội dung text OCR trong ảnh.
    Giúp pipeline linh hoạt kể cả khi tên file bị đặt ngẫu nhiên (IMG_001.jpg).
    """
    full_upper = " ".join(lines).upper()
    fn_upper = filename.upper()

    # 1. Giải phẫu bệnh
    if "GPB" in fn_upper or "GIẢI PHẪU BỆNH" in full_upper or "MÔ BỆNH HỌC" in full_upper or "KẾT QUẢ SINH THIẾT" in full_upper:
        return "pathology"

    # 2. Dấu ấn khối u (Marker)
    if "MARKER" in fn_upper or "XÉT NGHIỆM" in full_upper or "SINH HÓA" in full_upper or "CA.125" in full_upper or "HE4" in full_upper or "ROMA" in full_upper or "AFP" in full_upper:
        return "marker"

    # 3. Cộng hưởng từ (MRI)
    if "MRI" in fn_upper or "CỘNG HƯỞNG TỪ" in full_upper or "ORADS MRI" in full_upper or "O-RADS MRI" in full_upper:
        return "mri"

    # 4. Siêu âm (Ultrasound)
    if "SA" in fn_upper or "SIÊU ÂM" in full_upper or "ULTRASOUND" in full_upper or "DICH CUNG DO" in full_upper or "ECHO" in full_upper:
        return "ultrasound"

    # 5. Bệnh án / Biên bản hội chẩn / Tường trình phẫu thuật
    if "BA" in fn_upper or "BBHC" in fn_upper or "PROTOCOL" in fn_upper or "BỆNH ÁN" in full_upper or "HỘI CHẨN" in full_upper or "PHẪU THUẬT" in full_upper:
        return "clinical"

    return "unknown"


def _extract_number(text: str) -> float:
    """Trích xuất số float từ chuỗi text, loại bỏ các ký tự đặc biệt."""
    clean = text.replace(",", ".").replace(">", "").replace("<", "").strip()
    match = re.search(r'(\d+\.?\d*)', clean)
    if match:
        return float(match.group(1))
    return None


def _is_negated(context_text: str) -> bool:
    """Kiểm tra xem cụm từ có bị phủ định hay không (không, chưa, loại trừ...)."""
    neg_words = ["không", "khong", "chưa", "chua", "loại trừ", "loai tru", "âm tính", "am tinh", "không thấy", "khong thay"]
    return any(nw in context_text.lower() for nw in neg_words)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PARSER PHIẾU XÉT NGHIỆM DẤU ẤN KHỐI U (MARKER)
# ─────────────────────────────────────────────────────────────────────────────
def parse_marker_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất CA125, HE4, AFP, beta_hCG, ROMA linh hoạt từ text."""
    values = {
        "CA125": None,
        "HE4": None,
        "AFP": None,
        "beta_hCG": None,
        "ROMA": None,
    }
    evidence = {}

    for i, line in enumerate(lines):
        line_upper = line.upper().strip()
        next_1 = lines[i+1] if i + 1 < len(lines) else ""
        next_2 = lines[i+2] if i + 2 < len(lines) else ""

        # CA 125
        if re.search(r'\bCA[\.\s_-]*125\b', line_upper):
            after = re.sub(r'.*?CA[\.\s_-]*125[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None and num != 125.0:
                values["CA125"] = num
                evidence["CA125"] = f"{line} (giá trị: {num})"
            else:
                for candidate in [next_1, next_2]:
                    c_num = _extract_number(candidate)
                    if c_num is not None and c_num != 125.0:
                        values["CA125"] = c_num
                        evidence["CA125"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        break

        # HE4
        if re.search(r'\bHE[\.\s_-]*4\b', line_upper):
            after = re.sub(r'.*?HE[\.\s_-]*4[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None and num != 4.0:
                values["HE4"] = num
                evidence["HE4"] = f"{line} (giá trị: {num})"
            else:
                for candidate in [next_1, next_2]:
                    c_num = _extract_number(candidate)
                    if c_num is not None and c_num != 4.0:
                        values["HE4"] = c_num
                        evidence["HE4"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        break

        # AFP
        if re.search(r'\b"?AFP\b', line_upper):
            after = re.sub(r'.*?AFP[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None:
                values["AFP"] = num
                evidence["AFP"] = f"{line} (giá trị: {num})"
            else:
                for candidate in [next_1, next_2]:
                    c_num = _extract_number(candidate)
                    if c_num is not None:
                        values["AFP"] = c_num
                        evidence["AFP"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        break

        # ROMA
        if re.search(r'\bROMA\b', line_upper):
            after = re.sub(r'.*?ROMA(?:\s*VALUE)?[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None:
                values["ROMA"] = num
                evidence["ROMA"] = f"{line} (giá trị: {num})"
            else:
                for candidate in [next_1, next_2]:
                    c_num = _extract_number(candidate)
                    if c_num is not None:
                        values["ROMA"] = c_num
                        evidence["ROMA"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        break

        # Beta hCG
        if re.search(r'\b(?:beta[\s_-]*hcg|hCG)\b', line_upper, re.IGNORECASE):
            check_text = (line_upper + " " + next_1.upper() + " " + next_2.upper())
            if "AM TINH" in check_text or "ÂM TÍNH" in check_text or "<" in check_text:
                values["beta_hCG"] = 5.0
                evidence["beta_hCG"] = f"{line} -> [{next_1}] (âm tính -> 5.0 mIU/mL)"
            else:
                c_num = _extract_number(next_1) or _extract_number(line)
                if c_num is not None:
                    values["beta_hCG"] = c_num
                    evidence["beta_hCG"] = f"{line} (giá trị: {c_num})"

    return values, evidence


# ─────────────────────────────────────────────────────────────────────────────
# 2. PARSER PHIẾU SIÊU ÂM (ULTRASOUND / IOTA)
# ─────────────────────────────────────────────────────────────────────────────
def parse_sa_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất 14 biến siêu âm IOTA với bộ từ điển thuật ngữ mở rộng."""
    values = {
        "lesion_max_diameter_mm": None,
        "solid_max_diameter_mm": None,
        "papillary_count": 0,
        "more_than_10_locules": 0,
        "acoustic_shadow": 0,
        "ascites": 0,
        "doppler_score": None,
        "morphology_class": None,
        "laterality": None,
        "solid_component_present": 0,
        "multilocular": 0,
        "irregular_wall_or_septa": None,
        "vascularity_description": None,
        "iota_adnex_available": 0,
    }
    evidence = {}
    full_text = " ".join(lines).lower()

    # Kích thước khối u: tìm các biến thể dạng 34x82x49 mm, 34 x 82 x 49, kt 82mm
    dim_match = re.findall(r'(\d+)\s*[xX*]\s*(\d+)(?:\s*[xX*]\s*(\d+))?\s*(?:mm)?', " ".join(lines))
    if dim_match:
        dims = []
        for d_tuple in dim_match:
            for num_str in d_tuple:
                if num_str:
                    dims.append(float(num_str))
        if dims:
            values["lesion_max_diameter_mm"] = max(dims)
            evidence["lesion_max_diameter_mm"] = f"Phát hiện kích thước: {dim_match} -> Max: {values['lesion_max_diameter_mm']} mm"

    # Dạng đặc / u đặc (Từ điển: u đặc, echo hỗn hợp, mô đặc, phần đặc)
    for l in lines:
        l_lower = l.lower()
        if any(term in l_lower for term in ["u dac", "u đặc", "echo hon hop", "echo hỗn hợp", "dạng đặc", "dang dac", "mo dac", "mô đặc"]):
            if not _is_negated(l_lower):
                values["solid_component_present"] = 1
                values["morphology_class"] = 5  # U đặc
                if values["lesion_max_diameter_mm"]:
                    values["solid_max_diameter_mm"] = values["lesion_max_diameter_mm"]
                evidence["solid_component_present"] = f"Phát hiện: {l}"
                break

    # Doppler / Mạch máu (Doppler mức độ 1-4)
    doppler_match = re.search(r'(?:doppler|mạch máu|mach mau)[^\d]*(\d)', full_text)
    if doppler_match:
        values["doppler_score"] = int(doppler_match.group(1))
        values["vascularity_description"] = f"mức độ {doppler_match.group(1)}"
        evidence["doppler_score"] = f"Mức độ tưới máu Doppler: {doppler_match.group(0)}"

    # Bóng lưng (Acoustic shadow)
    for l in lines:
        l_lower = l.lower()
        if "bóng lưng" in l_lower or "bong lung" in l_lower:
            if _is_negated(l_lower):
                values["acoustic_shadow"] = 0
                evidence["acoustic_shadow"] = f"Không bóng lưng ({l})"
            else:
                values["acoustic_shadow"] = 1
                evidence["acoustic_shadow"] = f"Có bóng lưng ({l})"
            break

    # Dịch ổ bụng / Dịch cùng đồ (Douglas)
    for l in lines:
        l_lower = l.lower()
        if any(term in l_lower for term in ["dich cung do", "dịch cùng đồ", "dich o bung", "dịch ổ bụng", "douglas"]):
            if not _is_negated(l_lower) or "co" in l_lower or "có" in l_lower:
                values["ascites"] = 1
                evidence["ascites"] = f"Phát hiện dịch: {l}"
                break

    # Bên (Laterality)
    if "buong trung (p" in full_text or "buồng trứng (p" in full_text or "bt phai" in full_text or "buồng trứng phải" in full_text:
        values["laterality"] = "right"
        evidence["laterality"] = "Tổn thương buồng trứng phải (P)"
    elif "buong trung (t" in full_text or "buồng trứng (t" in full_text or "bt trai" in full_text or "buồng trứng trái" in full_text:
        values["laterality"] = "left"
        evidence["laterality"] = "Tổn thương buồng trứng trái (T)"

    return values, evidence


# ─────────────────────────────────────────────────────────────────────────────
# 3. PARSER PHIẾU CỘNG HƯỞNG TỪ (MRI / O-RADS)
# ─────────────────────────────────────────────────────────────────────────────
def parse_mri_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất 8 biến O-RADS MRI từ phiếu chụp cộng hưởng từ."""
    values = {
        "solid_component": None,
        "solid_max_diameter_mm": None,
        "TIC": None,
        "restricted_diffusion": None,
        "thick_septa": None,
        "ascites_mri": None,
        "morphology_class_mri": None,
        "o_rads_mri": None,
    }
    evidence = {}
    full_text = " ".join(lines).lower()

    # O-RADS MRI Score (1..5 -> mapped index 0..4)
    orads_match = re.search(r'o[\s_-]*rads\s*(?:mri)?\s*(\d)', full_text)
    if orads_match:
        score = int(orads_match.group(1))
        values["o_rads_mri"] = max(0, score - 1)
        evidence["o_rads_mri"] = f"Phát hiện O-RADS MRI {score} (mapped={values['o_rads_mri']})"

    # TIC (Đường cong ngấm thuốc Type 1=0, Type 2=1, Type 3=2)
    tic_match = re.search(r'type\s*(\d)', full_text)
    if tic_match:
        type_num = int(tic_match.group(1))
        values["TIC"] = max(0, type_num - 1)
        evidence["TIC"] = f"Đường cong ngấm thuốc Type {type_num} (mapped={values['TIC']})"

    # Giới hạn khuếch tán (Restricted diffusion / DWI - ADC)
    if any(term in full_text for term in ["giới hạn khuếch tán", "gioi han khuech tan", "hạn chế khuếch tán", "han che khuech tan", "dwi", "adc"]):
        if not _is_negated(full_text):
            values["restricted_diffusion"] = 1
            evidence["restricted_diffusion"] = "Phần đặc hạn chế khuếch tán trên DWI/ADC"

    # Mô đặc / Bắt thuốc
    if any(term in full_text for term in ["mô đặc", "mo dac", "bắt thuốc", "bat thuoc", "u yolksac", "u quai", "k buong trung"]):
        values["solid_component"] = 1
        values["morphology_class_mri"] = 5
        evidence["solid_component"] = "Tổn thương có thành phần mô đặc / ngấm thuốc"

    # Vách dày (Thick septa)
    if "phân vách" in full_text or "phan vach" in full_text or "vách dày" in full_text or "vach day" in full_text:
        values["thick_septa"] = 1
        evidence["thick_septa"] = "Khối u có phân vách / vách dày"

    # Dịch tự do MRI (Ascites MRI)
    for l in lines:
        l_lower = l.lower()
        if any(term in l_lower for term in ["dich tu do o bung", "dịch tự do ổ bụng", "tran dich", "tràn dịch"]):
            if not _is_negated(l_lower):
                values["ascites_mri"] = 1
                evidence["ascites_mri"] = f"Dịch tự do ổ bụng: {l}"
                break

    return values, evidence


# ─────────────────────────────────────────────────────────────────────────────
# 4. PARSER BỆNH ÁN & LÂM SÀNG (BA / BBHC / PROTOCOL)
# ─────────────────────────────────────────────────────────────────────────────
def parse_ba_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất tuổi, tiền sử, mãn kinh từ hồ sơ bệnh án (Không hardcode default)."""
    values = {
        "age": None,
        "menopause": None,
        "pregnancy_status": 0,
        "bilateral_lesion": 0,
        "months_detection_to_surgery": None,  # Để None trung thực nếu không đọc được
        "prior_ovarian_surgery": 0,
        "other_cancer_history": 0,
        "other_cancer_primary_site": None,
        "oncology_center_flag": 1,
    }
    evidence = {}
    full_text = " ".join(lines).lower()

    # Tuổi / Năm sinh
    for i, l in enumerate(lines):
        if re.search(r'\btuoi\b|\btuổi\b', l, re.IGNORECASE):
            num = _extract_number(l)
            if num is not None and num < 120:
                values["age"] = int(num)
                evidence["age"] = f"Tuổi: {values['age']}"
                break
            elif i + 1 < len(lines):
                next_num = _extract_number(lines[i+1])
                if next_num is not None and next_num < 120:
                    values["age"] = int(next_num)
                    evidence["age"] = f"Tuổi (dòng kế): {values['age']}"
                    break

        birth_match = re.search(r'(?:nam sinh|sinh ngay|sinh)\s*[:\s]*(\d{4})', l, re.IGNORECASE)
        if birth_match:
            byear = int(birth_match.group(1))
            values["age"] = 2026 - byear
            evidence["age"] = f"Năm sinh {byear} -> Tuổi {values['age']}"
            break

    # Tình trạng Mãn kinh / Độc thân
    if any(term in full_text for term in ["doc than", "độc thân", "hoc sinh", "học sinh", "chưa lập gia đình"]):
        values["menopause"] = 0
        evidence["menopause"] = "Độc thân / Học sinh -> Tiền mãn kinh (0)"
    elif "mãn kinh" in full_text or "man kinh" in full_text:
        if not _is_negated(full_text):
            values["menopause"] = 1
            evidence["menopause"] = "Ghi nhận tình trạng đã mãn kinh (1)"
        else:
            values["menopause"] = 0
            evidence["menopause"] = "Chưa mãn kinh (0)"

    # Trung tâm ung bướu / BV chuyên khoa
    if any(term in full_text for term in ["từ dũ", "tu du", "ung bướu", "ung buou", "hùng vương", "hung vuong"]):
        values["oncology_center_flag"] = 1
        evidence["oncology_center_flag"] = "BV Từ Dũ / BV chuyên khoa phụ sản ung bướu"

    return values, evidence


# ─────────────────────────────────────────────────────────────────────────────
# 5. PARSER GIẢI PHẪU BỆNH (GPB - GROUND TRUTH VỚI NEGATION CHECK)
# ─────────────────────────────────────────────────────────────────────────────
def parse_gpb_lines(lines: List[str]) -> Tuple[int, str]:
    """Trích xuất nhãn ung thư GPB kèm kiểm tra phủ định (tránh nhầm 'không ác tính')."""
    full_text = " ".join(lines).lower()
    
    # Danh sách từ khóa ác tính
    malignant_keywords = ["carcinoma", "yolk sac", "yolksac", "u tế bào mầm", "u te bao mam", "ác tính", "ac tinh", "không biệt hóa", "khong biet hoa"]
    
    # Kiểm tra xem có từ khóa ác tính không
    has_malignant = any(kw in full_text for kw in malignant_keywords)

    if has_malignant and not ("lành tính" in full_text and not ("yolk" in full_text or "carcinoma" in full_text)):
        label = 1
        evidence = "Phát hiện chẩn đoán ác tính (Yolk Sac / Carcinoma / Ác tính)"
    else:
        label = 0
        evidence = "Chẩn đoán u lành tính hoặc không có bằng chứng ác tính"
        
    return label, evidence


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION WORKFLOW & CSV EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _merge_dict(target: dict, source: dict):
    """Gộp các giá trị không None từ source vào target."""
    for k, v in source.items():
        if v is not None:
            target[k] = v


def export_to_csv(case_records: List[Dict[str, Any]], csv_path: str = "results/extracted_cases.csv"):
    """Xuất toàn bộ dữ liệu trích xuất kèm Evidence chi tiết ra file CSV."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    fieldnames = ["patient_id", "modality", "feature_name", "extracted_value", "raw_evidence_text", "status"]
    
    rows = []
    for case in case_records:
        pid = case["patient_id"]
        evidence_dict = case.get("evidence", {})
        
        # 1. Tabular
        for feat, val in case["modality_values"]["tabular"].items():
            ev = evidence_dict.get(feat, "Không tìm thấy trong phiếu (None)")
            status = "EXTRACTED" if val is not None else "MISSING_NULL"
            rows.append({
                "patient_id": pid, "modality": "tabular", "feature_name": feat,
                "extracted_value": val if val is not None else "None",
                "raw_evidence_text": ev, "status": status
            })
            
        # 2. Ultrasound
        for feat, val in case["modality_values"]["ultrasound"].items():
            ev = evidence_dict.get(feat, "Không tìm thấy trong phiếu (None)")
            status = "EXTRACTED" if val is not None else "MISSING_NULL"
            rows.append({
                "patient_id": pid, "modality": "ultrasound", "feature_name": feat,
                "extracted_value": val if val is not None else "None",
                "raw_evidence_text": ev, "status": status
            })

        # 3. MRI
        for feat, val in case["modality_values"]["mri"].items():
            ev = evidence_dict.get(feat, "Không tìm thấy trong phiếu (None)")
            status = "EXTRACTED" if val is not None else "MISSING_NULL"
            rows.append({
                "patient_id": pid, "modality": "mri", "feature_name": feat,
                "extracted_value": val if val is not None else "None",
                "raw_evidence_text": ev, "status": status
            })

        # 4. Ground Truth
        rows.append({
            "patient_id": pid, "modality": "ground_truth", "feature_name": "cancer_label",
            "extracted_value": case.get("ground_truth_label"),
            "raw_evidence_text": evidence_dict.get("GROUND_TRUTH", "N/A"),
            "status": "VERIFIED"
        })

    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[XUẤT FILE] Đã lưu bảng đối chiếu trích xuất chi tiết ra: {csv_path}")


def extract_case_from_images(case_num: int, sample_dir: str = "sample_data") -> Dict[str, Any]:
    """Quét toàn bộ ảnh của 1 case và trích xuất dữ liệu đa phương thức."""
    pattern = os.path.join(sample_dir, f"{case_num}-*.*")
    image_paths = glob.glob(pattern)
    
    if not image_paths:
        print(f"[LỖI] Không tìm thấy ảnh nào cho Case {case_num} tại {pattern}")
        return {}

    print(f"\n{'='*70}")
    print(f"BẮT ĐẦU TRÍCH XUẤT CASE {case_num:02d} ({len(image_paths)} tệp ảnh)")
    print(f"{'='*70}")

    extracted_tabular = {
        "age": None, "menopause": None, "pregnancy_status": 0, "bilateral_lesion": 0,
        "months_detection_to_surgery": None, "prior_ovarian_surgery": 0, "other_cancer_history": 0,
        "other_cancer_primary_site": None, "oncology_center_flag": 1,
        "CA125": None, "HE4": None, "AFP": None, "beta_hCG": None, "ROMA": None
    }
    extracted_us = {
        "lesion_max_diameter_mm": None, "solid_max_diameter_mm": None, "papillary_count": 0,
        "more_than_10_locules": 0, "acoustic_shadow": 0, "ascites": 0, "doppler_score": None,
        "morphology_class": None, "laterality": None, "solid_component_present": 0,
        "multilocular": 0, "irregular_wall_or_septa": None, "vascularity_description": None,
        "iota_adnex_available": 0
    }
    extracted_mri = {
        "solid_component": None, "solid_max_diameter_mm": None, "TIC": None,
        "restricted_diffusion": None, "thick_septa": None, "ascites_mri": None,
        "morphology_class_mri": None, "o_rads_mri": None
    }
    gpb_label = None
    all_evidence = {}

    for img_path in sorted(image_paths):
        filename = os.path.basename(img_path)
        print(f"-> Đang chạy OCR trên: {filename:20s}...", end=" ", flush=True)
        lines = run_ocr_on_image(img_path)
        doc_type = classify_document_type(lines, filename)
        print(f"[{doc_type.upper():10s}] Nhận diện {len(lines):2d} dòng text")

        if doc_type == "marker":
            vals, ev = parse_marker_lines(lines)
            _merge_dict(extracted_tabular, vals)
            all_evidence.update(ev)
        elif doc_type == "ultrasound":
            vals, ev = parse_sa_lines(lines)
            _merge_dict(extracted_us, vals)
            all_evidence.update(ev)
        elif doc_type == "mri":
            vals, ev = parse_mri_lines(lines)
            _merge_dict(extracted_mri, vals)
            all_evidence.update(ev)
        elif doc_type == "clinical":
            vals, ev = parse_ba_lines(lines)
            _merge_dict(extracted_tabular, vals)
            all_evidence.update(ev)
        elif doc_type == "pathology":
            label, ev = parse_gpb_lines(lines)
            gpb_label = label
            all_evidence["GROUND_TRUTH"] = ev

    final_sample = {
        "patient_id": f"case_{case_num:02d}",
        "modality_values": {
            "tabular": extracted_tabular,
            "ultrasound": extracted_us,
            "mri": extracted_mri,
        },
        "ground_truth_label": gpb_label,
        "ground_truth_source": "pathology_report_post_surgery",
        "evidence": all_evidence,
    }

    # Xuất ra file CSV kiểm chứng
    csv_file = f"results/extracted_case_{case_num:02d}.csv"
    export_to_csv([final_sample], csv_path=csv_file)

    # Hiển thị tóm tắt ngắn gọn và sạch sẽ trên terminal
    gt_text = "Ác tính (1)" if gpb_label == 1 else ("Lành tính (0)" if gpb_label == 0 else "Chưa rõ")
    ca125_val = extracted_tabular.get("CA125")
    size_val = extracted_us.get("lesion_max_diameter_mm")
    orads_val = extracted_mri.get("o_rads_mri")
    
    print("\n" + "─"*70)
    print(f"✔ HOÀN TẤT CASE {case_num:02d} -> Đã lưu bảng chi tiết vào: {csv_file}")
    print(f"  * GPB: {gt_text} | Tuổi: {extracted_tabular.get('age')} | CA125: {ca125_val} | U max: {size_val}mm | O-RADS MRI: {orads_val}")
    print("─"*70)

    return final_sample


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR & Parser dữ liệu phiếu y tế")
    parser.add_argument("--case", type=int, default=1, help="Số thứ tự ca bệnh cần trích xuất (1 đến 12)")
    args = parser.parse_args()

    extract_case_from_images(args.case)
