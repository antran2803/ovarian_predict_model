# Ovarian AI Learning Project

Project này dùng để học cách code machine learning từng bước, sau đó tái hiện và áp dụng các mô hình đã có trong paper về chẩn đoán u/bướu buồng trứng trước phẫu thuật.

Hướng đi chính hiện tại:

- Không xây model từ đầu theo cảm tính.
- Học và hiểu pipeline dữ liệu trước.
- Đọc paper phù hợp, bóc kiến trúc, rồi code lại theo từng phần nhỏ.
- Áp dụng model lên dữ liệu bệnh viện khi có thêm case thật.

---

## Cấu trúc thư mục

```text
ovarian/
├── config/
│   └── schema_config.py          # Định nghĩa Schema: danh sách cột & ngưỡng missing của từng modality
├── core/
│   ├── missing_utils.py          # Tính toán feature_mask và completeness
│   ├── sample_builder.py         # Tạo dict dữ liệu bệnh nhân & tính flag completeness (_available)
│   └── dataset_builder.py        # Gộp danh sách bệnh nhân thành DataFrame chuẩn hóa
├── data/
│   ├── mock/
│   │   └── mock_samples.py       # Dữ liệu mock (dùng test edge cases pipeline)
│   └── real/
│       └── case_01.py            # Dữ liệu thật từ bệnh viện (mỗi bệnh nhân 1 file)
├── models/
│   └── tabular_expert.py         # Tabular Expert Model (Logistic Regression & Random Forest)
├── scripts/
│   ├── build_dataset.py          # Script kiểm tra pipeline dữ liệu
│   └── train_tabular_expert.py   # Script train & đánh giá mô hình Tabular Expert
├── docs/
│   ├── du_lieu_benh_nhan_ubt.xlsx # Dữ liệu bệnh nhân & Data Dictionary
│   ├── WEEKLY_PLAN_WEEK_01.md    # Kế hoạch tuần 1
│   └── PROGRESS_REPORT_WEEK01.md # Báo cáo tiến độ tuần 1
├── requirements.txt
├── README.md
```

---

## Ý nghĩa từng phần

- `config/`: Nơi duy nhất định nghĩa schema chung (Schema v2): modality nào có những feature nào, thứ tự feature ra sao, và ngưỡng missing cho từng modality.
- `core/`: Chứa logic thuần không phụ thuộc mô hình:
  - Tính feature mask
  - Tính modality có đủ dùng hay không (`_available`)
  - Build sample cho từng bệnh nhân
  - Flatten sample thành DataFrame để train model
- `data/mock/`: Chứa dữ liệu giả (15 ca edge cases) để test pipeline không lỗi.
- `data/real/`: Chứa dữ liệu thật, mỗi bệnh nhân nằm trong 1 file riêng để dễ trace, audit và sửa lại sau khi bác sĩ xác nhận.
- `models/`: Chứa các mô hình chuyên gia (hiện có `tabular_expert.py`).
- `scripts/`: Nơi lắp ráp pipeline để chạy ra kết quả cuối.
- `docs/`: Nơi lưu trữ tài liệu dữ liệu bệnh viện và báo cáo tiến độ.

---

## Quy trình chạy (Workflow & Commands)

Kích hoạt môi trường ảo:

```powershell
.\venv\Scripts\Activate.ps1
```

Cài đặt các gói phụ thuộc:

```powershell
python -m pip install -r requirements.txt
```

### 1. Kiểm tra Pipeline Dataset (`scripts/build_dataset.py`)
Load tất cả dữ liệu bệnh nhân (mock + real), kiểm tra tính đầy đủ của thuộc tính và xuất bảng thông tin DataFrame:

```powershell
python scripts\build_dataset.py
```

### 2. Huấn luyện & Đánh giá Tabular Expert (`scripts/train_tabular_expert.py`)

```powershell
python scripts\train_tabular_expert.py
```

---

*Lưu ý: Mọi ghi chép chi tiết về lộ trình, nhật ký quyết định (Decision Log), ghi chú y khoa và CHANGELOG được theo dõi tập trung tại [`AI_CONTINUATION.md`](file:///d:/project/ovarian/AI_CONTINUATION.md).*
