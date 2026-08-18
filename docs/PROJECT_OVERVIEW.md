# Tài liệu Tổng quan Project: Ovarian Cancer Prediction System
---

## 1. Mục tiêu Project

Xây dựng hệ thống **hỗ trợ phân loại nguy cơ u buồng trứng** (Ung thư / Không ung thư) từ dữ liệu đa phương thức (multimodal), kết hợp:
- Dữ liệu **lâm sàng + sinh hóa** (tuổi, CA-125, HE4, v.v.)
- Dữ liệu **siêu âm** (IOTA protocol)
- Dữ liệu **MRI** (O-RADS protocol)

Tiêu chuẩn vàng (ground truth): **Kết quả giải phẫu bệnh sau mổ**.

---

## 2. Nguồn tham khảo & Lý do

### Bài báo gốc: Kunishima et al., 2025
- **Tên**: Multimodal Machine Learning for Ovarian Tumor Classification
- **Tại sao**: Đây là paper đầu tiên đề xuất kiến trúc **Late Fusion đa phương thức** (siêu âm + MRI + lâm sàng) cho bài toán phân loại u buồng trứng — phù hợp với quy trình lâm sàng thực tế tại Việt Nam.
- **Ứng dụng**: Lộ trình model, ý tưởng TabularExpert, Late Fusion, và phương pháp đánh giá LOOCV.

### Hướng dẫn nghiên cứu chính thức (docs/research)
- 11 ảnh tài liệu từ nghiên cứu chính thức tại bệnh viện (Việt Nam)
- **Dùng làm nguồn quyết định** cho: danh sách biến, mã hóa giá trị, ngưỡng missing, tiêu chuẩn loại trừ.

### Hệ thống phân loại chuẩn
| Hệ thống | Dùng cho | Lý do |
|---|---|---|
| **IOTA ADNEX** | Siêu âm | Tiêu chuẩn quốc tế phân loại u phụ khoa qua SA |
| **O-RADS MRI** | MRI | Tiêu chuẩn phân tầng nguy cơ ác tính trên MRI |
| **CA-125, HE4, ROMA** | Sinh hóa | Marker ung thư buồng trứng được dùng rộng rãi |

---

## 3. Công nghệ sử dụng

### Ngôn ngữ & Thư viện
| Thứ | Công cụ | Mục đích |
|---|---|---|
| Python 3.x | — | Ngôn ngữ chính |
| scikit-learn | Logistic Regression, Random Forest, LeaveOneOut (LOOCV) |
| LightGBM | Model chính — native NaN + categorical handling |
| pandas | Xử lý DataFrame phẳng |
| numpy | Tính toán số học |

### Tại sao LightGBM là model chính?
1. **Native NaN Handling**: Không cần impute thủ công — tự học hướng phân nhánh tối ưu cho giá trị thiếu.
2. **Native Categorical**: Xử lý trực tiếp cột category không cần one-hot encoding.
3. **Hiệu quả trên dataset nhỏ**: Với `min_child_samples=1`, hoạt động được ngay cả khi N < 20.
4. **class_weight='balanced'**: Tự động ưu tiên Sensitivity — tránh bỏ sót ca ung thư.

---

## 4. Cấu trúc Project

```
d:\project\ovarian\
│
├── config/
│   └── schema_config.py      
│
├── core/
│   ├── sample_builder.py      
│   ├── dataset_builder.py      
│   └── missing_utils.py        
│
├── models/
│   ├── tabular_expert.py       <- dùng để so sánh các thuật toán
│   └── late_fusion.py          
│
├── data/
│   ├── mock/mock_samples.py    ← 15 ca giả lập để test pipeline
│   └── real/case_01.py         ← 1 ca thật từ hồ sơ bệnh án
│
├── scripts/
│   ├── train_tabular_expert.py ← So sánh 3 model (demo, train=test)
│   ├── evaluate_loocv.py       ← LOOCV đúng phương pháp luận
│   └── evaluate_late_fusion.py ← Fusion logic
│
├── results/
│   ├── loocv_results.csv       ← P(cancer) LOOCV từng ca
│   └── tabular_expert_results.csv
│
└── docs/
    ├── research/         
    └── WEEKLY_PLAN_WEEK_01.md  <- Lên Plan cho tuần 1
```

---

## 5. Luồng hoạt động tổng quát

```
┌──────────────────────────────────────────────────────────────────┐
│                     DỮ LIỆU ĐẦU VÀO                             │
│  (hồ sơ bệnh án: phiếu SA, kết quả MRI, xét nghiệm, lâm sàng)  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                   ┌────────────▼────────────┐
                   │    schema_config.py     │ Định nghĩa 3 nhóm modality:
                   │    (source of truth)    │ tabular / ultrasound / mri
                   └────────────┬────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
  ┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
  │  TABULAR      │   │  ULTRASOUND     │   │  MRI            │
  │  14 biến      │   │  14 biến IOTA   │   │  8 biến O-RADS  │
  │  (lâm sàng    │   │  (hình thái,    │   │  (TIC, DWI/ADC, │
  │  + sinh hóa)  │   │  Doppler, ...)  │   │  O-RADS score)  │
  └───────┬───────┘   └────────┬────────┘   └────────┬────────┘
          │                    │                      │
          ▼              (tuần 2+)              (tuần 2+)
  ┌───────────────┐            │                      │
  │ TabularExpert │            │                      │
  │ LightGBM      │            │                      │
  │ + LOOCV       │            │                      │
  │               │            │                      │
  │ → P_tabular   │            │                      │
  └───────┬───────┘            │                      │
          │                    │                      │
          └────────────────────┼──────────────────────┘
                               ▼
                  ┌────────────────────────┐
                  │      LATE FUSION       │
                  │  P_fusion = Σ wᵢ × Pᵢ │
                  │  (weighted average)    │
                  └────────────┬───────────┘
                               │
                  ┌────────────▼───────────┐
                  │   KẾT QUẢ ĐẦU RA      │
                  │   P(cancer) ∈ [0,1]   │
                  │   → Cancer /           │
                  │     Non-cancer         │
                  └────────────────────────┘
```

---

## 6. Nhóm dữ liệu & Mã hóa

### 6.1 Tabular (14 biến — ngưỡng missing 30%)
*Một nhóm thống nhất theo mục 2.5.1.1 & 2.3.4.1 tài liệu nghiên cứu*

| Biến | Kiểu | Mã hóa |
|---|---|---|
| `age` | int | Tuổi năm |
| `menopause` | binary | 0=chưa mãn kinh, 1=đã mãn kinh |
| `pregnancy_status` | binary | 0/1 |
| `bilateral_lesion` | binary | 0=1 bên, 1=2 bên |
| `months_detection_to_surgery` | float | Số tháng |
| `prior_ovarian_surgery` | ordinal 0-3 | 0=không có; 1=có/không rõ GPB; 2=lành tính; 3=giáp biên ác |
| `other_cancer_history` | binary | 0/1 |
| `other_cancer_primary_site` | str | Text phụ trợ (không phải ML feature) |
| `oncology_center_flag` | binary | 0/1 |
| `CA125` | float (U/mL) | Marker sinh hóa |
| `HE4` | float (pmol/L) | Marker sinh hóa |
| `AFP` | float (ng/mL) | Marker sinh hóa |
| `beta_hCG` | float (mIU/mL) | Marker sinh hóa |
| `ROMA` | float (%) | Chỉ số tổng hợp CA125+HE4 |

### 6.2 Ultrasound (14 biến — ngưỡng missing 25% tạm đặt - Trong tài liệu thì ghi ko có là ko tính)
8 biến IOTA bắt buộc + 6 biến mở rộng. Doppler ordinal 1-4, morphology_class category 1-7.

### 6.3 MRI (8 biến — ngưỡng missing 25% tạm đặt -Trong tài liệu thì ghi ko có là ko tính)
TIC ordinal 0/1/2 (Type1/2/3), o_rads_mri ordinal 0-4 (ORADS1-5), restricted_diffusion binary.

---

## 7. Dữ liệu dùng hiện tại

### Mock data (15 ca — chỉ để test code)
- File: [`data/mock/mock_samples.py`](file:///d:/project/ovarian/data/mock/mock_samples.py)
- Bao gồm đủ edge case: thiếu modality, thiếu sinh hóa, toàn None...
- **Chỉ mang tính chất tham khảo thui :))**

### Real case (1 ca thật)
- File: [`data/real/case_01.py`](file:///d:/project/ovarian/data/real/case_01.py)
- Nguồn: Hồ sơ bệnh án thật (8 ảnh)
- GPB: Carcinoma tuyến dịch nhầy giai đoạn IA → label=1 (Cancer)
- 5 biến sinh hóa đều None (không có phiếu XN trong hồ sơ)

---

## 8. Kết quả đầu ra hiện tại

### LOOCV trên mock (N=12, chỉ để kiểm tra code):

| Model | ROC-AUC | Sensitivity @0.5 | Specificity @0.5 |
|---|---|---|---|
| Logistic | 0.7143 | 60% (3/5) | 57.1% (4/7) |
| Random Forest | 0.8429 | 80% (4/5) | 100% (7/7) |
| **LightGBM** | **0.8571** | **80% (4/5)** | **71.4% (5/7)** |

> ROC-AUC là chỉ số duy nhất đáng tin cậy (không phụ thuộc threshold).  
> Sensitivity/Specificity tính tại threshold=0.5 (demo, chưa tối ưu).

---

## 9. Lộ trình 

| Tuần | Trạng thái | Nội dung |
|---|---|---|
| **Tuần 1** | ✅ HOÀN THÀNH | TabularExpert (3 model) + LOOCV + LateFusion scaffold + Schema alignment với tài liệu nghiên cứu |

