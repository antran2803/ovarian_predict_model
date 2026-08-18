# Báo cáo Tiến độ Tuần 1

**Dự án:** Hệ thống AI dự báo nguy cơ ung thư khối u buồng trứng trước phẫu thuật  
**Ngày báo cáo:** 2026-08-15  
**Người thực hiện:** [Sinh viên]  
**Người hướng dẫn:** [Giảng viên / Bệnh viện]

---

## 1. Tóm tắt kết quả theo Checklist

| Mục | Nội dung | Trạng thái |
|-----|----------|-----------|
| 1.1 | Bài tập kiểm tra tư duy Feature Mask, Modality Availability, Label GPB | ✅ Hoàn thành |
| 1.2 | Thống nhất Schema dữ liệu (Clinical, Biochemical, Ultrasound, MRI) | ✅ Hoàn thành |
| 1.3 | Data Pipeline: dict bệnh nhân → pandas DataFrame phẳng | ✅ Hoàn thành |
| 1.4 | Nguyên tắc xử lý Missing Data, ngưỡng Completeness từng modality | ✅ Hoàn thành |
| 2.1 | Thiết kế luồng Information Extraction (Raw Report → Structured Features) | ✅ Hoàn thành (thủ công, xem mục 4) |
| 2.2 | Quy chuẩn Siêu âm (8 biến IOTA) và MRI từ kết quả đọc bác sĩ | ✅ Hoàn thành (xem schema_config.py) |
| 2.3 | Kiểm tra nguyên tắc chống Data Leakage | ✅ Hoàn thành (xem mục 3) |
| 3.1 | Module `models/tabular_expert.py` | ✅ Hoàn thành |
| 3.2 | Script huấn luyện với Logistic Regression và Random Forest | ✅ Hoàn thành |
| 3.3 | Kiểm tra tính toàn vẹn pipeline (train/test split) | ✅ Scaffold hoàn thành (xem mục 5) |
| 4.1 | Late Fusion đơn giản (Simple Average) | ✅ Scaffold hoàn thành |
| 4.2 | Metrics cơ bản: ROC-AUC, Sensitivity, Specificity | ✅ Scaffold hoàn thành |
| 4.3 | Báo cáo tiến độ tuần 1 | ✅ File này |

---

## 2. Mô tả kỹ thuật những gì đã xây dựng

### 2.1 Data Pipeline (`core/`, `config/`)

Xây dựng pipeline chuyển đổi dữ liệu bệnh nhân từ dict thô sang DataFrame phẳng,
gồm các thành phần:

- **`config/schema_config.py`**: Định nghĩa danh sách feature theo từng modality
  (Clinical, Biochemical, Ultrasound, MRI) và ngưỡng completeness (`MISSING_THRESHOLD`).
  Thứ tự feature trong schema là **cố định** — feature mask phụ thuộc thứ tự này.

- **`core/missing_utils.py`**: Tính `feature_mask` (0/1 cho từng feature) và
  `modality_available` (1 nếu tỷ lệ missing ≤ ngưỡng, 0 nếu ngược lại).

- **`core/sample_builder.py`**: Tạo cấu trúc sample hoàn chỉnh cho 1 bệnh nhân,
  gồm các khối modality và ground truth.

- **`core/dataset_builder.py`**: Chuyển list sample → DataFrame phẳng.

### 2.2 Tabular Expert (`models/tabular_expert.py`)

Class `TabularExpert` hỗ trợ 2 loại mô hình (chọn qua `model_type`):

| model_type | Mô hình | Đặc điểm |
|---|---|---|
| `"logistic"` | Logistic Regression | Tuyến tính, dễ giải thích |
| `"random_forest"` | Random Forest (100 cây) | Phi tuyến, chịu đựng tốt với nhiều missing |

Pipeline của cả 2: `SimpleImputer(median)` → Classifier.

> **Lưu ý quan trọng (để dùng sau):** `SimpleImputer(median)` đang được dùng tạm
> cho bước học (Logistic Regression → Random Forest). Khi nâng lên LightGBM (bước
> tiếp theo), **bắt buộc bỏ SimpleImputer** và dùng native NaN handling của LightGBM
> — vì median imputation thay đổi phân phối dữ liệu, làm mất đi tín hiệu "feature
> này bị missing" mà LightGBM có thể khai thác trực tiếp.

Tích hợp kiểm tra tường minh: nếu SimpleImputer xóa cột (vì toàn NaN),
code sẽ in cảnh báo rõ với danh sách tên cột — không chỉ dựa vào
`UserWarning` ngầm của sklearn.

### 2.3 Script huấn luyện (`scripts/train_tabular_expert.py`)

Script hiện thực hiện đủ các bước:
1. Load data → lọc mẫu hợp lệ → tách X, y
2. Huấn luyện và so sánh Logistic Regression vs Random Forest
3. Tính AUC, Sensitivity, Specificity (scaffold)
4. Late Fusion (Simple Average) với slot sẵn cho Ultrasound Expert và MRI Expert

---

## 3. Nguyên tắc chống Data Leakage — Đã áp dụng

Đây là nguyên tắc bắt buộc trong mọi bài toán dự đoán y tế:

| Nguyên tắc | Áp dụng |
|---|---|
| **Predictor chỉ dùng data trước phẫu thuật** | ✅ Clinical, Biochemical, Ultrasound, MRI đều là data tiền phẫu |
| **Ground Truth = GPB sau mổ** | ✅ Không dùng sinh thiết lạnh trong mổ, không dùng kết luận MRI/SA |
| **Không để label ảnh hưởng ngược vào feature** | ✅ Label lưu riêng trong `sample["label"]`, không join vào X |

---

## 4. Trích xuất thông tin từ báo cáo y tế (Mục 2.1 – 2.2)

Hiện tại đang thực hiện **thủ công** cho từng bệnh nhân:
bác sĩ đọc báo cáo SA/MRI → điền vào file Python chuẩn hóa (`data/real/case_XX.py`).

Ví dụ: `data/real/case_01.py` — bệnh nhân thật đầu tiên đã được nhập thủ công.

> **Hướng phát triển (tuần 2 trở đi):** Xây dựng module NLP/Rules tự động
> trích xuất giá trị số từ văn bản báo cáo (ví dụ: "CA125: 300 U/mL") thành
> structured dict — thay thế bước nhập tay.

---

## 5. Giới hạn và điều kiện hiện tại

> [!IMPORTANT]
> Hiện chỉ có **1 bệnh nhân thật** đã được nhập vào hệ thống (`case_01`).
> Mọi con số metrics (AUC, Sensitivity, Specificity) in ra trong script đều
> là **scaffold chạy thử** — xác nhận code tính đúng công thức, không phải
> kết quả đánh giá mô hình.
>
> Để đánh giá mô hình có ý nghĩa, cần:
> - Ít nhất **30 case thật** để chia train/test cơ bản.
> - Hoặc dùng **Leave-One-Out Cross-Validation (LOOCV)** khi có dataset nhỏ
>   (< 50 case) — phù hợp nhất với điều kiện y tế thực tế.

**Vấn đề kỹ thuật đã phát hiện (trung thực):**

- **3 cột biochemical bị xóa** do toàn NaN trong data hiện có:
  `biochemical_HE4`, `biochemical_AFP`, `biochemical_ROMA`.
  → Nguyên nhân: case_01 không có giá trị cho 3 xét nghiệm này.
  → Cách xử lý: đã thêm cảnh báo tường minh; sẽ tự động giữ lại khi có data thật.

- **Ngưỡng completeness Ultrasound (25%)** chưa được bác sĩ xác nhận chính thức.
  → Hiện đặt tạm 25% tương tự MRI.

- **valid_mask dùng OR** giữa `clinical_available` và `biochemical_available`
  là tạm thời — chưa phù hợp hoàn toàn với kiến trúc long-term.
  → Đã ghi vào Decision Log và TODO.

---

## 6. Kế hoạch Tuần 2

| Ưu tiên | Việc cần làm | Lý do |
|---|---|---|
| 🔴 Cao nhất | Nhập data 11 bệnh nhân thật còn lại từ bệnh viện | Cần data thật trước khi nâng cấp model |
| 🔴 Cao nhất | Thay Logistic/RF bằng **LightGBM** + bỏ SimpleImputer | Bước 3/4 trong lộ trình, gần nhất với paper |
| 🟡 Trung bình | Áp dụng **LOOCV** khi có đủ data | Đánh giá mô hình đúng với dataset nhỏ |
| 🟡 Trung bình | Bắt đầu module NLP extraction từ báo cáo SA/MRI | Giảm công nhập tay, hướng tới scale |
| 🟢 Thấp | Đọc code OvcaFinder (có GitHub) để tham khảo kiến trúc multimodal | Học từ code thật, không reinvent the wheel |

---

*File này được tạo tự động từ kết quả thực tế của tuần 1.  
Mọi thông tin đều phản ánh đúng trạng thái code và data hiện có — không ước tính hay chế thêm.*
