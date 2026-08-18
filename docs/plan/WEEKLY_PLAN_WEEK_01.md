# Kế hoạch & Checklist Tiến độ - Tuần 1

**Dự án:** Hệ thống AI dự báo nguy cơ ung thư khối u buồng trứng trước phẫu thuật  
**Đơn vị phối hợp:** Trường Đại học Y Dược / Bệnh viện Từ Dũ  
**Mục tiêu tuần 1:** Hoàn thiện Data Pipeline Multimodal, xây dựng & so sánh các mô hình chuyên biệt Tabular (Logistic Regression, Random Forest, LightGBM), thiết lập phương pháp đánh giá LOOCV và khung tích hợp Late Fusion Scaffold.

---

## 📋 Checklist Tiến độ Tuần 1 (Báo cáo Người hướng dẫn)

### 1. Nền tảng Dữ liệu & Quy chuẩn Multimodal (Thứ 2 - Thứ 3)
- [x] **1.1.** Hoàn thành bài tập kiểm tra tư duy Feature Mask, Modality Availability và Label GPB.
- [x] **1.2.** Thống nhất Schema dữ liệu cho các nhóm (Lâm sàng, Sinh hóa, Siêu âm, MRI...).
- [x] **1.3.** Xây dựng Data Pipeline chuyển đổi dữ liệu bệnh nhân từ dạng thô/dict sang pandas DataFrame phẳng (`core/dataset_builder.py`).
- [x] **1.4.** Đảm bảo nguyên tắc xử lý dữ liệu thiếu (Missing Data): `missing != 0`, kiểm tra ngưỡng Completeness cho từng modality (`core/missing_utils.py`).

### 2. Nguyên tắc Dữ liệu & Chống Rò rỉ Thông tin (Thứ 4 - Thứ 5)
- [x] **2.1.** Kiểm tra nguyên tắc chống rò rỉ dữ liệu (Data Leakage): Chỉ dùng dữ liệu trước phẫu thuật làm predictor; Ground Truth bắt buộc là Giải phẫu bệnh sau mổ.
- [x] **2.2.** Mở rộng bộ dữ liệu mô phỏng (`data/mock/mock_samples.py` - 15 ca edge cases) để kiểm thử toàn diện các trường hợp biên của dữ liệu y tế.
- 💡 *(Lưu ý: Luồng Information Extraction tự động từ văn bản báo cáo y tế thô của bệnh viện sẽ được chuyển sang triển khai trong Tuần 2 cùng với 11 ca bệnh nhân thật).*

### 3. Huấn luyện Mô hình Chuyên biệt Dữ liệu Bảng (Thứ 6)
- [x] **3.1.** Xây dựng module mô hình chuyên biệt dữ liệu bảng (Tabular Expert): `models/tabular_expert.py` hỗ trợ Logistic Regression, Random Forest, và LightGBM (Native Missing Handling & Categorical Support).
- [x] **3.2.** Viết script huấn luyện và đánh giá: `scripts/train_tabular_expert.py`, chuẩn hóa thông báo chẩn đoán mô phỏng trung tính `[DEMO - CHƯA VALIDATE]` và tự động xuất CSV kết quả.
- [x] **3.3.** Kiểm tra luồng đánh giá không overfit với **LOOCV (Leave-One-Out Cross-Validation)**: `scripts/evaluate_loocv.py` xuất `results/loocv_results.csv`.

### 4. Tích hợp Late Fusion & Đánh giá Ban đầu (Thứ 7 - Chủ Nhật)
- [x] **4.1.** Triển khai module Late Fusion Scaffold: `models/late_fusion.py` và script thử nghiệm `scripts/evaluate_late_fusion.py` (đọc P(cancer) từ LOOCV).
- [x] **4.2.** Đánh giá các chỉ số cơ bản: ROC-AUC (chỉ số chính), Sensitivity, Specificity (kèm số đếm thô TP/FP/TN/FN).
- [x] **4.3.** Tổng hợp báo cáo tiến độ tuần 1 gửi cho Người hướng dẫn / Giảng viên (`docs/BAO_CAO_TIEN_DO_TUAN_01.md`).

---

## 🎯 Mục tiêu đầu ra của Tuần 1 (Deliverables) — ĐÃ HOÀN THÀNH 100%
1. **Source Code:** Data Pipeline hoàn chỉnh hỗ trợ `feature_mask` & `modality_available`.
2. **Tabular Expert Models:** Pipeline hoàn chỉnh so sánh 3 mô hình (LR, RF, LightGBM) và đánh giá qua LOOCV.
3. **Late Fusion Scaffold:** Khung kết hợp đa phương thức sẵn sàng tiếp nhận thêm các Expert (US, MRI).
4. **Báo cáo tiến độ Tuần 1:** Bản tóm tắt kết quả gửi Giảng viên kèm định hướng triển khai dữ liệu thực tế cho Tuần 2.
