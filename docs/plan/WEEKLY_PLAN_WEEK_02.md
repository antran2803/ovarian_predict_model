# Kế hoạch & Checklist Tiến độ - Tuần 2

**Dự án:** Hệ thống AI dự báo nguy cơ ung thư khối u buồng trứng trước phẫu thuật  
**Đơn vị phối hợp:** Trường Đại học Y Dược / Bệnh viện Từ Dũ  
**Mục tiêu tuần 2:** Xây dựng pipeline tự động đọc và trích xuất dữ liệu từ ảnh phiếu y tế in máy (12 ca, 92 ảnh trong `sample_data/`) bằng **PaddleOCR offline + rule/regex Python**. Sau đó hoàn thiện 2 Expert Models còn lại (Ultrasound Expert & MRI Expert) và chạy LOOCV.

> **Quyết định kỹ thuật đã chốt (2026-08-16):**
> * **OCR Engine**: PaddleOCR (offline, miễn phí, không giới hạn lần chạy, không cần API key).
> * **Lý do**: Toàn bộ 12 ca phiếu đều là chữ in máy (không có phần data quan trọng nào là chữ viết tay). PaddleOCR xử lý tốt phiếu in tiếng Việt.
> * **Trích xuất**: Rule-based / Regex Python sau khi có text thô từ OCR — khớp tên biến theo `schema_config.py`.
> * **Kiểm chứng kết quả**: Do **người dùng kiểm tra thủ công** sau mỗi ca test, không cần tự động hóa bước so khớp.

---

## 📋 Checklist Tiến độ Tuần 2 (Báo cáo Người hướng dẫn)

### 1. OCR & Trích xuất Dữ liệu từ Ảnh Phiếu Y tế (Thứ 2 - Thứ 3)
- [x] **Thứ 2 (1.1 - 1.3): Cài đặt & Viết Parser cơ bản** *(Hoàn thành 2026-08-18)*
  * Cài đặt PaddleOCR offline trong venv, chạy thử trên ảnh mẫu (`1-marker.jpg`).
  * Xây dựng `scripts/extract_from_images.py` phân loại phiếu theo tên file (`BA`, `marker`, `SA`, `MRI`, `GPB`).
  * Viết parser rule/regex cho 4 loại phiếu: `marker_parser` (CA125, HE4, AFP, beta_hCG, ROMA), `sa_parser` (kích thước, Doppler, dịch ổ bụng...), `mri_parser` (O-RADS, TIC, DWI/ADC...), `ba_parser` (tuổi, tiền sử...).
- [x] **Thứ 3 (1.4): Chạy thử & Tinh chỉnh trên `case_01`** *(Hoàn thành 2026-08-18)*
  * Chạy pipeline trên 8 ảnh của `sample_data/1-*.*`.
  * Khắc phục 5 điểm hạn chế: Header Routing, Negation check per-line, xóa default hardcode, mở rộng từ điển y khoa, xuất CSV kiểm chứng.
  * Xuất file dữ liệu chuẩn hóa `data/real/case_01.py` và bảng đối chiếu `results/extracted_case_01.csv`.
  * Kiểm chứng thủ công, tinh chỉnh regex/rule parser nếu phát hiện sai lệch.

### 2. Trích xuất Hàng loạt & Ultrasound Expert (Thứ 4)
- [ ] **Thứ 4 (1.5 + 2.1 - 2.3): Chạy Hàng loạt 12 Ca & Xây dựng Ultrasound Expert**
  * Chạy pipeline OCR tự động trích xuất toàn bộ 12 ca (`case_01.py` đến `case_12.py`) trong `sample_data/`.
  * Refactor cấu trúc mô hình: gom phần khung lõi huấn luyện (Logistic, Random Forest, LightGBM) thành base class dùng chung để tránh trùng lặp code.
  * Xây dựng `models/ultrasound_expert.py` (kế thừa/tái sử dụng base class) chuyên biệt cho 14 biến IOTA.

### 3. MRI Expert & Kiểm tra Độ đầy đủ Dữ liệu Thật (Thứ 5)
- [ ] **Thứ 5 (3.1 - 3.3): Xây dựng MRI Expert & Lọc Ca Đủ Điều Kiện**
  * Xây dựng `models/mri_expert.py` (tái sử dụng base class) cho 8 biến O-RADS MRI.
  * Thống kê, kiểm tra số lượng ca thật đủ điều kiện cho từng modality (theo ngưỡng missing 30% cho tabular, 25% cho US/MRI).

### 4. Đánh giá Độc lập 3 Expert qua LOOCV & Báo cáo (Thứ 6 - Chủ Nhật)
- [ ] **Thứ 6 (4.1 - 4.2): Chạy LOOCV cho cả 3 Expert Models**
  * Nâng cấp `scripts/evaluate_loocv.py` chạy LOOCV độc lập cho cả 3 nhánh ($P_{loocv\_tabular}, P_{loocv\_us}, P_{loocv\_mri}$).
  * Xuất bảng xác suất đầy đủ ra `results/loocv_results.csv`.
- [ ] **Thứ 7 - Chủ Nhật (4.3): Buffer & Báo cáo Tiến độ Tuần 2**
  * Dành thời gian đệm (buffer) để tinh chỉnh nếu có khâu bị trễ.
  * Viết báo cáo tiến độ tuần 2 (`docs/BAO_CAO_TIEN_DO_TUAN_02.md`) gửi Giảng viên/Người hướng dẫn, chốt hạ toàn bộ các Expert đơn lẻ để Tuần 3 tập trung 100% vào Multimodal Late Fusion.

---

## 🎯 Mục tiêu đầu ra của Tuần 2 (Deliverables)
1. **Dữ liệu thật trích xuất:** Bộ dữ liệu ca bệnh thật được trích xuất và đối chiếu trực tiếp từ ảnh y tế `sample_data/`.
2. **Mã nguồn 3 Expert Models hoàn chỉnh:**
   * [`models/tabular_expert.py`](file:///d:/project/ovarian/models/tabular_expert.py)
   * `models/ultrasound_expert.py`
   * `models/mri_expert.py`
3. **Kết quả LOOCV Đa Expert:** File `results/loocv_results.csv` chứa đầy đủ các cột xác suất độc lập ($P_{tabular}, P_{us}, P_{mri}$).
4. **Báo cáo Tiến độ Tuần 2:** Bản báo cáo tóm tắt tiến độ và các phát hiện lâm sàng.
