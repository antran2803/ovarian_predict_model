"""
Build 1 sample hoàn chỉnh (patient) từ raw values của từng modality.
Hàm ở đây KHÔNG hard-code dữ liệu bệnh nhân cụ thể nào - dữ liệu được
truyền vào từ bên ngoài (mock hoặc file JSON thật trong data/real).
"""

from config.schema_config import MODALITY_NAMES
from core.missing_utils import compute_feature_mask, compute_modality_available


def build_modality_block(values: dict, modality_name: str) -> dict:
    """Gói 1 modality: values + feature_mask + available."""
    feature_mask = compute_feature_mask(values, modality_name)
    available = compute_modality_available(feature_mask, modality_name)
    return {
        "values": values,
        "feature_mask": feature_mask,
        "available": available,
    }


def build_patient_sample(
    patient_id: str,
    modality_values: dict,
    ground_truth_label: int,
    ground_truth_source: str = "pathology_report",
) -> dict:
    """
    modality_values: dict {modality_name: {feature_name: value_or_None}}
    Phải có đủ key cho tất cả modality trong MODALITY_NAMES (dù value bên
    trong có thể toàn None).
    """
    sample = {"patient_id": patient_id}

    for modality in MODALITY_NAMES:
        values = modality_values.get(modality, {})
        sample[modality] = build_modality_block(values, modality)

    sample["ground_truth"] = {
        "label": ground_truth_label,
        "source": ground_truth_source,
    }
    return sample
