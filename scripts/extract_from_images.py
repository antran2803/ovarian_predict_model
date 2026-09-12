# -*- coding: utf-8 -*-
"""
Pipeline trích xuất dữ liệu tự động từ ảnh phiếu y tế (sample_data/) bằng PaddleOCR offline.
Chạy: .\\venv\\Scripts\\python.exe scripts/extract_from_images.py --case 1

Kiến trúc 4 lớp (v2 — Bước 2, tái thiết kế 2026-08-22):
  LỚP 1 – Normalization : normalize_ocr_text() — chuẩn hóa ký tự OCR, tách số dính chữ.
  LỚP 2 – Routing       : classify_document_type() — nhận diện loại phiếu.
  LỚP 3 – Extraction    : parse_ba/sa/mri/marker/gpb — trích xuất giá trị theo ngữ cảnh cục bộ.
  LỚP 4 – Validation    : validate_extracted_values() — kiểm tra range, Missing != 0.
"""

import os
import sys
import re
import glob
import json
import csv
import argparse
from datetime import datetime
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
        print("[OCR] Khởi tạo PaddleOCR engine (lang='vi', det_limit_side_len=2500, offline)...")
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="vi", det_limit_side_len=2500, det_db_box_thresh=0.3, show_log=False)
    return _ocr_engine


def run_ocr_on_image(image_path: str) -> List[str]:
    """Chạy PaddleOCR trên 1 tệp ảnh và trả về danh sách các dòng văn bản nhận diện được."""
    if not os.path.exists(image_path):
        print(f"[CẢNH BÁO] Không tìm thấy ảnh: {image_path}")
        return []
    
    import cv2
    ocr = get_ocr_engine()
    
    # Đối với phiếu xét nghiệm sinh hóa/marker: dùng ảnh gốc để giữ trọn vẹn nét chữ số mảnh
    # Đối với phiếu chụp MRI/Siêu âm: áp dụng CLAHE để phát hiện các dòng chữ nhỏ ở khối giữa
    filename_lower = os.path.basename(image_path).lower()
    if "marker" in filename_lower:
        result = ocr.ocr(image_path, cls=True)
    else:
        img = cv2.imread(image_path)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            result = ocr.ocr(enhanced_bgr, cls=True)
        else:
            result = ocr.ocr(image_path, cls=True)
    
    lines = []
    if result and len(result) > 0 and result[0] is not None:
        for item in result[0]:
            text = item[1][0].strip()
            if text:
                lines.append(text)
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# LỚP 1: NORMALIZATION — Chuẩn hóa text OCR thô trước mọi bước xử lý
# ─────────────────────────────────────────────────────────────────────────────

# Bảng chuẩn hóa ký tự OCR lỗi phổ biến trong văn bản tiếng Việt PaddleOCR
OCR_CHAR_MAP = {
    'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
    'ą': 'a',  # ký tự Ba Lan đôi khi xuất hiện
}

# Patterns tách số/từ dính chữ trong văn bản y tế Việt (dùng cho re.sub)
DINH_CHU_PATTERNS = [
    # Tuoi22 -> Tuoi 22 ; Tuoi:40 -> Tuoi 40
    (r'(?i)(Tuoi)[:\s]*(\d+)', r'\1 \2'),
    # NamSinh2004 -> Nam Sinh 2004 ; namsinhnam2004 -> nam sinh 2004
    (r'(?i)(Nam\s*sinh)(\d{4})', r'\1 \2'),
    # BENHVIENTUDO -> BENH VIEN TU DO
    (r'(?i)(BENHVIEN)(TUDO|TUDU|HUNGVUONG)', r'\1 \2'),
    # ROMAVALUE -> ROMA VALUE
    (r'(?i)(ROMA)(VALUE)', r'\1 \2'),
    # Tách số dính mã xét nghiệm (CA125: -> CA 125 :)
    (r'(?i)(CA)[.\s]*(125)', r'CA.125'),
]


def normalize_ocr_text(lines: List[str]) -> List[str]:
    """
    LỚP 1 NORMALIZATION: Chuẩn hóa danh sách dòng text OCR thô.
    Gọi một lần ngay sau run_ocr_on_image(), trước mọi bước parse.
    """
    result = []
    for line in lines:
        # 1. Chuẩn hóa ký tự lỗi OCR (umlaut, ký tự đặc biệt)
        for bad_char, good_char in OCR_CHAR_MAP.items():
            line = line.replace(bad_char, good_char)
        # 2. Tách số/từ dính theo bảng pattern
        for pattern, replacement in DINH_CHU_PATTERNS:
            line = re.sub(pattern, replacement, line)
        result.append(line)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# LỚP 2: DOCUMENT ROUTING — Phân loại phiếu dựa trên nội dung
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
    is_marker_by_name = "MARKER" in fn_upper
    is_marker_by_content = ("XÉT NGHIỆM" in full_upper or "SINH HÓA" in full_upper) and ("CA.125" in full_upper or "HE4" in full_upper or "ROMA" in full_upper)
    if is_marker_by_name or is_marker_by_content:
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
    """
    Kiểm tra xem cụm từ có bị phủ định hay không (không có, âm tính, không thấy...).
    Loại trừ các cụm từ bệnh học như 'không trưởng thành' (immature), 'chưa loại trừ' (cannot rule out), 'không đồng nhất' (heterogeneous).
    """
    text = context_text.lower()
    
    # Loại bỏ các cụm từ y khoa chứa chữ 'không'/'chưa' nhưng KHÔNG PHẢI phủ định tổn thương
    exempt_terms = [
        "không trưởng thành", "khong truong thanh", "không truong thanh",
        "chưa loại trừ", "chua loai tru", "chưa loại trừ:", "chua loai tru:",
        "không đồng nhất", "khong dong nhat", "không thuần nhất", "khong thuan nhat",
        "không rõ", "khong ro", "không đều", "khong deu"
    ]
    cleaned_text = text
    for term in exempt_terms:
        cleaned_text = cleaned_text.replace(term, " ")

    neg_words = ["không thấy", "khong thay", "không có", "khong co", "khong co",
                 "không phát hiện", "khong phat hien", "âm tính", "am tinh",
                 "chưa thấy", "chua thay", "bình thường", "binh thuong",
                 # Các biến thể OCR lỗi của "không"
                 "khng co", "kh6ng", "<hong co", "6ng co",
                 "khong sang",  # "không sáng" trên DWI
                 "khong tang sinh",  # "không tăng sinh mạch máu"
                 ]
    return any(nw in cleaned_text for nw in neg_words)


def _get_local_context(lines: List[str], idx: int, window: int = 2) -> str:
    """
    Lấy ngữ cảnh CỤC BỘ ±window dòng quanh dòng idx.
    Dùng để thay thế full_text trong các phủ định check — tránh phủ định TẦM XA.
    """
    start = max(0, idx - window)
    end = min(len(lines), idx + window + 1)
    return " ".join(lines[start:end]).lower()


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
        # Dòng trước nhãn — dùng khi phiếu bố cục đảo (value trước, label sau)
        prev_1 = lines[i-1] if i >= 1 else ""
        prev_2 = lines[i-2] if i >= 2 else ""
        prev_3 = lines[i-3] if i >= 3 else ""

        # CA 125 — Hỗ trợ cả 2 bố cục: label-trước-value (Case 01) và value-trước-label (Case 02)
        if re.search(r'\bCA[\.\s_-]*125\b', line_upper):
            # 1. Tìm số trên cùng dòng sau cụm "CA.125"
            after = re.sub(r'.*?CA[\.\s_-]*125[:\s]*', '', line_upper)
            after_stripped = re.sub(r'\([^)]*\)', '', after).strip()
            num = _extract_number(after_stripped) if after_stripped else None
            if num is not None and num != 125.0:
                values["CA125"] = num
                evidence["CA125"] = f"{line} (giá trị: {num})"
            else:
                # 2. Tìm forward (next_1, next_2) — layout chuẩn
                found = False
                for candidate in [next_1, next_2]:
                    cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                    # Bỏ qua nếu dòng chứa mã xét nghiệm / đơn vị (như "MD-13/Ali", "pmol/L", "U/mL")
                    if re.search(r'[A-Za-z]{2,}', cand_stripped):
                        continue
                    c_num = _extract_number(cand_stripped)
                    if c_num is not None and c_num != 125.0:
                        values["CA125"] = c_num
                        evidence["CA125"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        found = True; break
                if not found:
                    # 3. Fallback backward (prev_1, prev_2, prev_3) — layout đảo cột (Case 02)
                    for candidate in [prev_1, prev_2, prev_3]:
                        cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if re.search(r'[A-Za-z]{2,}', cand_stripped):
                            continue
                        c_num = _extract_number(cand_stripped)
                        if c_num is not None and c_num != 125.0:
                            values["CA125"] = c_num
                            evidence["CA125"] = f"{line} <- [{candidate}] (giá trị: {c_num}, layout đảo cột)"
                            break

        # HE4
        if re.search(r'\bHE[\.\s_-]*4\b', line_upper):
            after = re.sub(r'.*?HE[\.\s_-]*4[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None and num != 4.0:
                values["HE4"] = num
                evidence["HE4"] = f"{line} (giá trị: {num})"
            else:
                found = False
                for candidate in [next_1, next_2]:
                    cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                    if re.search(r'[A-Za-z]{2,}', cand_stripped):
                        continue
                    c_num = _extract_number(cand_stripped)
                    if c_num is not None and c_num != 4.0:
                        values["HE4"] = c_num
                        evidence["HE4"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        found = True; break
                if not found:
                    for candidate in [prev_1, prev_2, prev_3]:
                        cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if re.search(r'[A-Za-z]{2,}', cand_stripped):
                            continue
                        c_num = _extract_number(cand_stripped)
                        if c_num is not None and c_num != 4.0:
                            values["HE4"] = c_num
                            evidence["HE4"] = f"{line} <- [{candidate}] (giá trị: {c_num}, layout đảo cột)"
                            break

        # AFP
        if re.search(r'\b"?AFP\b', line_upper):
            after = re.sub(r'.*?AFP[:\s]*', '', line_upper)
            num = _extract_number(after) if after else None
            if num is not None:
                values["AFP"] = num
                evidence["AFP"] = f"{line} (giá trị: {num})"
            else:
                found = False
                for candidate in [next_1, next_2]:
                    cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                    if re.search(r'[A-Za-z]{2,}', cand_stripped):
                        continue
                    c_num = _extract_number(cand_stripped)
                    if c_num is not None:
                        values["AFP"] = c_num
                        evidence["AFP"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        found = True; break
                if not found:
                    for candidate in [prev_1, prev_2, prev_3]:
                        cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if re.search(r'[A-Za-z]{2,}', cand_stripped):
                            continue
                        c_num = _extract_number(cand_stripped)
                        if c_num is not None:
                            values["AFP"] = c_num
                            evidence["AFP"] = f"{line} <- [{candidate}] (giá trị: {c_num}, layout đảo cột)"
                            break

        # ROMA — Hỗ trợ cả 2 layout (forward + backward)
        if re.search(r'\bROMA\b', line_upper):
            after = re.sub(r'.*?ROMA(?:\s*VALUE)?[:\s]*', '', line_upper)
            after_stripped = re.sub(r'\([^)]*\)', '', after).strip()
            num = _extract_number(after_stripped) if after_stripped else None
            if num is not None:
                values["ROMA"] = num
                evidence["ROMA"] = f"{line} (giá trị: {num})"
            else:
                found = False
                for candidate in [next_1, next_2]:
                    cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                    if re.search(r'[A-Za-z]{2,}', cand_stripped):
                        continue
                    c_num = _extract_number(cand_stripped)
                    if c_num is not None:
                        values["ROMA"] = c_num
                        evidence["ROMA"] = f"{line} -> [{candidate}] (giá trị: {c_num})"
                        found = True; break
                if not found:
                    for candidate in [prev_1, prev_2, prev_3]:
                        cand_stripped = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if re.search(r'[A-Za-z]{2,}', cand_stripped):
                            continue
                        c_num = _extract_number(cand_stripped)
                        if c_num is not None:
                            values["ROMA"] = c_num
                            evidence["ROMA"] = f"{line} <- [{candidate}] (giá trị: {c_num}, layout đảo cột)"
                            break

        # Beta hCG — Hỗ trợ cả 2 layout: label-trước-value và value-trước-label
        if re.search(r'\b(?:beta[\s_-]*hcg|hcg)\b', line_upper, re.IGNORECASE):
            check_text = (line_upper + " " + next_1.upper() + " " + next_2.upper())
            # Kiểm tra âm tính CHỈ khi ký hiệu < 5 nằm NGAY SAU hCG (tránh bắt nhầm range của field khác)
            am_tinh = "AM TINH" in check_text or "ÂM TÍNH" in check_text or re.search(r'<\s*5(?:[^\d]|$)', check_text)
            if am_tinh:
                values["beta_hCG"] = 5.0
                evidence["beta_hCG"] = f"{line} -> [{next_1}] (âm tính -> 5.0 mIU/mL)"
            else:
                # Ưu tiên 1: số trên cùng dòng
                after_hcg = re.sub(r'.*?(?:beta[\s_-]*hcg|hcg)[:\s]*', '', line_upper, flags=re.IGNORECASE)
                after_hcg_stripped = re.sub(r'\([^)]*\)', '', after_hcg).strip()
                c_num = _extract_number(after_hcg_stripped)
                if c_num is None:
                    # Ưu tiên 2: next lines (layout chuẩn)
                    for candidate in [next_1, next_2]:
                        cs = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if not re.search(r'[A-Za-z]{2,}', cs):
                            c_num = _extract_number(cs)
                            if c_num is not None: break
                if c_num is None:
                    # Ưu tiên 3: prev lines (layout đảo cột — Case 02, quét tới prev_3)
                    for candidate in [prev_1, prev_2, prev_3]:
                        cs = re.sub(r'\([^)]*\)', '', candidate).strip()
                        if re.search(r'[A-Za-z]{2,}', cs):
                            continue
                        c_num = _extract_number(cs)
                        if c_num is not None: break
                if c_num is not None and c_num > 0:
                    values["beta_hCG"] = c_num
                    evidence["beta_hCG"] = f"{line} (giá trị: {c_num})"

    return values, evidence


def _extract_lesion_dimensions(lines: List[str]) -> Tuple[float, str]:
    """
    Trích xuất kích thước lớn nhất của KHỐI U BUỒNG TRỨNG theo ngữ cảnh.
    Loại trừ tuyệt đối kích thước của Tử cung, Nội mạc tử cung, Màng phổi, Thận.
    Kháng lỗi OCR mất ký tự 'x' (vd '185  108 x 165 mm').
    """
    excluded_keywords = ["tử cung", "tu cung", "nội mạc", "noi mac", "màng phổi", "mang phoi", "thận", "than", "lách", "gan", "ngả trước", "nga truoc", "ngả sau", "nga sau"]
    # Thêm: "bt trái", "bt phải" để bắt kích thước theo context buồng trứng trong phiếu siêu âm
    target_keywords = ["u buồng trứng", "u buong trung", "khối u", "khoi u", "tổn thương", "ton thuong", "u đặc", "u dac", "khối echo", "khoi echo", "hạ vị", "ha vi", "u quái", "u yolksac", "u bi", "phần phụ", "phan phu", "bt trái", "bt trai", "bt phải", "bt phai", "buồng trứng", "buong trung", "echo hỗn hợp", "echo hon hop"]

    candidates = []

    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Tạo ngữ cảnh rộng 3 dòng xung quanh
        context = line_lower
        if i > 0:
            context = lines[i-1].lower() + " " + context
        if i > 1:
            context = lines[i-2].lower() + " " + context
        if i + 1 < len(lines):
            context = context + " " + lines[i+1].lower()
        if i + 2 < len(lines):
            context = context + " " + lines[i+2].lower()

        # Kiểm tra xem ngữ cảnh có phải là Tử cung / Nội mạc / Màng phổi không
        is_in_uterus_or_organ_section = any(ex in context for ex in excluded_keywords) and not any(tk in context for tk in target_keywords)
        if is_in_uterus_or_organ_section:
            continue

        # Tìm các mẫu kích thước: 185x108x165 mm, 185 108 x 165, 20x25x20cm, d # 15 cm
        # 1. Tìm dãy 2 hoặc 3 số đo liên tiếp (chấp nhận dấu x, *, khoảng trắng làm phân cách)
        dim_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:[xX*]|\s+)\s*(\d+(?:\.\d+)?)(?:\s*(?:[xX*]|\s+)\s*(\d+(?:\.\d+)?))?\s*(mm|cm)?', line)
        for d_match in dim_matches:
            unit = d_match[3].lower() if d_match[3] else "mm"
            multiplier = 10.0 if unit == "cm" else 1.0
            
            n1 = float(d_match[0]) * multiplier
            n2 = float(d_match[1]) * multiplier
            if n1 > 300 or n2 > 300: # Lọc số năm hoặc mã số
                continue
            dims = [n1, n2]
            if d_match[2]:
                n3 = float(d_match[2]) * multiplier
                if n3 <= 300:
                    dims.append(n3)
            
            max_val = max(dims)
            has_target = any(tk in context for tk in target_keywords)
            if has_target:
                candidates.append((max_val, line, True))

        # 2. Mẫu đường kính đơn (vd: "d # 15 cm" hoặc "kt # 80 mm")
        single_match = re.findall(r'(?:d\s*#|kt\s*#?|đường kính\s*#?)\s*(\d+(?:\.\d+)?)\s*(mm|cm)', line_lower)
        for s_match in single_match:
            unit = s_match[1]
            multiplier = 10.0 if unit == "cm" else 1.0
            val = float(s_match[0]) * multiplier
            if val > 300:
                # Xử lý trường hợp OCR dính 2 số 2 chữ số (vd '4130mm' -> 41 và 30)
                if len(s_match[0]) == 4 and s_match[0].isdigit():
                    v1 = float(s_match[0][:2]) * multiplier
                    v2 = float(s_match[0][2:]) * multiplier
                    val = max(v1, v2)
                else:
                    continue
            candidates.append((val, line, True))

    if candidates:
        best = max(candidates, key=lambda x: x[0])
        return best[0], f"Kích thước khối u: {best[0]} mm (từ dòng: '{best[1]}')"

    return None, "Không tìm thấy kích thước khối u (None)"


# ─────────────────────────────────────────────────────────────────────────────
# 2. PARSER PHIẾU SIÊU ÂM (ULTRASOUND / IOTA)
# ─────────────────────────────────────────────────────────────────────────────
def parse_sa_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất 14 biến siêu âm IOTA với bộ từ điển thuật ngữ mở rộng và không hardcode."""
    values = {
        "lesion_max_diameter_mm": None,
        "solid_max_diameter_mm": None,
        "papillary_count": None,
        "more_than_10_locules": None,
        "acoustic_shadow": None,
        "ascites": None,
        "doppler_score": None,
        "morphology_class": None,
        "laterality": None,
        "solid_component_present": None,
        "multilocular": None,
        "irregular_wall_or_septa": None,
        "vascularity_description": None,
        "iota_adnex_available": None,
    }
    evidence = {}
    full_text = " ".join(lines).lower()

    # Kích thước khối u theo ngữ cảnh
    size_val, size_ev = _extract_lesion_dimensions(lines)
    if size_val is not None:
        values["lesion_max_diameter_mm"] = size_val
        evidence["lesion_max_diameter_mm"] = size_ev

    # Dạng đặc / u đặc (Kháng lỗi dính chữ OCR: 'udac', 'echohonhop', 'dangdac')
    for l in lines:
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        if any(term in l_lower for term in ["u dac", "u đặc", "echo hon hop", "echo hỗn hợp", "dạng đặc", "dang dac", "mo dac", "mô đặc"]) or \
           any(term in l_nospace for term in ["udac", "uđặc", "echohonhop", "dangdac", "dạngđặc", "modac", "môđặc"]):
            if not _is_negated(l_lower):
                values["solid_component_present"] = 1
                evidence["solid_component_present"] = f"Phát hiện thành phần đặc: '{l}'"
                values["morphology_class"] = 5  # U đặc
                evidence["morphology_class"] = f"Hình thái tổn thương dạng u đặc (Class 5): '{l}'"
                # Chỉ gán solid_max = lesion_max khi u đặc hoàn toàn (Class 5)
                # Không gán nếu đây chỉ là một phần nhỏ trong u nang
                if values["lesion_max_diameter_mm"]:
                    values["solid_max_diameter_mm"] = values["lesion_max_diameter_mm"]
                    evidence["solid_max_diameter_mm"] = f"U đặc hoàn toàn: solid_max = lesion_max = {values['solid_max_diameter_mm']} mm"
                break

    # Tìm rõ kích thước phần đặc riêng nếu có ("phan dac dk / kich thuoc X mm")
    # Pattern: "phan dac / phand ac ... dk / kich thuoc # Xmm" hoặc "dk lon nhat # Xmm"
    solid_dim_match = re.search(
        r'(?:ph[aân]\.?\s*d[aạ]c|m[oô]\.?\s*d[aạ]c|thanh phan dac)[^\d]*'
        r'(?:dk|kich\s*thuoc|kich\s*th\.\.?|d\s*#?|kt\s*#?)[^\d]*'
        r'(\d+(?:[.,]\d+)?)\s*(?:mm|cm)?',
        full_text
    )
    if solid_dim_match and values.get("solid_max_diameter_mm") is None:
        sv = float(solid_dim_match.group(1).replace(',', '.'))
        if sv <= 300:
            values["solid_max_diameter_mm"] = sv
            evidence["solid_max_diameter_mm"] = f"Kích thước phần đặc riêng biệt: {sv} mm (từ: '{solid_dim_match.group(0)}')"

    # solid_max_diameter_mm = 0 khi phiếu ghi rõ "không phần đặc"
    if values.get("solid_max_diameter_mm") is None:
        for l in lines:
            l_lower = l.lower()
            if any(neg_solid in l_lower for neg_solid in [
                "khong phan dac", "không phần đặc", "khong chi", "khong choi",
                "khng chi", "khong phan dac", "kh6ng phan dac"
            ]) and not any(pos in l_lower for pos in ["co phan dac", "có phần đặc"]):
                values["solid_max_diameter_mm"] = 0.0
                values["solid_component_present"] = values.get("solid_component_present") or 0
                evidence["solid_max_diameter_mm"] = f"Phiếu ghi không phần đặc: solid_max = 0 (từ: '{l}')"
                break

    # Doppler / Mạch máu — Chiến lược 2 tầng:
    # Tầng 1 (Ưu tiên): "tăng sinh mạch máu mức độ X" — kháng lỗi OCR ä/ö (PaddleOCR hay dùng umlaut)
    # Tầng 2 (fallback): pattern rộng — chỉ dùng nếu tầng 1 không tìm được
    doppler_score_found = False

    # Tầng 1: Tìm pattern đầy đủ "tăng sinh mạch máu mc/mức/mưc dö/độ/do X"
    # Bao gồm biến thể OCR: ä=a, ö=o, mc=mức, dö=độ
    doppler_specific = re.search(
        r't[aäă]ng\s*sinh\s*m[aä]ch\s*m[aä]u[^0-9]{0,25}(?:mc|m[uúüứ]c)[^0-9]{0,10}d[oöôộ][^0-9]{0,5}(\d)',
        full_text
    )
    if doppler_specific:
        score_digit = int(doppler_specific.group(1))
        values["doppler_score"] = score_digit
        values["vascularity_description"] = f"mức độ {score_digit}"
        evidence["doppler_score"] = f"Tăng sinh mạch máu (tầng 1): {doppler_specific.group(0)}"
        evidence["vascularity_description"] = f"Mô tả mạch máu: mức độ {score_digit}"
        doppler_score_found = True

    if not doppler_score_found:
        # Tầng 2: Pattern rộng hơn (fallback) — nhưng bắt buộc lọc bỏ số 0 nếu context
        # có "không" trước đó (tránh bắt “không tăng sinh mạch máu ... 0 Tử CUNG”)
        doppler_match = re.search(
            r'(?:doppler|m[aä]ch\s*m[aä]u|m[uúüû]c\s*d[oôộö])[^\d]*(\d)',
            full_text
        )
        if doppler_match:
            score_digit = int(doppler_match.group(1))
            # Loại bỏ kết quả 0 nếu vị trí match gần cụm phủ định
            match_start = doppler_match.start()
            context_before = full_text[max(0, match_start-40):match_start]
            if score_digit == 0 and any(neg in context_before for neg in ["không", "khong", "khöng", "khừng"]):
                pass  # bỏ qua, đây là "không tăng sinh" bị bắt nhầm
            else:
                values["doppler_score"] = score_digit
                values["vascularity_description"] = f"mức độ {score_digit}"
                evidence["doppler_score"] = f"Mức độ tưới máu (fallback): {doppler_match.group(0)}"
                evidence["vascularity_description"] = f"Mô tả mạch máu: mức độ {score_digit}"

    # Morphology class + solid_component_present — thêm pattern OCR biến thể
    # Ví dụ: "ACBUONG TRUNG(T)", "U DAC BUONG TRUNG", "UDACBUONGTRUNG"
    if values.get("morphology_class") is None:
        for l in lines:
            l_upper = l.upper()
            l_nospace = l_upper.replace(" ", "")
            if any(term in l_upper for term in ["U DAC BUONG TRUNG", "U ĐẶC BUỒNG TRỨNG",
                                                "AC BUONG TRUNG", "ÁC BUỒNG TRỨNG"]) or \
               any(term in l_nospace for term in ["UDACBUONGTRUNG", "ACBUONGTRUNG",
                                                  "UĐẶCBUỒNGTRỨNG", "ÁCBUỒNGTRỨNG"]):
                values["morphology_class"] = 5
                evidence["morphology_class"] = f"Kết luận siêu âm: u đặc buồng trứng (Class 5): '{l}'"
                values["solid_component_present"] = 1
                if values.get("lesion_max_diameter_mm"):
                    values["solid_max_diameter_mm"] = values["lesion_max_diameter_mm"]
                    evidence["solid_max_diameter_mm"] = f"Khối u đặc: khích thước theo u max {values['lesion_max_diameter_mm']} mm"
                break

    # Bóng lưng (Acoustic shadow) — Hỗ trợ cả 'bóng lưng' và biến thể OCR 'bóng lung'
    for l in lines:
        l_lower = l.lower()
        if any(nw in l_lower for nw in ["không quan sát rõ bóng lưng", "khong quan sat ro bong lung", "không thấy bóng lưng", "khong thay bong lung", "không có bóng lưng", "khong co bong lung", "không bóng lưng", "khong bong lung", "không quan sát rõ bóng lung"]):
            values["acoustic_shadow"] = 0
            evidence["acoustic_shadow"] = f"Không quan sát thấy bóng lưng: '{l}'"
            break
        elif any(pw in l_lower for pw in ["có bóng lưng", "co bong lung", "có bóng lung", "co bong lung", "có sọc bóng lưng", "co soc bong lung", "soc bong lung"]):
            values["acoustic_shadow"] = 1
            evidence["acoustic_shadow"] = f"Có bóng lưng: '{l}'"
            break

    # Dịch ổ bụng / Dịch cùng đồ (Douglas) - LOẠI TRỪ TUYỆT ĐỐI MÀNG PHỔI
    for l in lines:
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        if any(ex in l_lower for ex in ["màng phổi", "mang phoi", "khoang ngực", "lồng ngực", "pleural"]):
            continue
        if any(term in l_lower for term in ["dich cung do", "dịch cùng đồ", "dich o bung", "dịch ổ bụng", "douglas", "khoang gan - than", "gan - than", "hố chậu", "ho chau"]) or \
           any(term in l_nospace for term in ["dichcungdo", "dichobung", "dịchổbụng", "gan-than", "ganthan", "hochau", "hchau"]):
            if any(c_kw in l_nospace for c_kw in ["co", "có", "c6", "codich", "c6dich"]) or not _is_negated(l_lower):
                values["ascites"] = 1
                evidence["ascites"] = f"Phát hiện dịch ổ bụng/cùng đồ: '{l}'"
                break
            elif "không dịch" in l_lower or "khong dich" in l_lower or "khongdich" in l_nospace:
                values["ascites"] = 0
                evidence["ascites"] = f"Không có dịch ổ bụng/cùng đồ: '{l}'"

    # Đa thùy / Nhiều ngăn (Multilocular) — dùng per-line local context để tránh phủ định tầm xa
    for i, l in enumerate(lines):
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        if any(term in l_lower for term in ["da thuy", "đa thùy", "nhieu thuy", "nhiều thùy",
                                             "da ngan", "đa ngăn", "nhieu ngan", "nhiều ngăn",
                                             "multilocular", "nhieu vach", "nhiều vách",
                                             "phan vach", "phân vách", "co vach", "có vách"]) or \
           any(term in l_nospace for term in ["dathuy", "đathùy", "nhieuthuy", "dangan",
                                              "nhieungan", "phanvach", "phânvách", "covach"]):
            # Dùng local context (không dùng full_text) để tránh phủ định tầm xa
            local_ctx = _get_local_context(lines, i)
            if _is_negated(local_ctx):
                values["multilocular"] = 0
                evidence["multilocular"] = f"Không có dấu hiệu đa thùy: '{l}'"
            else:
                values["multilocular"] = 1
                evidence["multilocular"] = f"Phát hiện tổn thương đa thùy/nhiều ngăn: '{l}'"
            break
        elif any(term in l_lower for term in ["đơn thùy", "don thuy", "1 thùy", "một thùy",
                                               "đơn ngăn", "don ngan", "unilocular"]) or \
             any(term in l_nospace for term in ["donthuy", "đơnthùy", "1thuy", "donngan"]):
            values["multilocular"] = 0
            evidence["multilocular"] = f"Tổn thương đơn thùy/1 ngăn: '{l}'"
            break

    # Số chồi nhú (papillary_count) — bình thường các phiếu ghi "không chồi" hoặc "không chi"
    # Pattern từ Catalog: 'khng choi', 'khong chi', 'khong choi', 'khng chi'
    papillary_found = False
    for i, l in enumerate(lines):
        l_lower = l.lower()
        # Dấu hiệu CÓ chồi nhú
        if any(term in l_lower for term in [
            "choi nhu", "chồi nhú", "có chồi", "co choi",
            "papillary", "c6 choi", "c6choi"
        ]):
            # Đếm số chồi nếu có (0-4)
            count_match = re.search(r'(\d)\s*ch[oồ]i', l_lower)
            if count_match:
                cnt = int(count_match.group(1))
                values["papillary_count"] = min(cnt, 4)
            else:
                values["papillary_count"] = 1  # Có chồi nhưng không rõ số lượng
            evidence["papillary_count"] = f"Có chồi nhú: '{l}'"
            papillary_found = True
            break
        # Dấu hiệu KHÔNG có chồi nhú (các dạng OCR từ Catalog)
        if any(term in l_lower for term in [
            "khong choi", "không chồi", "khong chi", "không chị",
            "khng choi", "khng chi", "khong c6i", "khong c6 choi",
            "khong c6 chi", "kh6ng choi", "kh6ng chi",
            "co vach", "> 10 vach", ">10vach"  # phiếu ghi "> 10 vách, không chồi" trong 1 dòng
        ]):
            # Kiểm tra không bị override bởi dấu hiệu có chồi khác
            if "co choi" not in l_lower and "có chồi" not in l_lower:
                values["papillary_count"] = 0
                evidence["papillary_count"] = f"Không có chồi nhú: '{l}'"
                papillary_found = True
                break

    # Trên 10 thùy (more_than_10_locules) — pattern từ Catalog
    # `vach > 10 vach` hoặc `> 10 vach` hoặc `co vach>10vach` — khởi phát bởi dấu >
    locules_found = False
    for l in lines:
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        # Có > 10 vách: các biến thể trong Catalog
        if re.search(r'>\s*10\s*(v[aâ]ch|vach|th[uùy]{1,2}|thuy)', l_nospace) or \
           any(term in l_lower for term in ["> 10 vach", ">10 vach", "hon 10 vach", "nhieu hon 10"]):
            values["more_than_10_locules"] = 1
            evidence["more_than_10_locules"] = f"Trên 10 vách/thùy: '{l}'"
            locules_found = True
            break
        # Ít hơn 10 vách: các phiếu ghi rõ "< 10 vách" hoặc "(10 vách)"
        if re.search(r'<\s*10\s*(v[aâ]ch|vach)', l_nospace) or \
           re.search(r'\(\s*10\s*v[aâ]ch\s*\)', l_lower):
            values["more_than_10_locules"] = 0
            evidence["more_than_10_locules"] = f"Dưới hoặc đúng 10 vách: '{l}'"
            locules_found = True
            break


    # Thành / Vách không đều (Irregular wall or septa)
    for l in lines:
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        if any(term in l_lower for term in ["thành không đều", "thanh khong deu", "vách không đều", "vach khong deu", "bờ không đều", "bo khong deu", "bờ đa cung", "bo da cung", "da cung", "đa cung", "gồ ghề", "go ghe", "không đồng nhất", "khong dong nhat"]) or \
           any(term in l_nospace for term in ["thanhkhongdeu", "vachkhongdeu", "bokhongdeu", "bodacung", "dacung", "goghe", "khongdongnhat"]):
            values["irregular_wall_or_septa"] = 1
            evidence["irregular_wall_or_septa"] = f"Phát hiện thành/vách/bờ không đều (bờ đa cung): '{l}'"
            break
    if values["irregular_wall_or_septa"] is None:
        for l in lines:
            l_lower = l.lower()
            l_nospace = l_lower.replace(" ", "")
            if any(term in l_lower for term in ["thành đều", "thanh deu", "vách đều", "vach deu", "bờ đều", "bo deu"]) or \
               any(term in l_nospace for term in ["thanhdeu", "vachdeu", "bodeu"]):
                values["irregular_wall_or_septa"] = 0
                evidence["irregular_wall_or_septa"] = f"Thành/vách/bờ đều: '{l}'"
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

    # Kích thước khối u / phần đặc theo ngữ cảnh MRI
    # 1. Bóc tách riêng kích thước phần đặc (vd: "mô đặc kt </= 137 x 64 mm" hoặc "cau trüc m dac kt</=(62x88x68)mm")
    # Kháng lỗi OCR: "m dac" (rớt chữ o), "cau trüc" (ü), dấu </=, <=, #, ( trước kích thước; Hỗ trợ cả 3 chiều
    solid_matches = re.findall(
        r'(?:m[oô]?\s*d[aạ]c|ph[aầ]n\s*d[aạ]c|c[aâ]u\s*tr[uúü]c)[^\d]*kt[^\d\w]*\(?(\d+(?:\.\d+)?)\s*(?:[xX*]|\s+)\s*(\d+(?:\.\d+)?)(?:\s*(?:[xX*]|\s+)\s*(\d+(?:\.\d+)?))?',
        full_text, re.IGNORECASE
    )
    if solid_matches:
        all_dims = []
        for sm in solid_matches:
            for val_str in sm:
                if val_str:
                    v = float(val_str)
                    if v <= 300:
                        all_dims.append(v)
        if all_dims:
            values["solid_max_diameter_mm"] = max(all_dims)
            evidence["solid_max_diameter_mm"] = f"Kích thước phần đặc MRI: {values['solid_max_diameter_mm']} mm"
    if values["solid_max_diameter_mm"] is None:
        size_val, size_ev = _extract_lesion_dimensions(lines)
        if size_val is not None:
            values["solid_max_diameter_mm"] = size_val
            evidence["solid_max_diameter_mm"] = size_ev

    # O-RADS MRI Score (1..5 -> mapped index 0..4)
    # Kháng lỗi OCR: "ORADS 4", "O-RADS 4", "O RADS4", "orads.4", "p-rad2"
    orads_match = re.search(r'o[\s_.-]*rads\s*(?:mri)?\s*[:\s#.]?\s*(\d)', full_text)
    if orads_match:
        score = int(orads_match.group(1))
        values["o_rads_mri"] = max(0, score - 1)
        evidence["o_rads_mri"] = f"Phát hiện O-RADS MRI {score} (mapped={values['o_rads_mri']})"

    # TIC (Đường cong ngấm thuốc Type 1=0, Type 2=1, Type 3=2)
    # FIX: Không dùng pattern rưỚng 'type\s*\d' trên full_text vì bắt nhầm 'Type A' của IOTA ADNEX
    # Phải có anchor: dòng chứa 'bat thuoc' / 'duong cong' / 'TIC' / 'ngam thuoc' / 'type'
    for i, l in enumerate(lines):
        l_lower = l.lower()
        # Chỉ tìm TIC khi dòng có liên quan đến bắt thuốc MRI
        if any(anchor in l_lower for anchor in [
            "bat thuoc", "bắt thuốc", "duong cong", "đường cong",
            "ngam thuoc", "ngấm thuốc", "tic", "tuong phan", "tương phản"
        ]):
            tic_match = re.search(r'type\s*([123])', l_lower)
            if tic_match:
                type_num = int(tic_match.group(1))
                values["TIC"] = max(0, type_num - 1)
                evidence["TIC"] = f"Đường cong ngấm thuốc Type {type_num} (mapped={values['TIC']}) từ dòng: '{l}'"
                break

    # Giới hạn khuếch tán (Restricted diffusion / DWI - ADC)
    # FIX: Dùng per-line local context — không dùng full_text (tránh phủ định tầm xa)
    for i, l in enumerate(lines):
        l_lower = l.lower()
        if any(term in l_lower for term in [
            "gioi han khuech tan", "giới hạn khuếch tán",
            "han che khuech tan", "hạn chế khuếch tán",
            "sang tren dwi", "sáng trên dwi",
            "khuech tan", "khuếch tán"
        ]):
            local_ctx = _get_local_context(lines, i)
            if _is_negated(local_ctx):
                values["restricted_diffusion"] = 0
                evidence["restricted_diffusion"] = f"Không hạn chế khuếch tán (0): '{l}'"
            else:
                values["restricted_diffusion"] = 1
                evidence["restricted_diffusion"] = f"Hạn chế khuếch tán DWI/ADC (1): '{l}'"
            break
    # Fallback: ghi nhận DWI chỉ liệt kê chuỗi xung kỹ thuật (không phải kết quả) -> None

    # Phân vách / Vách dày (Thick septa)
    # FIX: Dùng per-line local context — tránh 'vách chẫu trái' (tải trọng chậu) bị nhào vào thick_septa
    for i, l in enumerate(lines):
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        # Từ khóa specifically cho vách nội u (không phải vách chẫu ngoại khoa)
        if any(term in l_lower for term in [
            "vach day", "vách dày", "phan vach", "phân vách",
            "vach chia", "vách chia", "6 vach", "septa",
            "vach khong deu", "vách không đều"
        ]) and not any(excl in l_lower for excl in [
            "vach chau", "vách chẫu", "vach bung", "vach nguc"
        ]):
            local_ctx = _get_local_context(lines, i)
            if _is_negated(local_ctx):
                values["thick_septa"] = 0
                evidence["thick_septa"] = f"Không có phân vách/vách dày (0): '{l}'"
            else:
                values["thick_septa"] = 1
                evidence["thick_septa"] = f"Có phân vách/vách dày trong u (1): '{l}'"
            break

    # Dịch ổ bụng trên MRI (Ascites MRI) — kháng lỗi OCR: "dich tu' do", "o bung"
    # FIX: chỉ dùng per-line (không dùng full_text fallback) để tránh phủ định tầm xa

    # Thành phần đặc (solid_component) & Hình thái MRI — per-line context
    for i, l in enumerate(lines):
        l_lower = l.lower()
        if any(term in l_lower for term in [
            "dang dac", "dạng đặc", "mo dac", "mô đặc", "m dac",
            "bat thuoc", "bắt thuốc"
        ]):
            local_ctx = _get_local_context(lines, i)
            if not _is_negated(local_ctx):
                values["solid_component"] = 1
                evidence["solid_component"] = f"Mô đặc ngấm thuốc trên MRI (1): '{l}'"
                if any(t in l_lower for t in ["dang dac va nang", "dạng đặc và nang", "nang va dac", "hon hop"]):
                    if values.get("morphology_class_mri") is None:
                        values["morphology_class_mri"] = 4
                        evidence["morphology_class_mri"] = "Hình thái MRI: Đa thùy + mô đặc (Class 4)"
                elif any(t in l_lower for t in ["dang dac", "dạng đặc"]) and values.get("morphology_class_mri") is None:
                    values["morphology_class_mri"] = 5
                    evidence["morphology_class_mri"] = "Hình thái MRI: U đặc (Class 5)"
                break

    # Morphology class MRI từ kết luận O-RADS nếu chưa xác định
    if values.get("morphology_class_mri") is None:
        for l in lines:
            l_upper = l.upper()
            if any(t in l_upper for t in ["O-RADS 5", "ORADS 5", "O RADS 5", "CARCINOM"]):
                values["morphology_class_mri"] = 5
                evidence["morphology_class_mri"] = f"O-RADS 5/Carcinom -> Class 5: '{l}'"
                break
            elif any(t in l_upper for t in ["O-RADS 4", "ORADS 4", "CO PHAN DAC", "CO MO DAC"]):
                values["morphology_class_mri"] = 4
                evidence["morphology_class_mri"] = f"O-RADS 4 -> Class 4: '{l}'"
                break
            elif any(t in l_upper for t in ["O-RADS 3", "ORADS 3"]):
                values["morphology_class_mri"] = 3
                evidence["morphology_class_mri"] = f"O-RADS 3 -> Class 3: '{l}'"
                break

    # Dịch tự do MRI (Ascites MRI) - LOẠI TRỪ TUYỆT ĐỐI MÀNG PHỔI, per-line context
    for l in lines:
        l_lower = l.lower()
        l_nospace = l_lower.replace(" ", "")
        if any(ex in l_lower for ex in ["màng phổi", "mang phoi", "khoang ngực", "lồng ngực", "pleural"]):
            continue
        if any(term in l_lower for term in ["dich tu do", "dịch tự do", "dich o bung", "dịch ổ bụng",
                                            "dich cung do", "dịch cùng đồ", "co dich", "có dịch"]) or \
           any(term in l_nospace for term in ["dichtuudo", "dichobung", "dịchtựdo", "codich"]):
            if not _is_negated(l_lower):
                values["ascites_mri"] = 1
                evidence["ascites_mri"] = f"Dịch tự do ổ bụng trên MRI: '{l}'"
                break
            else:
                values["ascites_mri"] = 0
                evidence["ascites_mri"] = f"Không có dịch tự do ổ bụng trên MRI: '{l}'"

    return values, evidence



def parse_ba_lines(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Trích xuất tuổi, tiền sử, mãn kinh từ hồ sơ bệnh án (Không hardcode default 0/0/0/1)."""
    values = {
        "age": None,
        "menopause": None,
        "pregnancy_status": None,
        "bilateral_lesion": None,
        "months_detection_to_surgery": None,
        "prior_ovarian_surgery": None,
        "other_cancer_history": None,
        "other_cancer_primary_site": None,
        "oncology_center_flag": None,
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
            values["age"] = datetime.now().year - byear
            evidence["age"] = f"Năm sinh {byear} -> Tuổi {values['age']}"
            break

    # Tình trạng Mãn kinh / Độc thân
    if any(term in full_text for term in ["doc than", "độc thân", "hoc sinh", "học sinh", "chưa lập gia đình", "chua lap gia dinh"]):
        values["menopause"] = 0
        evidence["menopause"] = "Độc thân / Học sinh -> Tiền mãn kinh (0)"
        values["pregnancy_status"] = 0
        evidence["pregnancy_status"] = "Độc thân / Học sinh -> Không mang thai (0)"
    elif "mãn kinh" in full_text or "man kinh" in full_text:
        # Kiểm tra phủ định CHỈ trong ngữ cảnh cụm "mãn kinh", không xét toàn bộ full_text
        # Vì full_text có "Tiền căn nội khoa: Không" làm _is_negated() trả True sai
        man_kinh_match = re.search(r'(.{0,30}(?:mãn kinh|man kinh).{0,30})', full_text)
        local_ctx = man_kinh_match.group(1) if man_kinh_match else full_text
        if _is_negated(local_ctx):
            values["menopause"] = 0
            evidence["menopause"] = "Chưa mãn kinh (0)"
        else:
            values["menopause"] = 1
            evidence["menopause"] = "Ghi nhận tình trạng đã mãn kinh (1)"

    # Suy luận pregnancy_status từ PARA (PARA: 0000 -> chưa mang thai)
    para_match = re.search(r'\bpara[:\s]*(\d+)', full_text, re.IGNORECASE)
    if para_match and values["pregnancy_status"] is None:
        para_val = int(para_match.group(1))
        values["pregnancy_status"] = 0 if para_val == 0 else None
        if values["pregnancy_status"] == 0:
            evidence["pregnancy_status"] = f"PARA: {para_val} -> Không mang thai hiện tại (0)"

    # Thời gian phát hiện bệnh -> phẫu thuật (months_detection_to_surgery)
    # Ưu tiên 1: X tháng rõ ràng
    month_match = re.search(
        r'(?:đau\s*bụng|phát\s*hiện|triệu\s*chứng|dau\s*bung|phat\s*hien|benh|bệnh|khai|thấy|thay)'
        r'[^\d]*(\d+(?:\.\d+)?)\s*(?:th[aáâ\W\w]{1,2}ng|thang|tháng|thng)',
        full_text
    )
    if month_match:
        values["months_detection_to_surgery"] = float(month_match.group(1))
        evidence["months_detection_to_surgery"] = f"Thời gian phát hiện: {values['months_detection_to_surgery']} tháng (từ: '{month_match.group(0)}')"
    else:
        # Ưu tiên 2: X năm (bân hào chỉnh theo dõi) -> X * 12 tháng
        year_match = re.search(
            r'(?:đau\s*bụng|phát\s*hiện|theo\s*dõi|theo\s*doi|theo doi|u\s*buồng|u buong|khai|biết)'
            r'[^\d]*(\d+(?:\.\d+)?)\s*n[aă]m',
            full_text
        )
        if year_match:
            years = float(year_match.group(1))
            values["months_detection_to_surgery"] = round(years * 12, 1)
            evidence["months_detection_to_surgery"] = f"Phát hiện {years} năm -> {values['months_detection_to_surgery']} tháng (từ: '{year_match.group(0)}')"
        else:
            # Ưu tiên 3: X ngày -> X / 30 tháng
            day_match = re.search(
                r'(?:nhập viện|nhap vien|nhập|cách|cach)\s*(?:\d+\s*)?ngày|'
                r'cách\s*nhập\s*viện\s*(\d+)\s*ngày|'
                r'cach\s*nhap\s*vien\s*(\d+)\s*ngay',
                full_text
            )
            if day_match:
                # Lấy số ngày nếu có (nhóm 1 hoặc nhóm 2)
                days_str = day_match.group(1) or day_match.group(2)
                if days_str:
                    days = float(days_str)
                    values["months_detection_to_surgery"] = round(days / 30, 2)
                    evidence["months_detection_to_surgery"] = f"Cách nhập viện {days} ngày -> {values['months_detection_to_surgery']} tháng"
                else:
                    values["months_detection_to_surgery"] = round(1 / 30, 2)
                    evidence["months_detection_to_surgery"] = f"Cách nhập viện 1 ngày -> {values['months_detection_to_surgery']} tháng"

    # Tổn thương 2 bên (Bilateral lesion)
    if ("buồng trứng (p)" in full_text or "buong trung (p)" in full_text or "bt (p)" in full_text or "phải" in full_text) and ("buồng trứng (t)" in full_text or "buong trung (t)" in full_text or "bt (t)" in full_text or "trái" in full_text):
        if any(term in full_text for term in ["u bi buong", "u buong trung", "2 ben", "hai ben", "2pp"]):
            values["bilateral_lesion"] = 1
            evidence["bilateral_lesion"] = "Phát hiện u/tổn thương cả 2 bên buồng trứng (1)"

    # Tiền sử phẫu thuật buồng trứng (prior_ovarian_surgery: ordinal 0..3)
    # QUAN TRỌNG: Phân biệt mổ lấy thai (MLT) vs mổ u buồng trứng
    # Mẫu mở rộng: "Tiền căn ngoại khoa: Không", "Ngoại khoa: Chưa ghi nhận", "Chưa phẫu thuật"
    # Loại trừ pattern mổ lấy thai: PARA:2002 với "lay thai"/"MLT"/"vet mo cu" KHÔNG được tính là mổ u BT
    has_mlt = any(term in full_text for term in [
        "lay thai", "lấy thai", "mlt", "vet mo cu", "vết mổ cũ",
        "cs mo", "cs mổ", "cổ mổ", "mo cu", "mổ cũ"
    ])
    surg_match = re.search(
        r'(?:tiền căn ngoại khoa|tien can ngoai khoa|ngoại khoa|ngoai khoa'
        r'|tiền căn phẫu thuật|phẫu thuật u|mổ u buồng trứng|tiền sử ngoại khoa'
        r'|tien can ni khoa|ngoại khoa)'
        r'[^\w\n]*(?:không|khong|khong|chưa|chua|bình thường|binh thuong)',
        full_text, re.IGNORECASE
    )
    if surg_match:
        values["prior_ovarian_surgery"] = 0
        evidence["prior_ovarian_surgery"] = f"Tiền căn ngoại khoa: Không tiền sử phẫu thuật u BT (0) (từ: '{surg_match.group(0)}')"
    elif has_mlt:
        # Riêng trường hợp chỉ có MLT mà không có gì có liên quan tới u buồng trứng:
        values["prior_ovarian_surgery"] = 0
        evidence["prior_ovarian_surgery"] = "Tiền căn phẫu thuật chỉ có mổ lấy thai (MLT) — KHÔNG có mổ u buồng trứng (0)"
    elif any(term in full_text for term in ["chưa ghi nhận", "chua ghi nhan", "chưa phẫu thuật", "chua phau thuat"]) and any(k in full_text for k in ["tiền căn", "tien can", "tiền sử", "tien su"]):
        values["prior_ovarian_surgery"] = 0
        evidence["prior_ovarian_surgery"] = "Tiền căn: Chưa ghi nhận phẫu thuật trước đó (0)"

    # Tiền sử ung thư khác (other_cancer_history: binary 0/1)
    # Mẫu mở rộng: "Tiền căn nội khoa: Không", "Nội khoa: [x] Không", "Nội khoa: Chưa ghi nhận"
    # Kháng lỗi: Format checkbox "[x] Không" hoặc dấu cách trước ":" -> dùng \W+ thay vì [^\w\n]
    cancer_match = re.search(
        r'(?:tiền căn nội khoa|tien can noi khoa|nội khoa|noi khoa|ung thư khác|ung thu khac|bệnh lý ác tính|tiền sử nội khoa)[^\w\n]*(?:không|khong|chưa|chua|bình thường|binh thuong)',
        full_text, re.IGNORECASE
    )
    if cancer_match:
        values["other_cancer_history"] = 0
        evidence["other_cancer_history"] = f"Tiền căn nội khoa: Không tiền sử ung thư khác (0) (từ: '{cancer_match.group(0)}')"
    elif any(term in full_text for term in ["không ung thư", "khong ung thu", "chưa ghi nhận tiền sử ung thư"]) and any(k in full_text for k in ["tiền căn", "tien can", "tiền sử", "tien su"]):
        values["other_cancer_history"] = 0
        evidence["other_cancer_history"] = "Tiền căn: Chưa ghi nhận tiền sử ung thư khác (0)"

    # Trung tâm ung bướu / BV chuyên khoa phụ sản (Kháng lỗi dính chữ OCR)
    full_nospace = full_text.replace(" ", "")
    if any(term in full_text for term in ["từ dũ", "tu du", "ung bướu", "ung buou", "hùng vương", "hung vuong"]) or \
       any(term in full_nospace for term in ["benhvientudo", "benhvientudu", "tudu", "ungbuou", "hungvuong"]):
        values["oncology_center_flag"] = 1
        evidence["oncology_center_flag"] = "BV Từ Dũ / BV chuyên khoa phụ sản ung bướu (1)"

    return values, evidence


# ─────────────────────────────────────────────────────────────────────────────
# 5. PARSER GIẢI PHẪU BỆNH (GPB - GROUND TRUTH VỚI NEGATION CHECK)
# ─────────────────────────────────────────────────────────────────────────────
def parse_gpb_lines(lines: List[str]) -> Tuple[int, str]:
    """Trích xuất nhãn ung thư GPB - CHỈ đọc từ phần KẾT LUẬN trở về sau.
    
    NGUYÊN TẮC AN TOÀN DỮ LIỆU (BẮT BUỘC):
    - Ground truth PHẢI lấy từ kết luận GPB sau mổ, TUYỆT ĐỐI không đọc/suy
      diễn từ 'chẩn đoán vào viện', 'lý do vào viện', hay chẩn đoán trước mổ.
    - Nếu không tìm thấy dòng KẾT LUẬN → trả về None để đánh dấu cần xác nhận
      thủ công, KHÔNG đoán từ phần văn bản khác.
    - Nhãn dự án: Cancer(1) vs Non-cancer(0). U giáp biên = 0 (non-cancer).
    """
    # Bước 1: Tìm vị trí dòng "KẾT LUẬN" trong phiếu GPB
    # Kháng lỗi OCR đa dạng: sau replace(" ","") các biến thể đều về cùng dạng
    ket_luan_idx = None
    for i, line in enumerate(lines):
        # Xóa cả khoảng trắng và tab, chuyển về upper để so sánh
        normalized = line.upper().replace(" ", "").replace("\t", "")
        # Các anchor hợp lệ sau normalize
        if any(anchor in normalized for anchor in [
            "KETLUAN",      # 'KET LUAN:' hoặc 'KETLUAN:' đều match
            "KẾTLUẬN",
            "KẾTLUAN",
            "KETLUẬN",
        ]):
            ket_luan_idx = i
            break

    if ket_luan_idx is None:
        return None, "CẢNH BÁO: Không tìm thấy dòng 'KẾT LUẬN' trong phiếu GPB. Cần bác sĩ xác nhận thủ công."

    # Bước 2: Chỉ phân tích văn bản từ dòng KẾT LUẬN trở về sau
    conclusion_lines = lines[ket_luan_idx:]
    conclusion_text = " ".join(conclusion_lines).lower()
    # Thêm bản không dấu cách để bắt chuỗi dính: "UGIAPBIENACBUONGTRUNGTRAI"
    conclusion_nospace = conclusion_text.replace(" ", "")

    # Bước 3: Từ khóa lành tính / giáp biên (nhãn dự án = 0)
    # U giáp biên (borderline) = NON-CANCER trong dự án này (cancer vs non-cancer)
    benign_keywords = [
        "lành tính", "lanh tinh",
        "nang lạc nội mạc", "nang lac noi mac",
        "u xơ", "u xo",
        "u lành", "u lanh",
        "nang hoàng thể", "nang hoang the",
        "cellularfibroma", "fibroma",
        "mature teratoma",
        "u quai truong thanh lanh",
        "u quái trưởng thành",
        "u quai truong thanh",
    ]
    benign_nospace_keywords = [
        "ugiapbien",          # u giáp biên dính chữ OCR
        "lanhtinh",
        "nanglacnoimac",
        "uquaitruongthanh",
    ]
    # Từ khóa ác tính rõ ràng trong KẾT LUẬN
    malignant_keywords = [
        "carcinoma", "carcinom", "carcinôm", "carcinam",
        "yolk sac", "yolksac", "yolk sac tumour",
        "u tế bào mầm", "u te bao mam",
        "không biệt hóa", "khong biet hoa",
        "ung thư", "ung thu",
        "immature", "chưa trưởng thành", "chua truong thanh",
        "không trưởng thành", "khong truong thanh", "khong truong",
        "do 3", "độ 3", "grade 3", "grade iii",
    ]
    # Từ khóa ác tính dạng "ac tinh" — CHỈ bắt khi KHÔNG đi kèm lành/giáp biên
    ac_tinh_present = "ac tinh" in conclusion_text or "ác tính" in conclusion_text

    has_malignant = any(kw in conclusion_text for kw in malignant_keywords) or any(kw in conclusion_nospace for kw in ["yolksac", "carcinoma", "carcinom", "carcinôm", "immature"])
    has_benign = (any(kw in conclusion_text for kw in benign_keywords) or
                  any(kw in conclusion_nospace for kw in benign_nospace_keywords))
    # "yolk sac" hoặc "immature teratoma" luôn là ác tính
    has_yolksac_or_immature = (
        "yolk sac" in conclusion_text or "yolksac" in conclusion_nospace or
        "immature" in conclusion_text or "chưa trưởng thành" in conclusion_text or
        "chua truong thanh" in conclusion_text or "khong truong thanh" in conclusion_text or
        "khong truong" in conclusion_text
    )

    # Quy tắc phân loại (thứ tự ưu tiên):
    # 1. Nếu có Yolk Sac / U quái chưa trưởng thành (Immature Teratoma) → ác tính (1)
    if has_yolksac_or_immature:
        label = 1
        evidence = f"KẾT LUẬN GPB ác tính (Yolk Sac / Immature Teratoma) (1) [dòng {ket_luan_idx}]: '{conclusion_lines[0].strip()}'"
    # 2. Nếu có ác tính rõ ràng (carcinoma, ung thư...) → ác tính (1)
    elif has_malignant or (ac_tinh_present and not has_benign):
        label = 1
        evidence = f"KẾT LUẬN GPB ác tính (1) [dòng {ket_luan_idx}]: '{conclusion_lines[0].strip()}'"
    # 3. Nếu có lành tính/giáp biên rõ ràng và KHÔNG có ác tính → lành tính (0)
    elif has_benign:
        label = 0
        evidence = f"KẾT LUẬN GPB lành tính/giáp biên (0) [dòng {ket_luan_idx}]: '{conclusion_lines[0].strip()}'"
    # 4. Không bắt được từ khóa nào
    else:
        label = None
        evidence = f"CẢNH BÁO: Không nhận dạng được từ khóa trong KẾT LUẬN GPB. Cần xác nhận thủ công: '{conclusion_lines[0].strip() if conclusion_lines else 'trống'}'"

    return label, evidence


# ─────────────────────────────────────────────────────────────────────────────
# LỚP 4: MEDICAL VALIDATION — Kiểm tra ngưỡng y khoa & chuẩn hóa kiểu dữ liệu
# ─────────────────────────────────────────────────────────────────────────────

VALID_RANGES = {
    "age":                      (1, 120),
    "CA125":                    (0, 100000),
    "HE4":                      (0, 10000),
    "AFP":                      (0, 100000),
    "beta_hCG":                 (0, 100000),
    "ROMA":                     (0, 100),
    "lesion_max_diameter_mm":   (1, 500),
    "solid_max_diameter_mm":    (0, 500),
    "doppler_score":            (1, 4),
    "papillary_count":          (0, 4),
    "morphology_class":         (1, 7),
    "TIC":                      (0, 2),
    "o_rads_mri":               (0, 4),
    "morphology_class_mri":     (1, 7),
}

BINARY_FIELDS = [
    "menopause", "pregnancy_status", "bilateral_lesion",
    "prior_ovarian_surgery",
    "other_cancer_history", "oncology_center_flag",
    "acoustic_shadow", "ascites", "more_than_10_locules",
    "solid_component_present", "multilocular", "irregular_wall_or_septa",
    "iota_adnex_available", "solid_component",
    "restricted_diffusion", "thick_septa", "ascites_mri",
]


def validate_extracted_values(
    tabular: Dict[str, Any],
    ultrasound: Dict[str, Any],
    mri: Dict[str, Any]
) -> None:
    """
    LỚP 4 MEDICAL VALIDATION:
    Kiểm tra giá trị từng trường theo miền giá trị y khoa hợp lệ.
    Nếu vượt ngưỡng bất thường hoặc sai kiểu -> chuyển về None và cảnh báo (Missing != 0).
    """
    all_dicts = [("tabular", tabular), ("ultrasound", ultrasound), ("mri", mri)]

    for mod_name, d in all_dicts:
        for field, val in list(d.items()):
            if val is None:
                continue

            # 1. Kiểm tra range số thực/nguyên
            if field in VALID_RANGES:
                min_v, max_v = VALID_RANGES[field]
                try:
                    num_v = float(val)
                    if num_v < min_v or num_v > max_v:
                        print(f"  [VALIDATION WARNING] {mod_name}.{field}={val} nằm ngoài phạm vi [{min_v}, {max_v}] -> Đặt về None")
                        d[field] = None
                except (ValueError, TypeError):
                    print(f"  [VALIDATION WARNING] {mod_name}.{field}={val} không thể ép kiểu số -> Đặt về None")
                    d[field] = None

            # 2. Kiểm tra trường nhị phân / phân loại
            elif field in BINARY_FIELDS:
                if val not in (0, 1, 0.0, 1.0, 2, 3):  # prior_ovarian_surgery can be 0..3
                    print(f"  [VALIDATION WARNING] {mod_name}.{field}={val} không phải nhị phân/hợp lệ -> Đặt về None")
                    d[field] = None


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
        "age": None, "menopause": None, "pregnancy_status": None, "bilateral_lesion": None,
        "months_detection_to_surgery": None, "prior_ovarian_surgery": None, "other_cancer_history": None,
        "other_cancer_primary_site": None, "oncology_center_flag": None,
        "CA125": None, "HE4": None, "AFP": None, "beta_hCG": None, "ROMA": None
    }
    extracted_us = {
        "lesion_max_diameter_mm": None, "solid_max_diameter_mm": None, "papillary_count": None,
        "more_than_10_locules": None, "acoustic_shadow": None, "ascites": None, "doppler_score": None,
        "morphology_class": None, "laterality": None, "solid_component_present": None,
        "multilocular": None, "irregular_wall_or_septa": None, "vascularity_description": None,
        "iota_adnex_available": None
    }
    extracted_mri = {
        "solid_component": None, "solid_max_diameter_mm": None, "TIC": None,
        "restricted_diffusion": None, "thick_septa": None, "ascites_mri": None,
        "morphology_class_mri": None, "o_rads_mri": None
    }

    gpb_label = None
    all_evidence = {}
    all_raw_lines = []

    for img_path in sorted(image_paths):
        filename = os.path.basename(img_path)
        print(f"-> Đang chạy OCR trên: {filename:20s}...", end=" ", flush=True)
        raw_lines = run_ocr_on_image(img_path)
        # LỚP 1: Chuẩn hóa text OCR trước khi phân loại và parse
        lines = normalize_ocr_text(raw_lines)
        all_raw_lines.extend(lines)
        doc_type = classify_document_type(lines, filename)
        print(f"[{doc_type.upper():10s}] Nhận diện {len(lines):2d} dòng text (đã chuẩn hóa)")

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

    # ─── CROSS-DOCUMENT CLINICAL SYNTHESIS ───
    all_case_text = " ".join(all_raw_lines).lower()
    
    # 1. Tổn thương hai bên buồng trứng (bilateral_lesion: binary 0/1)
    has_right = any(kw in all_case_text for kw in ["buong trung (p", "buồng trứng (p", "bt (p", "bt phai", "bt phải", "buồng trứng phải"]) and \
                any(tk in all_case_text for tk in ["u dac", "u đặc", "u nang", "u quai", "u quái", "u yolksac", "u bi", "u bì", "k buong", "khối echo", "ác tính"])
    has_left = any(kw in all_case_text for kw in ["buong trung (t", "buồng trứng (t", "bt (t", "bt trai", "bt trái", "buồng trứng trái"]) and \
               any(tk in all_case_text for tk in ["u dac", "u đặc", "u nang", "u quai", "u quái", "u yolksac", "u bi", "u bì", "k buong", "khối echo", "u bi"])
    has_bilateral_kw = any(bk in all_case_text for bk in ["hai bên", "hai ben", "2 bên", "2 ben", "cả 2 buồng trứng", "cả hai buồng trứng", "u 2 buồng trứng", "bilateral", "2pp"])

    if has_bilateral_kw or (has_right and has_left):
        extracted_tabular["bilateral_lesion"] = 1
        all_evidence["bilateral_lesion"] = "Phát hiện u/tổn thương ở cả hai bên buồng trứng (1)"
    elif has_right or has_left:
        if any(nk in all_case_text for nk in ["mô lành", "mo lanh", "bình thường", "binh thuong", "không bat thuong"]):
            extracted_tabular["bilateral_lesion"] = 0
            all_evidence["bilateral_lesion"] = "Tổn thương buồng trứng đơn bên (0)"

    # 2. Đánh giá tính khả dụng cho IOTA ADNEX (iota_adnex_available: binary 0/1)
    has_iota_core = (
        extracted_tabular.get("age") is not None and
        extracted_tabular.get("oncology_center_flag") is not None and
        extracted_us.get("lesion_max_diameter_mm") is not None and
        extracted_us.get("ascites") is not None and
        extracted_us.get("doppler_score") is not None
    )
    if has_iota_core:
        extracted_us["iota_adnex_available"] = 1
        all_evidence["iota_adnex_available"] = "Đầy đủ các biến cốt lõi để tính toán mô hình IOTA ADNEX (1)"
    elif extracted_us.get("lesion_max_diameter_mm") is not None:
        extracted_us["iota_adnex_available"] = 0
        all_evidence["iota_adnex_available"] = "Thiếu một số biến siêu âm/lâm sàng cốt lõi cho IOTA ADNEX (0)"

    # 3. Bổ sung O-RADS MRI từ BBHC / Hội chẩn nếu phiếu MRI bị OCR lỗi
    # Lấy điểm O-RADS cao nhất nếu có tổn thương 2 bên (ví dụ BT Phải ORADS 2, BT Trái ORADS 4)
    all_orads = re.findall(r'o[\s_.-]*rads\s*(?:mri)?\s*[:\s#.]?\s*(\d)', all_case_text)
    if all_orads:
        max_score = max(int(s) for s in all_orads if int(s) <= 5)
        extracted_mri["o_rads_mri"] = max(0, max_score - 1)
        all_evidence["o_rads_mri"] = f"Phát hiện O-RADS MRI {max_score} từ hồ sơ bệnh án (mapped={extracted_mri['o_rads_mri']})"

    # 4. Tiền căn ung thư khác từ BBHC / Bệnh án
    if extracted_tabular.get("other_cancer_history") is None:
        if any(k in all_case_text for k in ["nội khoa", "noi khoa", "tiền căn nội khoa", "tien can noi khoa"]):
            if any(neg in all_case_text for neg in ["không", "khong", "chưa ghi nhận", "chua ghi nhan"]):
                extracted_tabular["other_cancer_history"] = 0
                all_evidence["other_cancer_history"] = "Tiền căn nội khoa: Không ghi nhận tiền sử ung thư khác (0)"

    # ─── LỚP 4: MEDICAL VALIDATION ───
    validate_extracted_values(extracted_tabular, extracted_us, extracted_mri)

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

    # Xuất ra file CSV kiểm chứng có gắn kèm ngày giờ (date & time)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"results/extracted_case_{case_num:02d}_{timestamp}.csv"
    export_to_csv([final_sample], csv_path=csv_file)

    # Hiển thị tóm tắt ngắn gọn và sạch sẽ trên terminal
    gt_text = "Ác tính (1)" if gpb_label == 1 else ("Lành tính (0)" if gpb_label == 0 else "Chưa rõ")
    ca125_val = extracted_tabular.get("CA125")
    size_val = extracted_us.get("lesion_max_diameter_mm")
    orads_val = extracted_mri.get("o_rads_mri")
    
    print("\n" + "─"*70)
    print(f"✔ HOÀN TẤT CASE {case_num:02d} -> Đã lưu file: {csv_file}")
    print(f"  * GPB: {gt_text} | Tuổi: {extracted_tabular.get('age')} | CA125: {ca125_val} | U max: {size_val}mm | O-RADS MRI: {orads_val}")
    print("─"*70)

    return final_sample


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR & Parser dữ liệu phiếu y tế")
    parser.add_argument("--case", type=int, default=1, help="Số thứ tự ca bệnh cần trích xuất (1 đến 12)")
    args = parser.parse_args()

    extract_case_from_images(args.case)
