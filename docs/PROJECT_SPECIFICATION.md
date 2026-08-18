# Đặc tả Kiến trúc & Quy chuẩn Kỹ thuật Dự án AI Y Khoa

**Tên đề tài:** Dự báo nguy cơ ung thư khối u buồng trứng trước phẫu thuật  
**Mục tiêu hệ thống:** Tích hợp dữ liệu đa phương thức (Multimodal AI) trước phẫu thuật để phân loại ca bệnh thành Cancer (`y=1`) hoặc Non-cancer (`y=0`).

---

## 1. Nguyên tắc Ground Truth & Chống Rò Rỉ Dữ Liệu (Data Leakage)

* **Ground Truth duy nhất:** Kết quả Giải Phẫu Bệnh (GPB) mô bệnh học sau phẫu thuật (`0 = non-cancer`, `1 = cancer`).
* **Tuyệt đối KHÔNG sử dụng làm Ground Truth:** Kết luận siêu âm, kết luận MRI, phân loại IOTA/ADNEX, chẩn đoán lâm sàng trước mổ hay kết quả sinh thiết lạnh.
* **Quy tắc Chống Rò Rỉ (Data Leakage):**
  * Chỉ các thông tin thu thập **trước phẫu thuật** mới được làm predictor (đầu vào của model).
  * Không dùng các xác suất phân loại ADNEX để điền ngược vào dữ liệu siêu âm ban đầu.

---

## 2. Kiến trúc Hệ thống (Multimodal Architecture)

```text
Raw Hospital Data (Reports, Images, Labs)
                  ↓
       Information Extraction
                  ↓
Structured Features + Feature-level Missing Mask
                  ↓
    Modality Completeness Check (Threshold)
       /                             \
     Có                              Không
      ↓                                ↓
Expert Model Chạy                 Expert Model Skip
(P_cancer, Available=1)           (Available=0)
       \                             /
        └──────────────┬────────────┘
                       ↓
                  Late Fusion
        (Simple Avg → Weighted Avg → NN)
                       ↓
                 Final P(cancer)
                       ↓
          Validation Threshold Selection
         (Dựa trên Sensitivity/Specificity)
                       ↓
                Cancer / Non-cancer
```

---

## 3. Quy chuẩn Xử lý Dữ liệu Thiếu (Missing Data Protocol)

1. **Tuyệt đối `missing != 0`:** Không biến các chỉ số thiếu thành 0.
2. **Feature-level Mask:** Mỗi modality lưu song song mảng giá trị và mảng mask (`0 = missing`, `1 = có dữ liệu`).
3. **Modality Completeness Threshold:**
   * Ngưỡng thiếu tối đa quy định theo protocol (ví dụ: Clinical: 0%, Biochemical: 30%, Ultrasound: 25%, MRI: 25%).
   * Nếu tỷ lệ missing vượt quá ngưỡng $\rightarrow$ Modality bị coi là `unavailable` $\rightarrow$ Skip Expert tương ứng.
4. **Late Fusion trên Expert khả dụng:** Fusion chỉ tính toán dựa trên các Expert có `available = 1` và renormalize trọng số tương ứng.

---

## 4. Quy trình Lựa chọn Ngưỡng (Threshold Selection) & Calibration

* **Calibration:** Xác suất thô từ các Expert phải qua bước hiệu chỉnh (Calibration) để phản ánh đúng xác suất thực tế trước khi đưa vào Fusion.
* **Ngưỡng quyết định (Threshold):**
  * KHÔNG mặc định $0.5$ hay $0.6$.
  * Ngưỡng được lựa chọn dựa trên tập **Validation**, đáp ứng yêu cầu lâm sàng của bác sĩ (ví dụ: $\text{Sensitivity} \ge 95\%$).
  * KHÔNG tối ưu ngưỡng trên tập Test.

---

## 5. Cấu trúc Thư mục Dự án

```text
ovarian/
├── config/
│   └── schema_config.py      # Định nghĩa Schema, Feature List & Missing Thresholds
├── core/
│   ├── missing_utils.py       # Logic xử lý Feature Mask & Modality Availability
│   ├── sample_builder.py     # Build sample bệnh nhân đa phương thức
│   └── dataset_builder.py    # Flatten sample thành DataFrame
├── data/
│   ├── mock/                 # Mock samples cho testing
│   └── real/                 # Dữ liệu thật từng bệnh nhân (mỗi file 1 case)
├── docs/
│   ├── PROJECT_SPECIFICATION.md  # Tài liệu đặc tả kỹ thuật này
│   └── WEEKLY_PLAN_WEEK_01.md    # Checklist tiến độ theo tuần
├── models/                   # Các mô hình chuyên biệt (Tabular Expert, Imaging Expert...)
├── scripts/                  # Scripts chạy pipeline & training
└── requirements.txt
```
