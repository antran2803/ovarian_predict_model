"""
Chạy: python3 scripts/build_dataset.py  (từ thư mục gốc ovarian_ai/)
Load mock samples + real case samples -> build -> in DataFrame.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sample_builder import build_patient_sample
from core.dataset_builder import build_dataframe
from data.mock.mock_samples import MOCK_PATIENTS
from data.real import case_01


def load_all_samples() -> list:
    samples = []

    # Mock samples
    for p in MOCK_PATIENTS:
        samples.append(
            build_patient_sample(
                patient_id=p["patient_id"],
                modality_values=p["modality_values"],
                ground_truth_label=p["ground_truth_label"],
                ground_truth_source=p["ground_truth_source"],
            )
        )

    # Real samples
    samples.append(
        build_patient_sample(
            patient_id=case_01.PATIENT_ID,
            modality_values=case_01.MODALITY_VALUES,
            ground_truth_label=case_01.GROUND_TRUTH_LABEL,
            ground_truth_source=case_01.GROUND_TRUTH_SOURCE,
        )
    )

    return samples


if __name__ == "__main__":
    samples = load_all_samples()
    df = build_dataframe(samples)

    print(f"Tổng số bệnh nhân: {len(df)}\n")
    print(df[["patient_id", "biochemical_available", "ultrasound_available",
              "mri_available", "label"]])

    print("\n--- Case-01 chi tiết (toàn bộ cột) ---")
    case_row = df[df["patient_id"] == "case_01"].T
    print(case_row)
