"""Filter audited real samples into modality-specific supervised datasets."""

import os
import sys
from typing import Dict, List, Tuple

import pandas as pd

sys.path.insert(0, os.path.abspath("."))

from config.schema_config import MODALITY_FEATURES, MODALITY_NAMES
from scripts.build_real_dataset import load_all_real_samples


def filter_samples_for_expert(samples: List[dict], modality_name: str) -> List[dict]:
    """Keep only labeled samples whose requested modality is available."""
    if modality_name not in MODALITY_NAMES:
        raise ValueError(
            f"modality_name='{modality_name}' không hợp lệ. "
            f"Chọn một trong: {MODALITY_NAMES}"
        )

    filtered = []
    for sample in samples:
        label = sample["ground_truth"]["label"]
        modality_available = sample[modality_name]["available"]
        if label is not None and modality_available == 1:
            filtered.append(sample)
    return filtered


def build_expert_dataset(
    samples: List[dict], modality_name: str
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Return feature matrix, labels, and patient IDs for one expert."""
    filtered = filter_samples_for_expert(samples, modality_name)
    features = MODALITY_FEATURES[modality_name]

    rows = [
        {feature: sample[modality_name]["values"].get(feature) for feature in features}
        for sample in filtered
    ]
    X = pd.DataFrame(rows, columns=features)
    y = pd.Series(
        [sample["ground_truth"]["label"] for sample in filtered],
        dtype="int64",
        name="label",
    )
    patient_ids = [sample["patient_id"] for sample in filtered]
    return X, y, patient_ids


def summarize_expert_datasets(samples: List[dict]) -> List[Dict[str, int]]:
    """Summarize eligible sample and class counts for every expert modality."""
    summary = []
    for modality_name in MODALITY_NAMES:
        filtered = filter_samples_for_expert(samples, modality_name)
        labels = [sample["ground_truth"]["label"] for sample in filtered]
        summary.append(
            {
                "expert": modality_name,
                "n_samples": len(filtered),
                "n_malignant": labels.count(1),
                "n_non_cancer": labels.count(0),
            }
        )
    return summary


def main() -> None:
    samples = load_all_real_samples()
    summary = summarize_expert_datasets(samples)

    print("REAL_EXPERT_DATASET_FILTER")
    print("Điều kiện: label != None AND modality_available == 1")
    print("expert | so ca | ac tinh | lanh tinh")
    for item in summary:
        print(
            f"{item['expert']} | {item['n_samples']} | "
            f"{item['n_malignant']} | {item['n_non_cancer']}"
        )

    used_ids = {
        modality: build_expert_dataset(samples, modality)[2]
        for modality in MODALITY_NAMES
    }
    if any("case_12" in patient_ids for patient_ids in used_ids.values()):
        raise AssertionError("Case 12 không được xuất hiện trong supervised dataset")

    print("Case 12: excluded from all supervised expert datasets")


if __name__ == "__main__":
    main()
