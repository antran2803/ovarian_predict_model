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
    """
    feature_order = MODALITY_FEATURES[modality_name]
    return [0 if values.get(f) is None else 1 for f in feature_order]


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
