"""
Mock data mở rộng — dùng để test pipeline với nhiều edge case.
Schema v2 (2026-08-15): đã bổ sung trường mới từ data_dictionary.

Mục đích:
  - Kiểm tra pipeline xử lý đúng với nhiều tình huống đặc biệt.
  - KHÔNG phản ánh phân phối thật của dữ liệu bệnh viện.
  - Giá trị các trường mới (v2) được gán hợp lý theo ngữ cảnh lâm sàng
    của từng case nhưng là DỮ LIỆU NHÂN TẠO, không phải data thật.

Thay đổi so với v1:
  - clinical: thêm pregnancy_status, bilateral_lesion,
    months_detection_to_surgery, prior_ovarian_surgery,
    other_cancer_history, other_cancer_primary_site, oncology_center_flag
  - ultrasound: thêm laterality, solid_component_present, multilocular,
    irregular_wall_or_septa, vascularity_description, iota_adnex_available
  - mri: DWI_ADC (float) → restricted_diffusion (binary 0/1)
         septa_thickness (float) → thick_septa (binary 0/1)
"""

MOCK_PATIENTS = [

    # ─────────────────────────────────────────────────────────────────────────
    # P001 — Case GỐC (cập nhật sang schema v2)
    # Non-cancer (0), đủ tất cả modality
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P001",
        "modality_values": {
            "tabular": {
                "age": 42, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 2.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 300, "HE4": None, "AFP": None, "beta_hCG": 3, "ROMA": None,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 149, "solid_max_diameter_mm": 84,
                "papillary_count": 2, "more_than_10_locules": 0,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": 3,
                "morphology_class": 4,
                "laterality": "right", "solid_component_present": 1,
                "multilocular": 1, "irregular_wall_or_septa": 1,
                "vascularity_description": "moderate", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 80, "TIC": 2,
                "restricted_diffusion": 0, "thick_septa": 1,
                "ascites_mri": 0, "morphology_class_mri": 4, "o_rads_mri": 4,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P002 — CANCER ĐIỂN HÌNH, đủ data hoàn toàn
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P002",
        "modality_values": {
            "tabular": {
                "age": 58, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": 1,
                "months_detection_to_surgery": 3.5,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 850, "HE4": 210, "AFP": 1.2, "beta_hCG": 1, "ROMA": 88,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 120, "solid_max_diameter_mm": 70,
                "papillary_count": 5, "more_than_10_locules": 1,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": 4,
                "morphology_class": 4,
                "laterality": "bilateral", "solid_component_present": 1,
                "multilocular": 1, "irregular_wall_or_septa": 1,
                "vascularity_description": "rich", "iota_adnex_available": 1,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 65, "TIC": 3,
                "restricted_diffusion": 1, "thick_septa": 1,
                "ascites_mri": 1, "morphology_class_mri": 4, "o_rads_mri": 5,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P003 — LÀNH TÍNH ĐIỂN HÌNH, đủ data hoàn toàn
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P003",
        "modality_values": {
            "tabular": {
                "age": 32, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 1.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": 18, "HE4": 42, "AFP": 0.9, "beta_hCG": 2, "ROMA": 5,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 35, "solid_max_diameter_mm": 0,
                "papillary_count": 0, "more_than_10_locules": 0,
                "acoustic_shadow": 1, "ascites": 0, "doppler_score": 1,
                "morphology_class": 1,
                "laterality": "left", "solid_component_present": 0,
                "multilocular": 0, "irregular_wall_or_septa": 0,
                "vascularity_description": "none", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 0, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 0, "morphology_class_mri": 1, "o_rads_mri": 2,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P004 — EDGE CASE: Chỉ có Clinical, không có Biochemical / US / MRI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P004",
        "modality_values": {
            "tabular": {
                "age": 51, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": None,
                "months_detection_to_surgery": 4.0,
                "prior_ovarian_surgery": 1, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": None, "HE4": None, "AFP": None, "beta_hCG": None, "ROMA": None,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": None, "solid_max_diameter_mm": None,
                "papillary_count": None, "more_than_10_locules": None,
                "acoustic_shadow": None, "ascites": None, "doppler_score": None,
                "morphology_class": None,
                "laterality": None, "solid_component_present": None,
                "multilocular": None, "irregular_wall_or_septa": None,
                "vascularity_description": None, "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": None, "solid_max_diameter_mm": None, "TIC": None,
                "restricted_diffusion": None, "thick_septa": None,
                "ascites_mri": None, "morphology_class_mri": None, "o_rads_mri": None,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P005 — EDGE CASE: Chỉ có Clinical + Biochemical, không có US/MRI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P005",
        "modality_values": {
            "tabular": {
                "age": 65, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": None,
                "months_detection_to_surgery": 6.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 2100, "HE4": 430, "AFP": 1.5, "beta_hCG": 1, "ROMA": 97,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": None, "solid_max_diameter_mm": None,
                "papillary_count": None, "more_than_10_locules": None,
                "acoustic_shadow": None, "ascites": None, "doppler_score": None,
                "morphology_class": None,
                "laterality": None, "solid_component_present": None,
                "multilocular": None, "irregular_wall_or_septa": None,
                "vascularity_description": None, "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": None, "solid_max_diameter_mm": None, "TIC": None,
                "restricted_diffusion": None, "thick_septa": None,
                "ascites_mri": None, "morphology_class_mri": None, "o_rads_mri": None,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P006 — EDGE CASE: Biochemical 3/5 None (60% > 30%) → unavailable
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P006",
        "modality_values": {
            "tabular": {
                "age": 45, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 1.5,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": 55, "HE4": None, "AFP": None, "beta_hCG": 8, "ROMA": None,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 60, "solid_max_diameter_mm": 0,
                "papillary_count": 0, "more_than_10_locules": 0,
                "acoustic_shadow": 1, "ascites": 0, "doppler_score": 1,
                "morphology_class": 2,
                "laterality": "left", "solid_component_present": 0,
                "multilocular": 0, "irregular_wall_or_septa": 0,
                "vascularity_description": "minimal", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 0, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 0, "morphology_class_mri": 2, "o_rads_mri": 2,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P007 — EDGE CASE: Biochemical 1/5 None (20% ≤ 30%) → available
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P007",
        "modality_values": {
            "tabular": {
                "age": 37, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 0.5,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": 28, "HE4": 60, "AFP": None, "beta_hCG": 3, "ROMA": 12,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 45, "solid_max_diameter_mm": 5,
                "papillary_count": 1, "more_than_10_locules": 0,
                "acoustic_shadow": 0, "ascites": 0, "doppler_score": 2,
                "morphology_class": 2,
                "laterality": "right", "solid_component_present": 1,
                "multilocular": 0, "irregular_wall_or_septa": 0,
                "vascularity_description": "minimal", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 5, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 0, "morphology_class_mri": 2, "o_rads_mri": 3,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P008 — EDGE CASE: Bệnh nhân RẤT TRẺ (18 tuổi), lành tính
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P008",
        "modality_values": {
            "tabular": {
                "age": 18, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 1.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": 12, "HE4": 35, "AFP": 1.1, "beta_hCG": 1, "ROMA": 3,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 28, "solid_max_diameter_mm": 0,
                "papillary_count": 0, "more_than_10_locules": 0,
                "acoustic_shadow": 1, "ascites": 0, "doppler_score": 1,
                "morphology_class": 1,
                "laterality": "right", "solid_component_present": 0,
                "multilocular": 0, "irregular_wall_or_septa": 0,
                "vascularity_description": "none", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 0, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 0, "morphology_class_mri": 1, "o_rads_mri": 1,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P009 — EDGE CASE: Bệnh nhân RẤT GIÀ (80 tuổi), hậu mãn kinh, cancer
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P009",
        "modality_values": {
            "tabular": {
                "age": 80, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": 1,
                "months_detection_to_surgery": 8.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 1,
                "other_cancer_primary_site": "breast", "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 1500, "HE4": 520, "AFP": 2.0, "beta_hCG": 1, "ROMA": 99,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 200, "solid_max_diameter_mm": 150,
                "papillary_count": 8, "more_than_10_locules": 1,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": 4,
                "morphology_class": 4,
                "laterality": "bilateral", "solid_component_present": 1,
                "multilocular": 1, "irregular_wall_or_septa": 1,
                "vascularity_description": "rich", "iota_adnex_available": 1,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 140, "TIC": 3,
                "restricted_diffusion": 1, "thick_septa": 1,
                "ascites_mri": 1, "morphology_class_mri": 4, "o_rads_mri": 5,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P010 — EDGE CASE: CA125 cực cao (5000) nhưng LÀNH TÍNH (false positive)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P010",
        "modality_values": {
            "tabular": {
                "age": 38, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 3.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": 5000, "HE4": 55, "AFP": 0.8, "beta_hCG": 2, "ROMA": 40,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 90, "solid_max_diameter_mm": 0,
                "papillary_count": 0, "more_than_10_locules": 1,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": 2,
                "morphology_class": 3,
                "laterality": "left", "solid_component_present": 0,
                "multilocular": 1, "irregular_wall_or_septa": 1,
                "vascularity_description": "minimal", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 0, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 1, "morphology_class_mri": 3, "o_rads_mri": 3,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P011 — EDGE CASE: CA125 bình thường (22) nhưng CANCER (false negative)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P011",
        "modality_values": {
            "tabular": {
                "age": 44, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 2.5,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 22, "HE4": 48, "AFP": 1.0, "beta_hCG": 1, "ROMA": 7,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 85, "solid_max_diameter_mm": 60,
                "papillary_count": 3, "more_than_10_locules": 0,
                "acoustic_shadow": 0, "ascites": 0, "doppler_score": 3,
                "morphology_class": 3,
                "laterality": "right", "solid_component_present": 1,
                "multilocular": 0, "irregular_wall_or_septa": 1,
                "vascularity_description": "moderate", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 55, "TIC": 2,
                "restricted_diffusion": 1, "thick_septa": 1,
                "ascites_mri": 0, "morphology_class_mri": 4, "o_rads_mri": 4,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P012 — EDGE CASE: Chỉ có US (2/14 None = 14% ≤ 25%), không có Biochemical
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P012",
        "modality_values": {
            "tabular": {
                "age": 50, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 5.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": None, "HE4": None, "AFP": None, "beta_hCG": None, "ROMA": None,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 78, "solid_max_diameter_mm": 30,
                "papillary_count": 2, "more_than_10_locules": None,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": None,
                "morphology_class": 3,
                "laterality": "right", "solid_component_present": 1,
                "multilocular": 1, "irregular_wall_or_septa": 0,
                "vascularity_description": "moderate", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": None, "solid_max_diameter_mm": None, "TIC": None,
                "restricted_diffusion": None, "thick_septa": None,
                "ascites_mri": None, "morphology_class_mri": None, "o_rads_mri": None,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P013 — EDGE CASE: US vượt ngưỡng missing (3/14 = 21% ≤ 25%)
    # LƯU Ý: với schema v2 có 14 US features, 3 None = 21% ≤ 25% → vẫn available
    # (khác với v1 là 8 features, 3/8=37.5% → unavailable)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P013",
        "modality_values": {
            "tabular": {
                "age": 55, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 7.0,
                "prior_ovarian_surgery": 1, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 120, "HE4": 90, "AFP": 1.3, "beta_hCG": 2, "ROMA": 45,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 95, "solid_max_diameter_mm": None,
                "papillary_count": None, "more_than_10_locules": None,
                "acoustic_shadow": 0, "ascites": 1, "doppler_score": 3,
                "morphology_class": 3,
                "laterality": "left", "solid_component_present": 1,
                "multilocular": 1, "irregular_wall_or_septa": 1,
                "vascularity_description": "moderate", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 40, "TIC": 2,
                "restricted_diffusion": 1, "thick_septa": 1,
                "ascites_mri": 0, "morphology_class_mri": 3, "o_rads_mri": 4,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P014 — EDGE CASE: CA125=None nhưng 4 biochemical còn lại có (20% ≤ 30%)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P014",
        "modality_values": {
            "tabular": {
                "age": 48, "menopause": 0,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 2.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 0,
                            # -- Sinh hoa --
                "CA125": None, "HE4": 75, "AFP": 1.2, "beta_hCG": 4, "ROMA": 20,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": 55, "solid_max_diameter_mm": 10,
                "papillary_count": 1, "more_than_10_locules": 0,
                "acoustic_shadow": 0, "ascites": 0, "doppler_score": 2,
                "morphology_class": 2,
                "laterality": "right", "solid_component_present": 1,
                "multilocular": 0, "irregular_wall_or_septa": 0,
                "vascularity_description": "minimal", "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 0, "solid_max_diameter_mm": 10, "TIC": 1,
                "restricted_diffusion": 0, "thick_septa": 0,
                "ascites_mri": 0, "morphology_class_mri": 2, "o_rads_mri": 3,
            },
        },
        "ground_truth_label":  0,
        "ground_truth_source": "pathology_report",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # P015 — EDGE CASE: Có MRI đủ, không có US; Biochemical thiếu nhiều
    # ─────────────────────────────────────────────────────────────────────────
    {
        "patient_id": "mock_P015",
        "modality_values": {
            "tabular": {
                "age": 62, "menopause": 1,
                "pregnancy_status": 0, "bilateral_lesion": 0,
                "months_detection_to_surgery": 12.0,
                "prior_ovarian_surgery": 0, "other_cancer_history": 0,
                "other_cancer_primary_site": None, "oncology_center_flag": 1,
                            # -- Sinh hoa --
                "CA125": 380, "HE4": None, "AFP": None, "beta_hCG": None, "ROMA": None,
            },
            "ultrasound": {
                "lesion_max_diameter_mm": None, "solid_max_diameter_mm": None,
                "papillary_count": None, "more_than_10_locules": None,
                "acoustic_shadow": None, "ascites": None, "doppler_score": None,
                "morphology_class": None,
                "laterality": None, "solid_component_present": None,
                "multilocular": None, "irregular_wall_or_septa": None,
                "vascularity_description": None, "iota_adnex_available": 0,
            },
            "mri": {
                "solid_component": 1, "solid_max_diameter_mm": 55, "TIC": 3,
                "restricted_diffusion": 1, "thick_septa": 1,
                "ascites_mri": 1, "morphology_class_mri": 4, "o_rads_mri": 5,
            },
        },
        "ground_truth_label":  1,
        "ground_truth_source": "pathology_report",
    },

]
