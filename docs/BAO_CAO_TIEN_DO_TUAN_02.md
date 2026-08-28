# Báo cáo Tiến độ Tuần 2

**Đề tài:** Hệ thống AI hỗ trợ dự báo nguy cơ ung thư khối u buồng trứng trước phẫu thuật

**Phạm vi báo cáo:** Pipeline trích xuất dữ liệu, ba Expert, LOOCV và Late Fusion baseline trên 12 ca thực tế.

## 1. Tóm tắt tiến độ

Tuần 2 đã chuyển pipeline từ dữ liệu mock và một ca thử nghiệm sang bộ 12 ca thực tế. Trong quá trình này, nhóm đã phát hiện overfitting của parser OCR/regex, kiểm toán lại Ground Truth, khóa checksum, xây dựng ba Expert và đánh giá bằng LOOCV. Late Fusion baseline đã được chạy bằng các prediction Logistic out-of-fold.

## 2. Pipeline OCR ban đầu và phát hiện overfitting

Pipeline ban đầu dùng PaddleOCR offline kết hợp rule/regex Python để định tuyến phiếu và trích xuất các biến Clinical, Biochemical, Ultrasound và MRI. Khi kiểm tra held-out Case 03, kết quả chỉ đạt 37.8%, trong khi kết quả trên Case 01/02 từng đạt khoảng 97.3%. Chênh lệch này cho thấy parser đang phụ thuộc quá nhiều vào các mẫu đã thấy, không đủ an toàn để làm nguồn Ground Truth tự động.

Vì vậy, dự án chuyển từ cách tinh chỉnh từng ca sang đọc toàn bộ 12 ca, lập danh mục biến thể ngôn ngữ một lần và thiết kế parser tổng quát hơn. Kết quả trên 12 ca hiện tại là in-sample đối với quá trình thiết kế parser; held-out test thật phải được lặp lại khi bệnh viện cung cấp ca mới.

## 3. Sự cố và bảo vệ Ground Truth

Đã phát hiện sai lệch ở các trường `iota_adnex_available` và `bilateral_lesion` trong quá trình kiểm toán. Các giá trị chuẩn được khôi phục theo ảnh nguồn và quy ước đã thống nhất. Case 12 không có phiếu GPB mô bệnh học sau mổ nên `cancer_label` được giữ là `None`.

Toàn bộ 12 báo cáo Ground Truth trong `docs/` là nguồn chuẩn duy nhất. Checksum SHA-256 được tạo và kiểm tra bằng `scratch/verify_ground_truth_checksums.py`. Kết quả kiểm tra gần nhất: 14/14 file hợp lệ, gồm 12 báo cáo Ground Truth và 2 file dữ liệu liên quan.

Một lỗi parser cũng được phát hiện: dòng `Nhãn cancer_label` của Case 01 từng bị đọc thành chuỗi `"'1'"` thay vì số nguyên `1`. Parser được chuẩn hóa tên field và regression check xác nhận 11 nhãn đã xác định đều là `int` đúng giá trị 0/1; Case 12 vẫn là `None`; phân bố là 5 ác tính, 6 không ung thư/giáp biên, 1 chưa xác nhận.

## 4. BaseExpert và ba Expert

Logic dùng chung được tách vào `models/base_expert.py`. Ba class mỏng lấy feature list từ `config/schema_config.py`:

- `TabularExpert`: 14 biến lâm sàng + sinh hóa.
- `UltrasoundExpert`: 14 biến IOTA.
- `MRIExpert`: 8 biến O-RADS.

Ba model type Logistic Regression, Random Forest và LightGBM đều vượt qua smoke test trên 15 mock patients. Logistic/RF dùng median imputation cho các cột numeric; LightGBM dùng native missing handling và categorical levels.

## 5. Build và lọc dữ liệu thật

Dataset supervised được lọc độc lập theo hai điều kiện:

1. `ground_truth.label is not None`.
2. Modality tương ứng có `available == 1`.

| Expert | Số ca | Ác tính | Không ung thư |
|---|---:|---:|---:|
| Tabular | 9 | 4 | 5 |
| Ultrasound | 11 | 5 | 6 |
| MRI | 10 | 4 | 6 |

Case 12 bị loại khỏi cả ba dataset supervised.

## 6. LOOCV độc lập

Script `scripts/evaluate_experts_loocv.py` chạy Leave-One-Out Cross-Validation cho từng Expert và từng model type. Kết quả được lưu trong `results/real_experts_loocv_predictions.csv` với 90 dòng và `results/real_experts_loocv_metrics.csv` với 9 dòng.

| Expert | Logistic AUC | Random Forest AUC | LightGBM AUC |
|---|---:|---:|---:|
| Tabular | 0.7500 | 0.7250 | 0.7000 |
| Ultrasound | 0.3667 | 0.6000 | 0.5667 |
| MRI | 0.7083 | 0.5833 | 0.4167 |

Các giá trị trên chỉ xác nhận pipeline LOOCV chạy được. N chỉ từ 9 đến 11 nên chưa có ý nghĩa thống kê hoặc lâm sàng.

## 7. Late Fusion baseline

Late Fusion dùng prediction Logistic out-of-fold của ba Expert, ghép theo `patient_id`. Modality thiếu được bỏ qua và trọng số trung bình được renormalize trên các Expert khả dụng.

Có 8 ca dùng đủ 3 Expert. Case 04 dùng Tabular + Ultrasound vì thiếu MRI. Case 05 và Case 10 dùng Ultrasound + MRI vì thiếu Tabular. Case 12 không được đưa vào đánh giá.

| Chiến lược | Số ca | ROC-AUC | Sensitivity | Specificity | F1 | Brier |
|---|---:|---:|---:|---:|---:|---:|
| Simple Average | 11 | 0.6667 | 0.6000 | 0.6667 | 0.6000 | 0.2720 |
| AND | 11 | 0.7000 | 0.4000 | 1.0000 | 0.5714 | 0.2727 |
| OR | 11 | 0.5500 | 0.6000 | 0.5000 | 0.5455 | 0.4545 |
| MAX | 11 | 0.7000 | 0.6000 | 0.5000 | 0.5455 | 0.3815 |

`Simple Average` được báo cáo riêng với nhóm voting `AND/OR/MAX`. Threshold 0.5 chỉ là threshold minh họa, chưa phải threshold lâm sàng.

## 8. Giới hạn và quyết định tiếp theo

- Dữ liệu thực tế hiện chỉ có 12 ca, trong đó mỗi Expert dùng 9-11 ca.
- Các metrics không được báo cáo như hiệu năng thật cho bệnh viện.
- LightGBM dùng thêm categorical features ở Tabular/Ultrasound, nên so sánh model type hiện chưa hoàn toàn công bằng.
- Không tối ưu trọng số hoặc threshold trên chính các prediction LOOCV này.
- Chưa dùng Case 12 trong supervised training/testing vì chưa có GPB sau mổ xác nhận.
- Chưa nâng cấp model và chưa tối ưu Late Fusion.

Khi bệnh viện cung cấp ca mới, quy trình tạm thời được chốt là đọc trực tiếp ảnh gốc, lập báo cáo Ground Truth riêng, đối chiếu và chạy checksum. Ước lượng ban đầu khoảng 2-4 giờ mỗi ca, có thể tăng nếu số ảnh lớn hoặc có nhiều trường cần bác sĩ xác nhận. Pipeline OCR/regex sẽ chỉ được dùng lại sau khi tái thiết kế đủ bốn tầng và có held-out test trên ca mới.

## 9. Danh sách file chính

- `models/base_expert.py`: logic chung cho ba Expert.
- `models/tabular_expert.py`: wrapper Tabular Expert.
- `models/ultrasound_expert.py`: wrapper Ultrasound Expert.
- `models/mri_expert.py`: wrapper MRI Expert.
- `scripts/prepare_real_expert_datasets.py`: lọc dataset supervised theo Expert.
- `scripts/evaluate_experts_loocv.py`: chạy LOOCV độc lập.
- `models/late_fusion.py`: logic kết hợp xác suất và luật voting.
- `scripts/evaluate_real_late_fusion.py`: chạy Late Fusion trên Logistic out-of-fold.
- `scratch/verify_parser_regression.py`: regression check parser.
- `scratch/verify_ground_truth_checksums.py`: kiểm tra toàn vẹn Ground Truth.
- `results/real_experts_loocv_predictions.csv`: prediction LOOCV.
- `results/real_experts_loocv_metrics.csv`: metrics LOOCV.
- `results/real_late_fusion_predictions.csv`: prediction Late Fusion.
- `results/real_late_fusion_metrics.csv`: metrics Late Fusion.
