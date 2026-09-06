import numpy as np
import pandas as pd
import pytest

from config.schema_config import MODALITY_FEATURES
from models.tabular_expert import TabularExpert


def make_mock_tabular_frame():
    rows = [
        {
            "age": 25,
            "menopause": 0,
            "pregnancy_status": 0,
            "bilateral_lesion": 0,
            "months_detection_to_surgery": 1.0,
            "prior_ovarian_surgery": 0,
            "other_cancer_history": 0,
            "other_cancer_primary_site": None,
            "oncology_center_flag": 1,
            "CA125": 20.0,
            "HE4": 40.0,
            "AFP": 2.0,
            "beta_hCG": 1.0,
            "ROMA": 5.0,
        },
        {
            "age": 35,
            "menopause": 0,
            "pregnancy_status": 0,
            "bilateral_lesion": 0,
            "months_detection_to_surgery": 2.0,
            "prior_ovarian_surgery": 0,
            "other_cancer_history": 0,
            "other_cancer_primary_site": None,
            "oncology_center_flag": 1,
            "CA125": None,
            "HE4": 45.0,
            "AFP": 2.5,
            "beta_hCG": 1.2,
            "ROMA": 6.0,
        },
        {
            "age": 60,
            "menopause": 1,
            "pregnancy_status": 0,
            "bilateral_lesion": 1,
            "months_detection_to_surgery": 4.0,
            "prior_ovarian_surgery": 0,
            "other_cancer_history": 1,
            "other_cancer_primary_site": "phoi",
            "oncology_center_flag": 1,
            "CA125": 600.0,
            "HE4": 300.0,
            "AFP": 4.0,
            "beta_hCG": 2.0,
            "ROMA": 65.0,
        },
        {
            "age": 70,
            "menopause": 1,
            "pregnancy_status": 0,
            "bilateral_lesion": 1,
            "months_detection_to_surgery": 6.0,
            "prior_ovarian_surgery": 1,
            "other_cancer_history": 0,
            "other_cancer_primary_site": None,
            "oncology_center_flag": 1,
            "CA125": 900.0,
            "HE4": 500.0,
            "AFP": None,
            "beta_hCG": 2.5,
            "ROMA": 80.0,
        },
    ]
    X = pd.DataFrame(rows, columns=MODALITY_FEATURES["tabular"])
    y = pd.Series([0, 0, 1, 1], name="label")
    return X, y


@pytest.mark.parametrize("model_type", ["logistic", "random_forest", "lightgbm"])
def test_tabular_expert_fit_and_predict_proba(model_type):
    X, y = make_mock_tabular_frame()
    expert = TabularExpert(model_type=model_type, random_state=42)

    expert.fit(X, y)
    probabilities = expert.predict_proba(X)

    assert len(probabilities) == len(X)
    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)


def test_predict_proba_before_fit_raises_runtime_error():
    X, _ = make_mock_tabular_frame()
    expert = TabularExpert(model_type="logistic")

    with pytest.raises(RuntimeError, match="chưa được fit|chÆ°a"):
        expert.predict_proba(X)


def test_invalid_model_type_raises_value_error():
    with pytest.raises(ValueError):
        TabularExpert(model_type="not_a_model")


@pytest.mark.parametrize("model_type", ["logistic", "random_forest", "lightgbm"])
def test_missing_values_do_not_crash_supported_models(model_type):
    X, y = make_mock_tabular_frame()
    X.loc[0, "CA125"] = None
    X.loc[1, "HE4"] = None

    expert = TabularExpert(model_type=model_type, random_state=42)
    expert.fit(X, y)
    probabilities = expert.predict_proba(X)

    assert len(probabilities) == len(X)
