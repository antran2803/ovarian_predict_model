import pytest

from core.gt_report_parser import parse_gt_report_to_dict


def parse_report(tmp_path, text):
    path = tmp_path / "EXTRACTION_REPORT_CASE_99.md"
    path.write_text(text, encoding="utf-8")
    return parse_gt_report_to_dict(str(path))


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("us,mri", [(185.0, 137.0), (38.0, None), (0.0, 50.0), (23.0, 0.0)])
def test_shared_field_keeps_modality_value(tmp_path, reverse, us, mri):
    sections = [
        f"### B. Nhóm Siêu âm `ultrasound`\n| `solid_max_diameter_mm` | {us} |",
        f"### C. Dữ Liệu Cộng Hưởng Từ (MRI O-RADS - 8 biến)\n| `solid_max_diameter_mm` | {mri} |",
    ]
    if reverse:
        sections.reverse()
    result = parse_report(tmp_path, "\n".join(sections))
    assert result["modality_values"]["ultrasound"]["solid_max_diameter_mm"] == us
    assert result["modality_values"]["mri"]["solid_max_diameter_mm"] == mri


@pytest.mark.parametrize("modality,other", [("ultrasound", "mri"), ("mri", "ultrasound")])
def test_missing_modality_does_not_inherit_other_value(tmp_path, modality, other):
    result = parse_report(tmp_path, f"### {modality}\n| solid_max_diameter_mm | 27.0 |")
    assert result["modality_values"][modality]["solid_max_diameter_mm"] == 27.0
    assert result["modality_values"][other]["solid_max_diameter_mm"] is None


@pytest.mark.parametrize("reverse", [False, True])
def test_inline_pending_does_not_cross_modalities(tmp_path, reverse):
    sections = [
        "### Ultrasound\n| solid_max_diameter_mm | 38 | measured |",
        "### MRI\n| solid_max_diameter_mm | 99 | PENDING_CONFIRMATION |",
    ]
    if reverse:
        sections.reverse()
    result = parse_report(tmp_path, "\n".join(sections))
    assert result["modality_values"]["ultrasound"]["solid_max_diameter_mm"] == 38.0
    assert result["modality_values"]["mri"]["solid_max_diameter_mm"] is None


def test_scoped_pending_note_and_label_preserve_other_modality(tmp_path):
    result = parse_report(tmp_path, """
### A. Tabular
| age | 41 |
| bilateral_lesion | 1 |
### B. Ultrasound
| solid_max_diameter_mm | 38 |
### C. MRI
| solid_max_diameter_mm | 99 |
### D. Ground Truth
| Nhãn `cancer_label` | 1 | PENDING_CONFIRMATION |
## 2. Trường cần bác sĩ xác nhận
* `solid_max_diameter_mm (MRI)`: PENDING_CONFIRMATION
* `bilateral_lesion`: PENDING_CONFIRMATION
""")
    assert result["modality_values"]["ultrasound"]["solid_max_diameter_mm"] == 38.0
    assert result["modality_values"]["mri"]["solid_max_diameter_mm"] is None
    assert result["modality_values"]["tabular"]["age"] == 41
    assert result["modality_values"]["tabular"]["bilateral_lesion"] is None
    assert result["ground_truth_label"] is None


@pytest.mark.parametrize("text", [
    "| solid_max_diameter_mm | 12 |",
    "### MRI\n| solid_max_diameter_mm | 99 |\n## Unrelated\n| solid_max_diameter_mm | 12 |",
    "### Ultrasound\n| solid_max_diameter_mm | 38 |\n## 2. Trường cần bác sĩ xác nhận\n* `solid_max_diameter_mm`: PENDING_CONFIRMATION",
])
def test_ambiguous_shared_field_fails_explicitly(tmp_path, text):
    with pytest.raises(ValueError, match="modality"):
        parse_report(tmp_path, text)
