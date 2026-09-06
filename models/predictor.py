"""End-to-end prediction helper for one patient."""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config.schema_config import MODALITY_FEATURES, MODALITY_NAMES
from core.missing_utils import compute_feature_mask, compute_modality_available
from models.late_fusion import LateFusion
from models.mri_expert import MRIExpert
from models.tabular_expert import TabularExpert
from models.ultrasound_expert import UltrasoundExpert
from scripts.prepare_real_expert_datasets import build_expert_dataset


DEMO_WARNING = (
    "DEMO_ONLY: N=9-11 too small for clinical use; pipeline check only."
)
FEATURE_WARNING = (
    "Logistic/RF use numeric features only; LightGBM exploratory may use extra "
    "categorical features in Tabular/Ultrasound."
)

EXPERT_CLASSES = {
    "tabular": TabularExpert,
    "ultrasound": UltrasoundExpert,
    "mri": MRIExpert,
}


def _feature_to_modalities() -> Dict[str, List[str]]:
    feature_map = defaultdict(list)
    for modality_name, features in MODALITY_FEATURES.items():
        for feature in features:
            feature_map[feature].append(modality_name)
    return dict(feature_map)


FEATURE_MODALITIES = _feature_to_modalities()
DUPLICATE_FEATURES = {
    feature: modalities
    for feature, modalities in FEATURE_MODALITIES.items()
    if len(modalities) > 1
}


class PatientPredictor:
    """In-memory fitted predictor for Tabular, Ultrasound, MRI and Late Fusion."""

    def __init__(
        self,
        experts: Dict[str, object],
        model_type: str,
        training_patient_ids: Dict[str, List[str]],
        training_summary: Dict[str, Dict[str, int]],
    ):
        self.experts = experts
        self.model_type = model_type
        self.training_patient_ids = training_patient_ids
        self.training_summary = training_summary
        self.duplicate_features = DUPLICATE_FEATURES
        self.fuser = LateFusion()

    @classmethod
    def fit_from_samples(
        cls,
        samples: List[dict],
        model_type: str = "logistic",
        random_state: int = 42,
    ) -> "PatientPredictor":
        """Fit one expert per modality from supervised, modality-available samples."""
        experts = {}
        training_patient_ids = {}
        training_summary = {}

        for modality_name in MODALITY_NAMES:
            X, y, patient_ids = build_expert_dataset(samples, modality_name)
            if any(patient_id == "case_12" for patient_id in patient_ids):
                raise AssertionError("case_12 must not be used for supervised fitting")
            if len(y) < 2 or y.nunique() < 2:
                raise ValueError(
                    f"Not enough labeled classes to fit {modality_name} expert."
                )

            expert = EXPERT_CLASSES[modality_name](
                model_type=model_type,
                random_state=random_state,
            )
            expert.fit(X, y)
            experts[modality_name] = expert
            training_patient_ids[modality_name] = list(patient_ids)
            training_summary[modality_name] = {
                "n_samples": int(len(y)),
                "n_malignant": int((y == 1).sum()),
                "n_non_cancer": int((y == 0).sum()),
            }

        return cls(
            experts=experts,
            model_type=model_type,
            training_patient_ids=training_patient_ids,
            training_summary=training_summary,
        )

    def predict_patient(self, patient_data: dict) -> dict:
        """Predict one patient from nested modality data or a flat schema-key dict."""
        modality_values, warnings = self._split_patient_data(patient_data)
        warnings.extend([DEMO_WARNING, FEATURE_WARNING])

        modality_probabilities = {modality_name: None for modality_name in MODALITY_NAMES}
        availability = {}
        missing_counts = {}

        for modality_name in MODALITY_NAMES:
            values = modality_values[modality_name]
            feature_mask = compute_feature_mask(values, modality_name)
            n_missing = feature_mask.count(0)
            n_total = len(feature_mask)
            is_available = compute_modality_available(feature_mask, modality_name)
            availability[modality_name] = is_available
            missing_counts[modality_name] = {
                "missing": n_missing,
                "total": n_total,
            }

            if not is_available:
                warnings.append(
                    f"{modality_name}_unavailable: missing {n_missing}/{n_total} fields"
                )
                continue

            X = pd.DataFrame([values], columns=MODALITY_FEATURES[modality_name])
            probability = self.experts[modality_name].predict_proba(X)[0]
            modality_probabilities[modality_name] = round(float(probability), 4)

        fusion_result = self.fuser.fuse(
            modality_probabilities,
            strategy="simple_average",
        )
        if fusion_result["P_fusion"] is None:
            warnings.append("no_available_modality: cannot compute P_fusion")

        return {
            "P_fusion": fusion_result["P_fusion"],
            "experts_used": fusion_result["experts_used"],
            "modality_probabilities": modality_probabilities,
            "availability": availability,
            "missing_counts": missing_counts,
            "warning_flags": warnings,
        }

    def _split_patient_data(self, patient_data: dict) -> Tuple[Dict[str, dict], List[str]]:
        if not isinstance(patient_data, dict):
            raise TypeError("patient_data must be a dict")

        warnings = []
        modality_values = {
            modality_name: {
                feature: None for feature in MODALITY_FEATURES[modality_name]
            }
            for modality_name in MODALITY_NAMES
        }

        nested_keys = {
            key for key, value in patient_data.items()
            if key in MODALITY_NAMES and isinstance(value, dict)
        }

        for key, value in patient_data.items():
            if key in nested_keys:
                continue
            if key in DUPLICATE_FEATURES:
                modalities = ",".join(DUPLICATE_FEATURES[key])
                warnings.append(f"ambiguous_flat_key: {key} appears in {modalities}")
                continue
            modalities = FEATURE_MODALITIES.get(key)
            if modalities:
                modality_values[modalities[0]][key] = value
            else:
                warnings.append(f"unknown_input_key_ignored: {key}")

        for modality_name in nested_keys:
            for key, value in patient_data[modality_name].items():
                if key in MODALITY_FEATURES[modality_name]:
                    modality_values[modality_name][key] = value
                else:
                    warnings.append(f"unknown_input_key_ignored: {modality_name}.{key}")

        return modality_values, warnings


def predict_patient(patient_data: dict, predictor: Optional[PatientPredictor] = None) -> dict:
    """Module-level wrapper around a fitted PatientPredictor."""
    if predictor is None:
        raise ValueError(
            "A fitted PatientPredictor is required. "
            "Use PatientPredictor.fit_from_samples(...) before calling predict_patient()."
        )
    return predictor.predict_patient(patient_data)
