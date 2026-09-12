from config.schema_config import MODALITY_FEATURES, MISSING_THRESHOLD
from core.missing_utils import compute_feature_mask, compute_modality_available


def values_for_modality(modality_name, fill_value=1):
    return {
        feature: fill_value
        for feature in MODALITY_FEATURES[modality_name]
    }


def test_compute_feature_mask_all_present():
    values = values_for_modality("tabular", fill_value=1)

    assert compute_feature_mask(values, "tabular") == [1] * 14


def test_compute_feature_mask_all_none():
    values = values_for_modality("mri", fill_value=None)

    assert compute_feature_mask(values, "mri") == [0] * 8


def test_other_cancer_primary_site_not_applicable_is_not_missing():
    values = values_for_modality("tabular", fill_value=1)
    values["other_cancer_history"] = 0
    values["other_cancer_primary_site"] = None

    mask = compute_feature_mask(values, "tabular")
    index = MODALITY_FEATURES["tabular"].index("other_cancer_primary_site")

    assert mask[index] == 1


def test_other_cancer_primary_site_required_when_history_positive():
    values = values_for_modality("tabular", fill_value=1)
    values["other_cancer_history"] = 1
    values["other_cancer_primary_site"] = None

    mask = compute_feature_mask(values, "tabular")
    index = MODALITY_FEATURES["tabular"].index("other_cancer_primary_site")

    assert mask[index] == 0


def test_other_cancer_primary_site_present_when_history_positive():
    values = values_for_modality("tabular", fill_value=1)
    values["other_cancer_history"] = 1
    values["other_cancer_primary_site"] = "phoi"

    mask = compute_feature_mask(values, "tabular")
    index = MODALITY_FEATURES["tabular"].index("other_cancer_primary_site")

    assert mask[index] == 1


def test_feature_mask_order_follows_schema_not_input_order():
    values = {
        "ROMA": 1,
        "age": 1,
        "CA125": None,
    }

    mask = compute_feature_mask(values, "tabular")

    assert len(mask) == len(MODALITY_FEATURES["tabular"])
    assert mask[MODALITY_FEATURES["tabular"].index("age")] == 1
    assert mask[MODALITY_FEATURES["tabular"].index("CA125")] == 0
    assert mask[MODALITY_FEATURES["tabular"].index("ROMA")] == 1


def test_missing_key_is_treated_as_none():
    values = values_for_modality("ultrasound", fill_value=1)
    values.pop("doppler_score")

    mask = compute_feature_mask(values, "ultrasound")
    index = MODALITY_FEATURES["ultrasound"].index("doppler_score")

    assert mask[index] == 0


def test_tabular_availability_boundaries():
    assert compute_modality_available([1] * 14, "tabular") == 1
    assert compute_modality_available([0] * 4 + [1] * 10, "tabular") == 1
    assert compute_modality_available([0] * 5 + [1] * 9, "tabular") == 0


def test_threshold_boundary_is_inclusive():
    assert MISSING_THRESHOLD["mri"] == 0.25
    assert compute_modality_available([0] * 2 + [1] * 6, "mri") == 1


def test_modality_thresholds_are_applied_separately():
    assert MISSING_THRESHOLD["tabular"] == 0.30
    assert MISSING_THRESHOLD["ultrasound"] == 0.25
    assert MISSING_THRESHOLD["mri"] == 0.25

    assert compute_modality_available([0] * 4 + [1] * 10, "tabular") == 1
    assert compute_modality_available([0] * 4 + [1] * 10, "ultrasound") == 0
    assert compute_modality_available([0] * 2 + [1] * 6, "mri") == 1
