from config.schema_config import MODALITY_NAMES
from core.sample_builder import build_modality_block, build_patient_sample


def test_build_modality_block_has_expected_keys_and_availability():
    values = {
        "solid_component": 1,
        "solid_max_diameter_mm": 20.0,
        "TIC": 1,
        "restricted_diffusion": 1,
        "thick_septa": 0,
        "ascites_mri": 0,
        "morphology_class_mri": 4,
        "o_rads_mri": 3,
    }

    block = build_modality_block(values, "mri")

    assert set(block.keys()) == {"values", "feature_mask", "available"}
    assert block["feature_mask"] == [1] * 8
    assert block["available"] == 1


def test_build_modality_block_keeps_values_object_unchanged():
    values = {"age": 45}

    block = build_modality_block(values, "tabular")

    assert block["values"] is values
    assert values == {"age": 45}


def test_build_patient_sample_has_all_modalities_and_ground_truth():
    sample = build_patient_sample(
        patient_id="mock_001",
        modality_values={"mri": {"solid_component": 1}},
        ground_truth_label=1,
        ground_truth_source="mock_pathology",
    )

    assert sample["patient_id"] == "mock_001"
    for modality_name in MODALITY_NAMES:
        assert modality_name in sample
        assert set(sample[modality_name].keys()) == {"values", "feature_mask", "available"}
    assert sample["ground_truth"] == {
        "label": 1,
        "source": "mock_pathology",
    }


def test_missing_modality_values_default_to_unavailable():
    sample = build_patient_sample(
        patient_id="mock_002",
        modality_values={},
        ground_truth_label=0,
    )

    for modality_name in MODALITY_NAMES:
        assert sample[modality_name]["values"] == {}
        assert sample[modality_name]["available"] == 0


def test_ground_truth_label_none_is_preserved():
    sample = build_patient_sample(
        patient_id="mock_case_12",
        modality_values={},
        ground_truth_label=None,
        ground_truth_source="pending_pathology",
    )

    assert sample["ground_truth"]["label"] is None
    assert sample["ground_truth"]["source"] == "pending_pathology"
