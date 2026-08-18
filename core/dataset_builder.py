"""
Convert nested sample(s) -> DataFrame phẳng cho training XGBoost.
"""

import pandas as pd

from config.schema_config import MODALITY_NAMES


def flatten_sample_to_row(sample: dict) -> dict:
    row = {"patient_id": sample["patient_id"]}

    for modality in MODALITY_NAMES:
        block = sample[modality]
        for feature_name, value in block["values"].items():
            row[f"{modality}_{feature_name}"] = value
        row[f"{modality}_available"] = block["available"]

    row["label"] = sample["ground_truth"]["label"]
    row["ground_truth_source"] = sample["ground_truth"]["source"]
    return row


def build_dataframe(samples: list) -> pd.DataFrame:
    """samples: list các sample dict (output của build_patient_sample)."""
    rows = [flatten_sample_to_row(s) for s in samples]
    return pd.DataFrame(rows)
