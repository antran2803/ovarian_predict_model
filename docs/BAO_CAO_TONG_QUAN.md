# Báo cáo Tuần 2

## 1) Mục tiêu của báo cáo tuần này

1. Làm rõ cách tổ chức hệ thống thành 3 mô hình chuyên gia: Tabular, Ultrasound và MRI.
2. Tập trung trình bày thêm hai Expert mới được hoàn thiện trong tuần này là Ultrasound Expert và MRI Expert.
3. Kiểm tra rằng từng Expert có thể huấn luyện và dự báo độc lập trên dữ liệu thật hiện có.
4. Đánh giá thử bằng LOOCV để biết pipeline đã chạy đúng về mặt kỹ thuật hay chưa.
5. Thử kết nối đầu ra xác suất của các Expert ở bước Late Fusion, nhưng chỉ xem đây là baseline kỹ thuật vì dữ liệu hiện còn ít.

-> Mục tiêu chính của tuần này là để mỗi Expert đọc đúng nhóm dữ liệu của mình, có thể tạo xác suất ung thư, và có thể chuẩn bị cho bước fusion khi có nhiều dữ liệu hơn.

---

## 2) Cách thức mô hình tổ chức

Hệ thống gồm 3 mô hình chuyên gia (Expert), mỗi Expert nhìn một nhóm dữ liệu riêng:

1. Tabular Expert
- Nhìn nhóm lâm sàng + sinh hóa.
- Tổng 14 biến.

2. Ultrasound Expert
- Nhìn nhóm siêu âm IOTA.
- Tổng 14 biến.

3. MRI Expert
- Nhìn nhóm MRI O-RADS.
- Tổng 8 biến.

Ba Expert này chạy độc lập, sau đó mới tổng hợp ở bước cuối cùnh là Late Fusion.

---

## 3) Tổng quan

### 3.1. Ba Expert dùng chung một khung BaseExpert

Trong hệ thống hiện tại, ba Expert được thiết kế theo cùng một cấu trúc chung thông qua lớp `BaseExpert`. 
Mục đích của `BaseExpert` là gom các bước xử lý giống nhau của các Expert vào một khung chung, bao gồm xử lý dữ liệu thiếu, huấn luyện mô hình, dự báo xác suất và kiểm tra đầu vào.

Điểm khác nhau giữa các Expert chủ yếu nằm ở nhóm biến đầu vào: 
+ Tabular Expert sử dụng biến lâm sàng và sinh hóa
+ Ultrasound Expert sử dụng biến siêu âm
+ MRI Expert sử dụng biến MRI. 

Sau khi nhận đúng nhóm biến của mình, cả ba Expert đều đi qua cùng một quy trình xử lý trong `BaseExpert`.

Vai trò của từng Expert trong giai đoạn hiện tại như sau:

- **Tabular Expert:** sử dụng nhóm thông tin lâm sàng và sinh hóa trước mổ, gồm 14 biến, để ước lượng xác suất một ca thuộc nhóm ung thư. (Đã có trong tuần trước)
- **Ultrasound Expert:** sử dụng 14 biến từ phiếu siêu âm theo IOTA, bao gồm kích thước khối u, thành phần đặc, chồi nhú, thành/vách, dịch ổ bụng, Doppler, hình thái, bên tổn thương và một số trường IOTA bổ sung ,đầu ra của mô hình là xác suất một ca thuộc nhóm ung thư dựa trên thông tin siêu âm.
- **MRI Expert:** sử dụng 8 biến từ MRI theo O-RADS, bao gồm mô đặc, kích thước phần đặc, đường cong bắt thuốc TIC, hạn chế khuếch tán, vách dày, dịch ổ bụng, hình thái và điểm O-RADS MRI ,đầu ra cũng là xác suất ung thư của từng ca, nhưng được suy ra từ dữ liệu MRI thay vì dữ liệu siêu âm hay lâm sàng.

### 3.2. BaseExpert đang hỗ trợ 3 thuật toán

- Logistic Regression
- Random Forest
- LightGBM

```python
VALID_MODEL_TYPES = ("logistic", "random_forest", "lightgbm")
```

### 3.3. Luồng xử lý cụ thể từ dữ liệu đến kết quả
```text
Dữ liệu bệnh nhân
        ↓
Lọc ca hợp lệ
có nhãn GPB + có dữ liệu của modality tương ứng
        ↓
Chọn đúng nhóm biến đầu vào
Tabular / Ultrasound / MRI
        ↓
Huấn luyện và dự báo bằng LOOCV
mỗi lượt giữ lại 1 ca để kiểm tra
        ↓
Tạo xác suất ung thư cho từng ca
p_cancer
        ↓
So sánh với nhãn GPB thật
        ↓
Tính các chỉ số đánh giá
ROC-AUC, sensitivity, specificity, F1, Brier
```

Điểm quan trọng là mỗi ca được dự báo trong lượt mà mô hình chưa học từ chính ca đó. Vì vậy, kết quả LOOCV phù hợp để kiểm tra pipeline ban đầu khi số ca còn ít.

Ở giai đoạn này, mục tiêu của luồng trên là xác nhận từng Expert có thể đi trọn quy trình từ dữ liệu đầu vào đến bảng kết quả, chưa phải kết luận mô hình cuối cùng để ứng dụng lâm sàng.

### 3.4. Late Fusion lấy xác suất từ Expert và gộp lại

Hiện hỗ trợ 4 chiến lược:
- `simple_average`
- `and`
- `or`
- `max`

```python
VALID_STRATEGIES = ("simple_average", "and", "or", "max")
```

Nếu không có Expert nào khả dụng thì trả `P_fusion=None`

Lưu ý: Ở Phần này hiện tại chỉ là đang check xem là các expert khi gộp xác suất có chạy được hay không, chưa phải là kết quả lâm sàng. Dữ liệu hiện tại còn ít nên các metric dao động mạnh.
---

## 4) Dữ liệu thật hiện đang dùng để đánh giá (hiện tại thì đang chỉ dùng 12 ca thực tế được cung cấp)

Sau khi lọc theo điều kiện supervised (`label != None` và modality `available == 1`):

- Tabular: 9 ca (4 ác tính, 5 không ung thư)
- Ultrasound: 11 ca (5 ác tính, 6 không ung thư)
- MRI: 10 ca (4 ác tính, 6 không ung thư)

Case 12 bị loại khỏi supervised vì chưa có GPB xác nhận nhãn.

---

## 5) Kết quả hiện tại của từng Expert (LOOCV)

Đây là kết quả kỹ thuật để kiểm tra pipeline, chưa phải hiệu năng lâm sàng.

| Expert (mô hình chuyên gia) | Thuật toán | N (số ca) | ROC-AUC (khả năng xếp hạng nguy cơ) | Sensitivity (độ nhạy) | Specificity (độ đặc hiệu) | F1 (cân bằng precision và recall) | Brier (độ chính xác xác suất) |
|---|---|---:|---:|---:|---:|---:|---:|
| Tabular | Logistic | 9 | 0.7500 | 0.7500 | 0.8000 | 0.7500 | 0.2222 |
| Tabular | Random Forest | 9 | 0.7250 | 0.2500 | 0.8000 | 0.3333 | 0.2070 |
| Tabular | LightGBM | 9 | 0.7000 | 0.5000 | 0.8000 | 0.5714 | 0.3332 |
| Ultrasound | Logistic | 11 | 0.3667 | 0.4000 | 0.5000 | 0.4000 | 0.4398 |
| Ultrasound | Random Forest | 11 | 0.6000 | 0.6000 | 0.5000 | 0.5455 | 0.2540 |
| Ultrasound | LightGBM | 11 | 0.5667 | 0.6000 | 0.6667 | 0.6000 | 0.3634 |
| MRI | Logistic | 10 | 0.7083 | 0.7500 | 0.8333 | 0.7500 | 0.2181 |
| MRI | Random Forest | 10 | 0.5833 | 0.2500 | 0.6667 | 0.2857 | 0.3006 |
| MRI | LightGBM | 10 | 0.4167 | 0.5000 | 0.5000 | 0.4444 | 0.4358 |


- **ROC-AUC:** cho biết mô hình có xếp ca ung thư lên mức nguy cơ cao hơn ca không ung thư hay không. Với chỉ số càng gần 1 càng tốt.
- **Sensitivity:** trong các ca thật sự ung thư, mô hình phát hiện đúng được bao nhiêu phần. Chỉ số này quan trọng nếu mục tiêu là hạn chế bỏ sót ca ác tính.
- **Specificity:** trong các ca thật sự không ung thư, mô hình nhận đúng được bao nhiêu phần. Chỉ số này quan trọng nếu muốn hạn chế báo động giả.
- **F1:** là chỉ số cân bằng giữa precision và recall. Có thể hiểu đơn giản là mô hình vừa cần bắt được ca ung thư, vừa không nên gọi quá nhiều ca không ung thư thành ung thư. F1 càng cao càng tốt, nhưng nó phụ thuộc vào ngưỡng phân loại đang dùng, hiện tại là ngưỡng demo 0.5.
- **Brier:** đo chất lượng của xác suất dự đoán. Nếu mô hình nói một ca có xác suất ung thư 0.9 và ca đó thật sự ung thư thì tốt; nếu nói 0.9 nhưng ca đó không ung thư thì bị phạt nặng. Brier càng thấp càng tốt.

---

## 6) Khó khăn/trở ngại hiện tại 

- Cỡ mẫu rất nhỏ (N=9 đến 11), nên metric dao động mạnh.
- Chưa có ca mới hoàn toàn để test độc lập đúng nghĩa.
- Threshold 0.5 hiện chỉ là ngưỡng demo kỹ thuật, chưa phải ngưỡng lâm sàng.
---


