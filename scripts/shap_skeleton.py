"""A3 smoke test: SHAP explanations for a standalone tabular LogisticRegression."""

import os
import sys

import pandas as pd
import shap
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.schema_config import MODALITY_FEATURES
from core.dataset_builder import build_dataframe
from core.sample_builder import build_patient_sample
from data.mock.mock_samples import MOCK_PATIENTS


DISCLAIMER = "N qua nho, ket qua khong co y nghia thong ke hoac lam sang."


def load_available_tabular_mock_data():
    samples = [
        build_patient_sample(
            patient_id=patient["patient_id"],
            modality_values=patient["modality_values"],
            ground_truth_label=patient["ground_truth_label"],
            ground_truth_source=patient.get("ground_truth_source", "mock"),
        )
        for patient in MOCK_PATIENTS
    ]
    dataframe = build_dataframe(samples)
    valid = dataframe[
        (dataframe["tabular_available"] == 1)
        & dataframe["label"].notna()
    ].copy()

    feature_columns = [
        f"tabular_{feature}" for feature in MODALITY_FEATURES["tabular"]
    ]
    valid = valid.reindex(columns=["patient_id", "label", *feature_columns])
    numeric_columns = [
        column for column in feature_columns
        if pd.api.types.is_numeric_dtype(valid[column])
    ]
    return valid, numeric_columns


def main():
    dataframe, feature_columns = load_available_tabular_mock_data()
    labels = dataframe["label"].astype(int)
    class_counts = labels.value_counts().sort_index().to_dict()

    print("A3 SHAP SMOKE TEST - MOCK TABULAR ONLY")
    print(DISCLAIMER)
    print(f"Samples after tabular availability filter: {len(dataframe)}")
    print(f"Class counts: {class_counts}")
    print(f"Numeric features used: {len(feature_columns)}")

    if class_counts.get(0, 0) < 2 or class_counts.get(1, 0) < 2:
        raise ValueError(
            "Mock Tabular data must contain at least two samples per class."
        )
    if not feature_columns:
        raise ValueError("No numeric Tabular features are available.")

    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    scaler = StandardScaler()
    X_imputed = imputer.fit_transform(dataframe[feature_columns])
    X_transformed = scaler.fit_transform(X_imputed)

    classifier = LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=42,
    )
    classifier.fit(X_transformed, labels)

    explainer = shap.LinearExplainer(classifier, X_transformed)
    explanations = explainer(X_transformed[: min(3, len(X_transformed))])
    shap_values = explanations.values

    print(f"Transformed matrix shape: {X_transformed.shape}")
    print(f"SHAP values shape: {shap_values.shape}")
    print(f"Feature names available: {len(feature_columns)}")
    if shap_values.shape != (min(3, len(dataframe)), len(feature_columns)):
        raise AssertionError("SHAP output shape does not match sample/feature shape.")
    print("Smoke test completed. No feature or clinical interpretation.")


if __name__ == "__main__":
    main()
