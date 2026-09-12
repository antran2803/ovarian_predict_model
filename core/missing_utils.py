"""
Logic thuần xử lý missing - không phụ thuộc dữ liệu bệnh nhân cụ thể nào.
"""

from config.schema_config import MISSING_THRESHOLD, MODALITY_FEATURES


def compute_feature_mask(values: dict, modality_name: str) -> list:
    """
    values: dict {feature_name: value or None}
    Duyệt theo ĐÚNG THỨ TỰ feature định nghĩa trong config (không theo
    thứ tự key của dict truyền vào) để đảm bảo mask luôn nhất quán
    giữa các bệnh nhân, kể cả khi values thiếu key hoàn toàn.

    XỬ LÝ BIẾN ĐIỀU KIỆN (Conditional Features):
    - `other_cancer_primary_site` chỉ áp dụng khi `other_cancer_history == 1`.
      Khi `other_cancer_history == 0`, việc trường này mang giá trị None hoặc 'N/A'
      là HỢP LỆ theo cấu trúc (không phải dữ liệu bị khuyết thiếu).
      Do đó, mask của trường này khi other_cancer_history == 0 được tính là 1 (Hợp lệ / Đầy đủ).
    """
    feature_order = MODALITY_FEATURES[modality_name]
    mask = []
    for f in feature_order:
        val = values.get(f)
        if f == "other_cancer_primary_site":
            if values.get("other_cancer_history") == 0:
                mask.append(1)
            else:
                mask.append(0 if val is None else 1)
        else:
            mask.append(0 if val is None else 1)
    return mask


def compute_modality_available(feature_mask: list, modality_name: str) -> int:
    """
    missing_rate = số feature thiếu / tổng số feature
    available = 1 nếu missing_rate <= ngưỡng cho phép, ngược lại 0.
    """
    n_total = len(feature_mask)
    n_missing = feature_mask.count(0)
    missing_rate = n_missing / n_total

    threshold = MISSING_THRESHOLD[modality_name]
    return 1 if missing_rate <= threshold else 0
