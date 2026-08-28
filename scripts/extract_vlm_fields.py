# -*- coding: utf-8 -*-
"""
Module trích xuất dữ liệu từ ảnh y tế bằng Vision-Language Model (VLM) chạy Local.
Hỗ trợ 2 model:
1. PP-DocBee (doc_understanding pipeline qua PaddleX)
2. PaddleOCR-VL (PaddleOCR-VL-0.9B qua PaddleX)

Input: Đường dẫn file ảnh gốc (.jpg/.png) - Đọc pixel trực tiếp.
Output: JSON chuẩn có đầy đủ giá trị, trích dẫn văn bản bằng chứng (evidence) và confidence.
"""

import os
import sys
import json
import time
import re
from typing import Dict, Any, List, Optional

# Đảm bảo in tiếng Việt UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VLM_TARGET_FIELDS = [
    "solid_max_diameter_mm",
    "ascites_mri",
    "o_rads_mri",
    "solid_component",
    "morphology_class_mri"
]

PROMPT_VLM_MRI = """Đây là ảnh chụp kết quả Cộng hưởng từ (MRI) vùng chậu / buồng trứng (tiếng Việt y khoa).
Hãy quan sát kỹ toàn bộ văn bản trong ảnh và trích xuất các thông tin sau:
1. solid_max_diameter_mm: Kích thước lớn nhất của thành phần MÔ ĐẶC / PHẦN ĐẶC trong khối u buồng trứng (tính bằng mm). Chú ý: Chỉ lấy kích thước của phần mô đặc, không phải kích thước toàn bộ u nang, và tuyệt đối không lấy kích thước của u xơ tử cung.
2. ascites_mri: Tình trạng dịch tự do ổ bụng / dịch cùng đồ trên MRI. Trả về 1 nếu có dịch tự do, 0 nếu không có hoặc bình thường.
3. o_rads_mri: Điểm phân loại O-RADS MRI (số nguyên từ 1 đến 5).
4. solid_component: Khối u có thành phần mô đặc ngấm thuốc không? (1 = có, 0 = không).

Quy tắc bắt buộc:
- Mỗi trường phải trích dẫn CHÍNH XÁC đoạn văn bản gốc trong ảnh làm bằng chứng (evidence).
- Nếu không tìm thấy thông tin hoặc không có bằng chứng rõ ràng, đặt value là null và evidence là "không tìm thấy trong ảnh".
- KHÔNG ĐƯỢC tự suy diễn hay đoán nếu không có chữ trong ảnh.

Trả về kết quả dưới dạng JSON duy nhất theo cấu trúc:
{
  "solid_max_diameter_mm": {"value": <số hoặc null>, "evidence": "<đoạn text trích từ ảnh>", "confidence": "<high/medium/low>"},
  "ascites_mri": {"value": <0 hoặc 1 hoặc null>, "evidence": "<đoạn text trích từ ảnh>", "confidence": "<high/medium/low>"},
  "o_rads_mri": {"value": <1-5 hoặc null>, "evidence": "<đoạn text trích từ ảnh>", "confidence": "<high/medium/low>"},
  "solid_component": {"value": <0 hoặc 1 hoặc null>, "evidence": "<đoạn text trích từ ảnh>", "confidence": "<high/medium/low>"}
}
"""

_docbee_pipeline = None
_paddleocr_vl_pipeline = None

def get_docbee_pipeline(device: str = "cpu"):
    global _docbee_pipeline
    if _docbee_pipeline is None:
        from paddlex import create_pipeline
        print(f"[VLM:PP-DocBee] Đang khởi tạo pipeline PP-DocBee trên device='{device}'...")
        _docbee_pipeline = create_pipeline(pipeline="doc_understanding", device=device)
    return _docbee_pipeline


def get_paddleocr_vl_pipeline(device: str = "cpu"):
    global _paddleocr_vl_pipeline
    if _paddleocr_vl_pipeline is None:
        from paddlex import create_pipeline
        print(f"[VLM:PaddleOCR-VL] Đang khởi tạo pipeline PaddleOCR-VL trên device='{device}'...")
        _paddleocr_vl_pipeline = create_pipeline(pipeline="PaddleOCR-VL", device=device)
    return _paddleocr_vl_pipeline


def extract_with_pp_docbee(image_path: str, prompt: str = PROMPT_VLM_MRI, device: str = "cpu") -> Dict[str, Any]:
    """Chạy PP-DocBee trên ảnh gốc và đo thời gian inference."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

    start_time = time.perf_counter()
    pipeline = get_docbee_pipeline(device=device)

    # Input truyền ảnh pixel trực tiếp
    input_data = {"image": image_path, "query": prompt}
    output_generator = pipeline.predict(input_data)
    
    raw_response = ""
    for res in output_generator:
        if hasattr(res, "result"):
            raw_response += str(res.result)
        elif isinstance(res, dict):
            raw_response += str(res.get("result", ""))
        else:
            raw_response += str(res)

    elapsed_sec = time.perf_counter() - start_time
    parsed_json = _parse_vlm_json_output(raw_response)

    return {
        "model": "PP-DocBee",
        "image_path": image_path,
        "elapsed_seconds": round(elapsed_sec, 2),
        "raw_response": raw_response,
        "extracted_fields": parsed_json
    }


def extract_with_paddleocr_vl(image_path: str, prompt: str = PROMPT_VLM_MRI, device: str = "cpu") -> Dict[str, Any]:
    """Chạy PaddleOCR-VL trên ảnh gốc và đo thời gian inference."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

    start_time = time.perf_counter()
    pipeline = get_paddleocr_vl_pipeline(device=device)

    input_data = {"image": image_path, "query": prompt}
    output_generator = pipeline.predict(input_data)
    
    raw_response = ""
    for res in output_generator:
        if hasattr(res, "result"):
            raw_response += str(res.result)
        elif isinstance(res, dict):
            raw_response += str(res.get("result", ""))
        else:
            raw_response += str(res)

    elapsed_sec = time.perf_counter() - start_time
    parsed_json = _parse_vlm_json_output(raw_response)

    return {
        "model": "PaddleOCR-VL",
        "image_path": image_path,
        "elapsed_seconds": round(elapsed_sec, 2),
        "raw_response": raw_response,
        "extracted_fields": parsed_json
    }


def _parse_vlm_json_output(raw_text: str) -> Dict[str, Any]:
    """Trích xuất khối JSON an toàn từ phản hồi của VLM."""
    default_result = {
        "solid_max_diameter_mm": {"value": None, "evidence": "Không tìm thấy trong ảnh", "confidence": "low"},
        "ascites_mri": {"value": None, "evidence": "Không tìm thấy trong ảnh", "confidence": "low"},
        "o_rads_mri": {"value": None, "evidence": "Không tìm thấy trong ảnh", "confidence": "low"},
        "solid_component": {"value": None, "evidence": "Không tìm thấy trong ảnh", "confidence": "low"}
    }
    
    if not raw_text:
        return default_result

    # Tìm json block trong ```json ... ``` hoặc { ... }
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    json_str = json_match.group(1) if json_match else None
    
    if not json_str:
        json_match2 = re.search(r'(\{[\s\S]*"solid_max_diameter_mm"[\s\S]*\})', raw_text)
        if json_match2:
            json_str = json_match2.group(1)

    if json_str:
        try:
            parsed = json.loads(json_str)
            for k in default_result:
                if k in parsed:
                    default_result[k] = parsed[k]
            return default_result
        except Exception:
            pass

    return default_result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test VLM extraction on MRI image")
    parser.add_argument("--image", type=str, default="sample_data/1-MRI1.jpg", help="Path to image file")
    parser.add_argument("--model", type=str, choices=["docbee", "paddleocr_vl", "both"], default="both")
    parser.add_argument("--device", type=str, default="cpu", help="Device: 'cpu' or 'gpu'")
    args = parser.parse_args()

    print(f"=== KIỂM TRA VLM TRÊN ẢNH: {args.image} ===")
    if args.model in ["docbee", "both"]:
        try:
            res_docbee = extract_with_pp_docbee(args.image, device=args.device)
            print(f"\n[PP-DocBee] Thời gian: {res_docbee['elapsed_seconds']}s")
            print(json.dumps(res_docbee["extracted_fields"], ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[PP-DocBee] LỖI: {e}")

    if args.model in ["paddleocr_vl", "both"]:
        try:
            res_pvl = extract_with_paddleocr_vl(args.image, device=args.device)
            print(f"\n[PaddleOCR-VL] Thời gian: {res_pvl['elapsed_seconds']}s")
            print(json.dumps(res_pvl["extracted_fields"], ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[PaddleOCR-VL] LỖI: {e}")
