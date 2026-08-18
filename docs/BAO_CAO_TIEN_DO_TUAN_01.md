# Báo cáo Tiến độ Tuần 1 — Gửi Giảng viên Hướng dẫn


Kính gửi Thầy/Cô,

Em xin báo cáo tiến độ tuần đầu tiên thực hiện đề tài nghiên cứu hệ thống AI hỗ trợ chẩn đoán khối u buồng trứng trước phẫu thuật (phối hợp BV Từ Dũ):

---

## 1. Các công việc em đã hoàn thành trong Tuần 1:

Em tập trung hoàn thiện **nền tảng xử lý dữ liệu đa phương thức và xây dựng các mô hình cơ sở** — đảm bảo toàn bộ pipeline chạy đúng logic và phương pháp luận trước khi đưa dữ liệu bệnh nhân thực tế vào:

1. **Chuẩn hóa cấu trúc dữ liệu đa phương thức (Multimodal Data Pipeline):**
   - Đã định nghĩa Schema đồng nhất cho 4 nhóm: Lâm sàng, Sinh hóa (CA-125, HE4, AFP, β-hCG, ROMA), Siêu âm (8 biến IOTA) và MRI.
   - Cài đặt cơ chế kiểm soát dữ liệu thiếu nghiêm ngặt: **giữ nguyên `NaN` (`missing != 0`)** và tính toán độ hoàn thiện (`completeness`) theo từng modality.

2. **Huấn luyện & So sánh các mô hình Tabular Expert (Lâm sàng + Sinh hóa):**
   - Xây dựng và so sánh song song 3 mô hình trên tập 15 ca mô phỏng (bao gồm nhiều ca biên khó như CA-125 cực cao nhưng lành tính, hoặc CA-125 bình thường nhưng ác tính):
     + **Logistic Regression** (baseline tuyến tính)
     + **Random Forest** (ensemble dạng cây)
     + **LightGBM** (mô hình tối ưu nhất theo bài báo tham khảo *Kunishima et al., Sci Rep 2025* — sử dụng cơ chế Native Missing Handling và Native Categorical Support).

3. **Thiết lập quy trình đánh giá chuẩn cho cỡ mẫu nhỏ (LOOCV):**
   - Áp dụng **Leave-One-Out Cross-Validation (LOOCV)** — tiêu chuẩn học thuật cho dữ liệu y tế cỡ mẫu nhỏ ($N < 30$), đảm bảo mỗi ca được dự đoán bởi mô hình hoàn toàn chưa nhìn thấy ca đó lúc huấn luyện (tránh tình trạng học thuộc đề / train=test).
   - Kết quả thử nghiệm trên tập mock 10 ca hợp lệ:
     + **Logistic Regression**: ROC-AUC = 0.56 | Sensitivity @0.5 = 60.0% (3/5) | Specificity @0.5 = 40.0% (2/5)
     + **Random Forest**: ROC-AUC = 0.88 | Sensitivity @0.5 = 80.0% (4/5) | Specificity @0.5 = 80.0% (4/5)
     + **LightGBM**: ROC-AUC = 1.00 | Sensitivity @0.5 = 80.0% (4/5) | Specificity @0.5 = 100.0% (5/5)
   - *(Lưu ý: Các chỉ số trên tập mock chỉ nhằm mục đích chứng minh code chạy đúng phương pháp luận, không phản ánh hiệu năng lâm sàng thực tế).*

4. **Xây dựng khung tích hợp Late Fusion Scaffold:**
   - Xây dựng module `LateFusion` sẵn sàng tiếp nhận và tổng hợp xác suất từ các Expert độc lập (Tabular, US, MRI).

---

## 2. Kế hoạch tiếp theo cho Tuần 2:

- **Nạp dữ liệu 11 ca bệnh nhân thật còn lại** từ file Excel của BV Từ Dũ (`case_02.py` đến `case_12.py`).
- **Thiết kế luồng trích xuất dữ liệu (Information Extraction)** từ các đoạn text mô tả kết quả siêu âm/MRI của bác sĩ sang các biến IOTA / O-RADS có cấu trúc.
- **Chạy đánh giá LOOCV & Late Fusion trực tiếp trên tập dữ liệu bệnh viện thực tế**.

---

## 3. Em xin ý kiến Thầy/Cô về một số định hướng:

1. **Về quy trình tổng thể**: Pipeline từ Dữ liệu $\rightarrow$ Tabular Expert (LightGBM) $\rightarrow$ LOOCV $\rightarrow$ Late Fusion như trên đã phù hợp với định hướng nghiên cứu chưa ạ?
2. **Về chỉ số đánh giá & ngưỡng chẩn đoán**: Trong bài báo tham khảo dùng ngưỡng mặc định $P = 0.5$, nhưng trong thực tế lâm sàng tại BV Từ Dũ, Thầy/Cô có khuyến nghị ưu tiên hạ ngưỡng (ví dụ $0.3 - 0.4$) để tối đa hóa Độ nhạy (Sensitivity - tránh bỏ sót ác tính) không ạ?
3. **Về các chỉ số sinh hóa**: Trong bài báo của Nhật, chỉ số **LDH** có tầm quan trọng rất cao; em muốn hỏi thêm tại bệnh viện mình thì xét nghiệm LDH có được làm thường quy cho các ca u buồng trứng không ạ?

---

Em xin cảm ơn Thầy/Cô rất nhiều ạ!
