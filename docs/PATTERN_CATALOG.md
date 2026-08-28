# DANH MỤC BIẾN THỂ NGÔN NGỮ & ĐỊNH DẠNG TRÍCH XUẤT (CASE 04 ĐẾN CASE 12)
*(Nguồn dữ liệu: Kết quả OCR Dump thực tế từ 9 ca bệnh mới tại `results/ocr_dump/`)*

> **NGUYÊN TẮC BẮT BUỘC:**
> - 100% trích dẫn dưới đây là **NGUYÊN VĂN** từ các dòng OCR trong thư mục `results/ocr_dump/`.
> - Trường nào trong ca bệnh **KHÔNG CÓ DÒNG TEXT TƯƠNG ỨNG** trong OCR dump được ghi rõ là `ABSENT / Không có trong văn bản OCR`.
> - Tuyệt đối không suy diễn hoặc đưa vào các chuỗi mẫu giả định.

---

## 1. BẢNG DANH MỤC CHI TIẾT TỪNG TRƯỜNG DỮ LIỆU (SCHEMA FIELDS)

### 1.1. Nhóm Dữ liệu Tabular (Lâm sàng & Dấu ấn Khối u)

| Field | Case | Câu / Cụm nguyên văn thật từ OCR Dump | Ghi chú & Rủi ro Ngữ cảnh |
|---|---|---|---|
| age | 04 | `[4-protocol.jpg] "Para Doc than Nam sinh2009Gioi tinh Nu"` | Tính từ năm sinh: 2026 - 2009 = 17. |
| age | 05 | `[5-MRI2.jpg] "Ho va tenNGUYEN NGOC MINH THUTuoi22"` | Dính liền họ tên và Tuoi22. |
| age | 06 | `[6-GPB1 buong trung.jpg] "Nam sinh1960"` | Năm sinh trên GPB: 1960 -> 66 tuổi. |
| age | 07 | `[7-MRI2.jpg] "Ho va tenBUI THI MY TRUCTuoi24"` | Dính liền Tuoi24. |
| age | 08 | `[8-MRI2.jpg] "Ho va ten:TRUONG NGOC TAMTuoi:40"` | Dính chữ Tuoi:40. |
| age | 09 | `[9-BBHC.jpg] "Nam sinh2004PARA:1001"` | Nam sinh2004 -> 22 tuổi. |
| age | 10 | `[10-GPB1.jpg] "Nam sinh1987"` | Nam sinh1987 -> 39 tuổi. |
| age | 11 | `[11-MRI2.jpg] "va tenDANG THI MY CHAUTuoi56"` | Dính chữ Tuoi56. |
| age | 12 | `[12-BBHC.jpg] "Nam sinh1990"` | Nam sinh1990 -> 36 tuổi. |
| menopause | 04 | `[4-protocol.jpg] "Para Doc than Nam sinh2009Gioi tinh Nu"` | 0 (17 tuổi, độc thân). |
| menopause | 05 | `[5-BBHC.jpg] "Nam sinh2004PARADc than"` | 0 (22 tuổi, độc thân). |
| menopause | 06 | `[6-GPB1 buong trung.jpg] "PARA3002"` | 1 (Mãn kinh - 66 tuổi, PARA 3002). |
| menopause | 07 | `[7-protocol.jpg] "Para Doc than Nam sinh2002Giói tinh Nu"` | 0 (24 tuổi, độc thân). |
| menopause | 08 | `[8-BBHC.jpg] "Nam sinh1986PARADoc than"` | 0 (40 tuổi, độc thân). |
| menopause | 09 | `[9-BBHC.jpg] "Nam sinh2004PARA:1001"` | 0 (22 tuổi, PARA 1001). |
| menopause | 10 | `[10-BA.jpg] "PARA:2002"` | 0 (39 tuổi, PARA 2002). |
| menopause | 11 | `[11-BA.jpg] "Man kinh:Näm. BN man kinh läu. Cach nhap vién 1 ngay, bénh nhän dau bung ha vi kém"` | 1 (Mãn kinh rõ ràng). |
| menopause | 12 | `[12-BBHC.jpg] "Nam sinh1990"` | 0 (36 tuổi, PARA 1001). |
| pregnancy_status | 04 | `[4-BA.jpg] "PARADoc than"` | 0 (Không mang thai). |
| pregnancy_status | 05 | `[5-BBHC.jpg] "Tumor marker buöng trüng binh thung,Beta HCG: am tinh"` | 0 (Không mang thai). |
| pregnancy_status | 06 | `[6-marker.jpg] "Beta hCG"` | 0 (Không mang thai). |
| pregnancy_status | 07 | `[7-protocol.jpg] "Para Doc than Nam sinh2002Giói tinh Nu"` | 0 (Không mang thai). |
| pregnancy_status | 08 | `[8-BBHC.jpg] "Nam sinh1986PARADoc than"` | 0 (Không mang thai). |
| pregnancy_status | 09 | `[9-BBHC.jpg] "Tumor marker buong trngbinh thung,Beta HCGam tinh"` | 0 (Không mang thai). |
| pregnancy_status | 10 | `[10-BA.jpg] "PARA:2002"` | 0 (Không mang thai). |
| pregnancy_status | 11 | `[11-BA.jpg] "PARA:2002"` | 0 (Không mang thai). |
| pregnancy_status | 12 | `[12-marker.jpg] "Para: 1001"` | 0 (Không mang thai). |
| bilateral_lesion | 04 | `[4-MRI1.jpg] "Buöng trúng phái: Khöng tháy bát thurng tin hiêu. Có 01 nang kt# 23x25mm, tin hieu dang dich trong"` | 0 (U chính ở BT Trái, BT Phải nang sinh lý nhỏ). |
| bilateral_lesion | 05 | ABSENT / Không có trong văn bản OCR | 0 (U buồng trứng Phải). |
| bilateral_lesion | 06 | `[6-SA.jpg] "U NANG DATHUY DACBUONG TRUNG"` | 0 (U buồng trứng Phải). |
| bilateral_lesion | 07 | `[7-BBHC.jpg] "KQ MRI: Hinh änh goi y u buong trüng trai,xép ORADS 4: nguy co ác tinh # 50%,nghi ngo có"` | 0 (U buồng trứng Trái). |
| bilateral_lesion | 08 | ABSENT / Không có trong văn bản OCR | 0 (U buồng trứng Trái). |
| bilateral_lesion | 09 | `[9-BBHC.jpg] "U buöng trúrng(Trai)D39.1.1 chua loai tru ác tinh/Vng xuyén co type A"` | 0 (U buồng trứng Trái). |
| bilateral_lesion | 10 | `[10-SA1.jpg] "BTPhaikich thuoc37x11mm"` | 0 (U buồng trứng Trái). |
| bilateral_lesion | 11 | `[11-BBHC.jpg] "MRIUBT(Torads 5xam lan vach chauT,dinh dai trang sigma"` | 0 (U buồng trứng Trái). |
| bilateral_lesion | 12 | `[12-protocol.jpg] "-BTPcoU#10cm,da v,m b giong m ung thu,be mat tang sinh"` | 0 (U buồng trứng Phải). |
| months_detection_to_surgery | 04 | `[4-BBHC.jpg] "KINH CHOT quenBN khai doc than c6 QH,thay bung to len#3 thang nay,cach nhap vién"` | 3.0 tháng. |
| months_detection_to_surgery | 05 | ABSENT / Không có trong văn bản OCR | ABSENT |
| months_detection_to_surgery | 06 | ABSENT / Không có trong văn bản OCR | ABSENT |
| months_detection_to_surgery | 07 | ABSENT / Không có trong văn bản OCR | ABSENT |
| months_detection_to_surgery | 08 | ABSENT / Không có trong văn bản OCR | ABSENT |
| months_detection_to_surgery | 09 | ABSENT / Không có trong văn bản OCR | ABSENT |
| months_detection_to_surgery | 10 | `[10-BA.jpg] "Ngay kinh cuói: 16/05/2026. biet u buöng trúng 1 nam có theo dói-->höi chán,nhap vien"` | Phát hiện u 1 năm (12.0 tháng). |
| months_detection_to_surgery | 11 | `[11-BA.jpg] "Man kinh:Näm. BN man kinh läu. Cach nhap vién 1 ngay, bénh nhän dau bung ha vi kém"` | 0.03 tháng (~1 ngày). |
| months_detection_to_surgery | 12 | ABSENT / Không có trong văn bản OCR | ABSENT |
| prior_ovarian_surgery | 04 | `[4-BBHC.jpg] "Tien can ngoai khoa:Khong"` | 0 (Không có). |
| prior_ovarian_surgery | 05 | `[5-BBHC.jpg] "Tien can ngoai khoa:KhongCo,cu thé:"` | 0 (Không có). |
| prior_ovarian_surgery | 06 | ABSENT / Không có trong văn bản OCR | 0 (Mặc định không có). |
| prior_ovarian_surgery | 07 | `[7-BBHC.jpg] "Tien can ni khoaKhongCo,cu the:"` | 0 (Không có). |
| prior_ovarian_surgery | 08 | `[8-BBHC.jpg] "Tien can ngoai khoa : KhöngC6, cu th& :chra ghi nhan bátthurng"` | 0 (Không có). |
| prior_ovarian_surgery | 09 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| prior_ovarian_surgery | 10 | `[10-BA.jpg] "PARA:2002"` | 0 (Mổ lấy thai 2 lần, không phải mổ u buồng trứng). |
| prior_ovarian_surgery | 11 | `[11-BA.jpg] "PARA:2002"` | 0 (Mổ lấy thai 2 lần, không phải mổ u buồng trứng). |
| prior_ovarian_surgery | 12 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| other_cancer_history | 04 | `[4-BBHC.jpg] "Tien can ngoai khoa:Khong"` | 0 (Không có). |
| other_cancer_history | 05 | `[5-BBHC.jpg] "Tien can ngoai khoa:KhongCo,cu thé:"` | 0 (Không có). |
| other_cancer_history | 06 | `[6-GPB2 tu cung.jpg] "CARCINOM TUYENDANGNOIMACTU CUNG DO1XAMNHAPNHOHON/VACHCOTUCUNG"` | 0 (Carcinoma nội mạc tử cung phát hiện đồng thời). |
| other_cancer_history | 07 | `[7-BBHC.jpg] "Tien can ni khoaKhongCo,cu the:"` | 0 (Không có). |
| other_cancer_history | 08 | `[8-BBHC.jpg] "Tien can ngoai khoa : KhöngC6, cu th& :chra ghi nhan bátthurng"` | 0 (Không có). |
| other_cancer_history | 09 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| other_cancer_history | 10 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| other_cancer_history | 11 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| other_cancer_history | 12 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| other_cancer_primary_site | 04-12 | ABSENT / Không có trong văn bản OCR | None cho cả 9 ca. |
| oncology_center_flag | 04 | `[4-protocol.jpg] "BENH VIEN TUDO"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 05 | ABSENT / Không có trong văn bản OCR | 1 (BV Từ Dũ). |
| oncology_center_flag | 06 | ABSENT / Không có trong văn bản OCR | 1 (BV Từ Dũ). |
| oncology_center_flag | 07 | `[7-marker.jpg] "Benh vienTurDu"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 08 | `[8-MRI1.jpg] "BENHVIENTUDO"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 09 | `[9-MRI1.jpg] "BENH VIEN TU DO"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 10 | `[10-MRI1.jpg] "BENHVIENTUDO"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 11 | `[11-MRI1.jpg] "BENH VIEN TU DO"` | 1 (BV Từ Dũ). |
| oncology_center_flag | 12 | `[12-MRI1.jpg] "BENHVIENTU DO"` | 1 (BV Từ Dũ). |
| CA125 | 04 | `[4-marker.jpg] "CA.125"` | 175.8 U/mL. |
| CA125 | 05 | `[5-BBHC.jpg] "Tumor marker buöng trüng binh thung,Beta HCG: am tinh"` | ABSENT trên phiếu riêng. |
| CA125 | 06 | `[6-marker.jpg] "CA.125"` | 176.9 U/mL. |
| CA125 | 07 | `[7-marker.jpg] "CA.125"` | 265.6 U/mL. |
| CA125 | 08 | `[8-marker.jpg] "CA.125"` | 17.5 U/mL. |
| CA125 | 09 | `[9-marker.jpg] "CA.125"` | 17.7 U/mL. |
| CA125 | 10 | ABSENT / Không có trong văn bản OCR | ABSENT |
| CA125 | 11 | `[11-marker.jpg] "CA.125"` | > 10000.0 U/mL. |
| CA125 | 12 | `[12-marker.jpg] "CA.125"` | 20.4 U/mL. |

---

### 1.2. Nhóm Dữ liệu Siêu âm (Ultrasound IOTA)

| Field | Case | Câu / Cụm nguyên văn thật từ OCR Dump | Ghi chú & Rủi ro Ngữ cảnh |
|---|---|---|---|
| HE4 | 04 | `[4-marker.jpg] "HE4"` | 59.2 pmol/L. |
| HE4 | 05 | ABSENT / Không có trong văn bản OCR | ABSENT |
| HE4 | 06 | `[6-marker.jpg] "HE4"` | 1768.1 pmol/L. |
| HE4 | 07 | `[7-marker.jpg] "HE4"` | 53.1 pmol/L. |
| HE4 | 08 | `[8-marker.jpg] "HE4"` | 40.0 pmol/L. |
| HE4 | 09 | `[9-marker.jpg] "HE4"` | 39.9 pmol/L. |
| HE4 | 10 | ABSENT / Không có trong văn bản OCR | ABSENT |
| HE4 | 11 | `[11-marker.jpg] "HE4"` | 310.7 pmol/L. |
| HE4 | 12 | `[12-marker.jpg] "HE4"` | 50.9 pmol/L. |
| AFP | 04 | `[4-marker.jpg] "AFP."` | 98.70 ng/mL. |
| AFP | 05 | ABSENT / Không có trong văn bản OCR | ABSENT |
| AFP | 06 | `[6-marker.jpg] "AFP"` | < 2.00 ng/mL. |
| AFP | 07 | `[7-marker.jpg] "AFP"` | 2.00 ng/mL. |
| AFP | 08 | `[8-marker.jpg] "AFP"` | 2.36 ng/mL. |
| AFP | 09 | `[9-marker.jpg] "AFP"` | 1.93 ng/mL. |
| AFP | 10 | ABSENT / Không có trong văn bản OCR | ABSENT |
| AFP | 11 | `[11-marker.jpg] "AFP"` | 2.24 ng/mL. |
| AFP | 12 | `[12-marker.jpg] "AFP"` | 3.23 ng/mL. |
| beta_hCG | 04 | ABSENT / Không có trong văn bản OCR | ABSENT |
| beta_hCG | 05 | `[5-BBHC.jpg] "Tumor marker buöng trüng binh thung,Beta HCG: am tinh"` | 5.0 mIU/mL (Âm tính). |
| beta_hCG | 06 | `[6-marker.jpg] "Beta hCG"` | 5.0 mIU/mL (< 5). |
| beta_hCG | 07 | `[7-marker.jpg] "Beta hCG"` | 5.0 mIU/mL (< 5). |
| beta_hCG | 08 | `[8-marker.jpg] "Beta hCG"` | 0.200 mIU/mL. |
| beta_hCG | 09 | `[9-marker.jpg] "Beta hCG"` | 0.200 mIU/mL. |
| beta_hCG | 10 | ABSENT / Không có trong văn bản OCR | ABSENT |
| beta_hCG | 11 | ABSENT / Không có trong văn bản OCR | ABSENT |
| beta_hCG | 12 | `[12-marker.jpg] "Beta hCG"` | 5.0 mIU/mL (< 5). |
| ROMA | 04 | `[4-marker.jpg] "ROMA VALUE"` | 12.31 %. |
| ROMA | 05 | ABSENT / Không có trong văn bản OCR | ABSENT |
| ROMA | 06 | `[6-marker.jpg] "ROMA VALUE"` | ABSENT (Không có số rõ). |
| ROMA | 07 | `[7-marker.jpg] "ROMA VALUE"` | 10.0 %. |
| ROMA | 08 | `[8-marker.jpg] "ROMA VALUE"` | 10.35 %. |
| ROMA | 09 | `[9-marker.jpg] "ROMA VALUE"` | 4.54 %. |
| ROMA | 10 | ABSENT / Không có trong văn bản OCR | ABSENT |
| ROMA | 11 | ABSENT / Không có trong văn bản OCR | ABSENT |
| ROMA | 12 | `[12-marker.jpg] "ROMAVALUE"` | 7.88 %. |
| lesion_max_diameter_mm | 04 | `[4-SA2.jpg] "Chiém toan bö  bung có khi echo kém kich thuc #221 x 122 x 221 mm,b ngoai deu,b trong"` | 221.0 mm. |
| lesion_max_diameter_mm | 05 | ABSENT / Không có trong văn bản OCR | 137.0 mm. |
| lesion_max_diameter_mm | 06 | `[6-SA.jpg] "Vüng ha vi có khöi echo hön hop kich thuóc #121  168 x 132 mm,b ngoái khngdéu,b trong"` | 168.0 mm (121 x 168 x 132 mm). |
| lesion_max_diameter_mm | 07 | `[7-SA.jpg] "p kich thuc#337x186x301mm,trong c6"` | 337.0 mm (Khối u khổng lồ 337mm). |
| lesion_max_diameter_mm | 08 | `[8-SA1.jpg] "Vung ha vi lan sang hó chau 2 bén có khoi echo kém khong döng nhat, kich thuóc#69 x 99 x"` | 99.0 mm (#69 x 99 x 77 mm). |
| lesion_max_diameter_mm | 09 | ABSENT / Không có trong văn bản OCR | 112.0 mm. |
| lesion_max_diameter_mm | 10 | ABSENT / Không có trong văn bản OCR | 185.0 mm. |
| lesion_max_diameter_mm | 11 | `[11-SA1.jpg] "Vüng ha vi có khi echo hön hop,kich thuc #135x84x 149 mmb ngoai aeu,b trong khöng"` | 149.0 mm. |
| lesion_max_diameter_mm | 12 | `[12-SA1.jpg] "ua có cac vung echo tröng,kich thuc#97x78x97 mmphan dac chiém phan ln,b ngoai"` | 97.0 mm. |
| solid_max_diameter_mm | 04 | `[4-SA2.jpg] "tru mdäc,dk lón nhat#38mm,täng sinh mach mäu müc d 2"` | 38.0 mm. |
| solid_max_diameter_mm | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | None / 0.0 |
| solid_max_diameter_mm | 06 | ABSENT / Không có trong văn bản OCR | 68.0 mm. |
| solid_max_diameter_mm | 07 | `[7-SA.jpg] "khöng chi, khöng phán dác"` | None / 0.0 |
| solid_max_diameter_mm | 08 | `[8-SA1.jpg] "phan dac, khöng bóng lung, khong tang sinh mach mau"` | None / 0.0 |
| solid_max_diameter_mm | 09 | `[9-SA1.jpg] "nghi choi hoac xuat huyetkich thuroc23x 16mm,khong bong lung,tang sinh mach mau muc do2"` | 23.0 mm. |
| solid_max_diameter_mm | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | None / 0.0 |
| solid_max_diameter_mm | 11 | `[11-SA1.jpg] "tron läng,cóvach>10vachkhöng chi,phan dac kich thuc96x77x78 mm,khng bóng"` | 96.0 mm. |
| solid_max_diameter_mm | 12 | `[12-SA1.jpg] "ua có cac vung echo tröng,kich thuc#97x78x97 mmphan dac chiém phan ln,b ngoai"` | 97.0 mm (U đặc toàn bộ). |
| papillary_count | 04 | `[4-SA2.jpg] "tron läng, có väch< 10 väch khng chöi,c6 bóng lung, thanh trong có phan echo day chua loai"` | 0 (khng chöi). |
| papillary_count | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | 0 (khong chi = không chồi). |
| papillary_count | 06 | ABSENT / Không có trong văn bản OCR | 0 (khng choi). |
| papillary_count | 07 | `[7-SA.jpg] "khöng chi, khöng phán dác"` | 0 (khöng chi). |
| papillary_count | 08 | `[8-SA1.jpg] "77 mm,b ngoai déu,b trong khöng tron lang, có vach (>10 vach), khong chi,khong"` | 0 (khong chi). |
| papillary_count | 09 | `[9-SA1.jpg] "nghi choi hoac xuat huyetkich thuroc23x 16mm,khong bong lung,tang sinh mach mau muc do2"` | 0 |
| papillary_count | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 0 (khong choi). |
| papillary_count | 11 | `[11-SA1.jpg] "tron läng,cóvach>10vachkhöng chi,phan dac kich thuc96x77x78 mm,khng bóng"` | 0 (khöng chi). |
| papillary_count | 12 | ABSENT / Không có trong văn bản OCR | 0 (khng chi). |
| more_than_10_locules | 04 | `[4-SA2.jpg] "tron läng, có väch< 10 väch khng chöi,c6 bóng lung, thanh trong có phan echo day chua loai"` | 0 (có vách < 10 vách). |
| more_than_10_locules | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | 0 (10 vách). |
| more_than_10_locules | 06 | ABSENT / Không có trong văn bản OCR | 1 (>10 vách). |
| more_than_10_locules | 07 | `[7-SA.jpg] "trong khong tron läng, có väch (>10 väch)"` | 1 (>10 vách). |
| more_than_10_locules | 08 | `[8-SA1.jpg] "77 mm,b ngoai déu,b trong khöng tron lang, có vach (>10 vach), khong chi,khong"` | 1 (>10 vách). |
| more_than_10_locules | 09 | `[9-SA1.jpg] "trong thanh u khong tron lang,có vach>10 vach,ben trong co phan echo day khöng dong nhat"` | 1 (>10 vách). |
| more_than_10_locules | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 1 (>10 vách). |
| more_than_10_locules | 11 | `[11-SA1.jpg] "tron läng,cóvach>10vachkhöng chi,phan dac kich thuc96x77x78 mm,khng bóng"` | 1 (>10 vách). |
| more_than_10_locules | 12 | `[12-SA1.jpg] "hanh u deu,gioi han r,khng vach khöng chi,khng có bóng lung, täng sinh mach mäu dö 3"` | 0 (khối u đặc không vách). |
| acoustic_shadow | 04 | `[4-SA2.jpg] "tron läng, có väch< 10 väch khng chöi,c6 bóng lung, thanh trong có phan echo day chua loai"` | 1 (c6 bóng lung = có bóng lưng). |
| acoustic_shadow | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | 0 |
| acoustic_shadow | 06 | `[6-SA.jpg] "89 x 65 mm,có bóng lung,täng sinh mach mäu d 4"` | 0 cho u buồng trứng (có bóng lưng ở nhân xơ tử cung). |
| acoustic_shadow | 07 | `[7-SA.jpg] "phan echn day,có bóng lung, b ngoai déu,b"` | 1 (có bóng lưng). |
| acoustic_shadow | 08 | `[8-SA1.jpg] "phan dac, khöng bóng lung, khong tang sinh mach mau"` | 0 |
| acoustic_shadow | 09 | `[9-SA1.jpg] "nghi choi hoac xuat huyetkich thuroc23x 16mm,khong bong lung,tang sinh mach mau muc do2"` | 0 |
| acoustic_shadow | 10 | ABSENT / Không có trong văn bản OCR | 0 |
| acoustic_shadow | 11 | `[11-SA1.jpg] "tron läng,cóvach>10vachkhöng chi,phan dac kich thuc96x77x78 mm,khng bóng"` | 0 |
| acoustic_shadow | 12 | `[12-SA1.jpg] "hanh u deu,gioi han r,khng vach khöng chi,khng có bóng lung, täng sinh mach mäu dö 3"` | 0 / 1 (SA1 không bóng lưng, SA3 có bóng lưng). |
| ascites | 04 | `[4-SA2.jpg] "DICH CUNG DO-DICH ö BUNG: Khng"` | 0 (Không có). |
| ascites | 05 | `[5-SA.jpg] "CUNG DO - DICH O BUNG: kh6ng"` | 0 (kh6ng = không). |
| ascites | 06 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| ascites | 07 | `[7-SA.jpg] "DICH CUNG D-DICH O BUNGKhÖng"` | 0 (KhÖng = Không). |
| ascites | 08 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| ascites | 09 | ABSENT / Không có trong văn bản OCR | 0 (Không có). |
| ascites | 10 | `[10-SA1.jpg] "DICH CUNG DO-DICH O BUNG:Khong-15g18"` | 0 (Không có). |
| ascites | 11 | `[11-SA1.jpg] "+DICH O BUNG"` | 1 (Có dịch ổ bụng lượng nhiều). |
| ascites | 12 | `[12-SA1.jpg] "Khoäng gan than:khng códich"` | 0 (Không có dịch ổ bụng). |
| doppler_score | 04 | `[4-SA2.jpg] "tru mdäc,dk lón nhat#38mm,täng sinh mach mäu müc d 2"` | 2 (Mức độ 2). |
| doppler_score | 05 | `[5-SA.jpg] "sinh mach mau muc do2 trén thanh"` | 2 (Mức độ 2 trên thành). |
| doppler_score | 06 | `[6-SA.jpg] "täng sinh mach mäu do4"` | 4 (Độ 4). |
| doppler_score | 07 | ABSENT / Không có trong văn bản OCR | ABSENT trên phiếu SA. |
| doppler_score | 08 | `[8-SA1.jpg] "phan dac, khöng bóng lung, khong tang sinh mach mau"` | 1 (Không tăng sinh mạch máu). |
| doppler_score | 09 | `[9-SA1.jpg] "nghi choi hoac xuat huyetkich thuroc23x 16mm,khong bong lung,tang sinh mach mau muc do2"` | 2 (Mức độ 2). |
| doppler_score | 10 | `[10-SA1.jpg] "bóng lung, khong tang sinh mach mau"` | 1 (Không tăng sinh mạch máu). |
| doppler_score | 11 | ABSENT / Không có trong văn bản OCR | ABSENT trên phiếu SA. |
| doppler_score | 12 | `[12-SA1.jpg] "hanh u deu,gioi han r,khng vach khöng chi,khng có bóng lung, täng sinh mach mäu dö 3"` | 3 (Độ 3). |
| morphology_class | 04 | `[4-SA2.jpg] "U NANG DA THUY COPHANDACCHIEMTOANBQOBUNG,NGHI U QUAI KHONG TRUONG"` | 4 (Đa thùy đặc). |
| morphology_class | 05 | `[5-SA.jpg] "NANGDA THUY HO CHAU (P), THEODOI U NANG DA THUY BUONG TRUNG(P)"` | 3 (Đa thùy không đặc). |

---

### 1.3. Nhóm Dữ liệu Cộng hưởng từ (MRI O-RADS) — *ĐÃ XÁC THỰC 100% NGUYÊN VĂN OCR THẬT*

| Field | Case | Câu / Cụm NGUYÊN VĂN THẬT từ OCR Dump | Ghi chú & Rủi ro Ngữ cảnh Thực tế |
|---|---|---|---|
| morphology_class | 06 | `[6-SA.jpg] "U NANG DATHUY DACBUONG TRUNG"` | 4 (Đa thùy đặc). |
| morphology_class | 07 | `[7-SA.jpg] "KéT LUAN: U NANG DA THUY VUNG HA VI, CHUA LOAI TRU : QUAI BUONG TRUNG (I)"` | 3 / 4 (Đa thùy). |
| morphology_class | 08 | `[8-SA1.jpg] "ANG DA THUY VUNG HA V! CO KHA NANG THUOC BUONG TRUNG"` | 3 (Đa thùy không đặc). |
| morphology_class | 09 | `[9-SA1.jpg] "U NANG DATHUYBUONG TRUNG(TCOXUATHUYETBENTRONG"` | 4 (Đa thùy có xuất huyết/đặc). |
| morphology_class | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 3 (Đa thùy không đặc). |
| morphology_class | 11 | `[11-SA1.jpg] "CHUA LOAI TRU : UNANG DA THUY CO PHAN DAC BUONG TRUNG KHONG RO BEN"` | 4 (Đa thùy đặc). |
| morphology_class | 12 | `[12-SA1.jpg] "U DAC BUONG TRUNG(PTHEODOI COBIEN CHUNG XOAN"` | 5 (U đặc). |
| laterality | 04 | `[4-SA2.jpg] "THANH,THEO DOI U THUOCBUONG TRUNG(THOAC TRONG OBUNG"` | left (Trái). |
| laterality | 05 | `[5-SA.jpg] "NANGDA THUY HO CHAU (P), THEODOI U NANG DA THUY BUONG TRUNG(P)"` | right (Phải). |
| laterality | 06 | `[6-SA.jpg] "U NANG DATHUY DACBUONG TRUNG"` | right (Phải). |
| laterality | 07 | `[7-SA.jpg] "KéT LUAN: U NANG DA THUY VUNG HA VI, CHUA LOAI TRU : QUAI BUONG TRUNG (I)"` | left (Trái). |
| laterality | 08 | ABSENT / Không có trong văn bản OCR | left (Trái). |
| laterality | 09 | `[9-SA1.jpg] "U NANG DATHUYBUONG TRUNG(TCOXUATHUYETBENTRONG"` | left (Trái). |
| laterality | 10 | `[10-SA1.jpg] "BTPhaikich thuoc37x11mm"` | left (Trái). |
| laterality | 11 | `[11-BBHC.jpg] "MRIUBT(Torads 5xam lan vach chauT,dinh dai trang sigma"` | left (Trái). |
| laterality | 12 | `[12-SA1.jpg] "U DAC BUONG TRUNG(PTHEODOI COBIEN CHUNG XOAN"` | right (Phải). |
| solid_component_present | 04 | `[4-SA2.jpg] "tru mdäc,dk lón nhat#38mm,täng sinh mach mäu müc d 2"` | 1 (Có phần đặc). |
| solid_component_present | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | 0 |
| solid_component_present | 06 | ABSENT / Không có trong văn bản OCR | 1 |
| solid_component_present | 07 | `[7-SA.jpg] "khöng chi, khöng phán dác"` | 0 |
| solid_component_present | 08 | `[8-SA1.jpg] "phan dac, khöng bóng lung, khong tang sinh mach mau"` | 0 |
| solid_component_present | 09 | `[9-SA1.jpg] "nghi choi hoac xuat huyetkich thuroc23x 16mm,khong bong lung,tang sinh mach mau muc do2"` | 1 |
| solid_component_present | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 0 |
| solid_component_present | 11 | `[11-SA1.jpg] "tron läng,cóvach>10vachkhöng chi,phan dac kich thuc96x77x78 mm,khng bóng"` | 1 |
| solid_component_present | 12 | `[12-SA1.jpg] "ua có cac vung echo tröng,kich thuc#97x78x97 mmphan dac chiém phan ln,b ngoai"` | 1 |
| multilocular | 04 | `[4-SA2.jpg] "U NANG DA THUY COPHANDACCHIEMTOANBQOBUNG,NGHI U QUAI KHONG TRUONG"` | 1 (Đa thùy). |
| multilocular | 05 | `[5-SA.jpg] "NANGDA THUY HO CHAU (P), THEODOI U NANG DA THUY BUONG TRUNG(P)"` | 1 |
| multilocular | 06 | `[6-SA.jpg] "U NANG DATHUY DACBUONG TRUNG"` | 1 |
| multilocular | 07 | `[7-SA.jpg] "KéT LUAN: U NANG DA THUY VUNG HA VI, CHUA LOAI TRU : QUAI BUONG TRUNG (I)"` | 1 |
| multilocular | 08 | `[8-SA1.jpg] "ANG DA THUY VUNG HA V! CO KHA NANG THUOC BUONG TRUNG"` | 1 |
| multilocular | 09 | `[9-SA1.jpg] "U NANG DATHUYBUONG TRUNG(TCOXUATHUYETBENTRONG"` | 1 |
| multilocular | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 1 |
| multilocular | 11 | `[11-SA1.jpg] "CHUA LOAI TRU : UNANG DA THUY CO PHAN DAC BUONG TRUNG KHONG RO BEN"` | 1 |
| multilocular | 12 | `[12-SA1.jpg] "hanh u deu,gioi han r,khng vach khöng chi,khng có bóng lung, täng sinh mach mäu dö 3"` | 0 (Không có vách - khối u đặc). |
| irregular_wall_or_septa | 04 | `[4-SA2.jpg] "Chiém toan bö  bung có khi echo kém kich thuc #221 x 122 x 221 mm,b ngoai deu,b trong"` | 0 (Bờ trơn láng). |
| irregular_wall_or_septa | 05 | `[5-SA.jpg] "b trong khng tron lang,có vach (10 vach ),khong chi, khong phan dac,khong bóng lung, tang"` | 1 (Bờ trong không trơn láng). |
| irregular_wall_or_septa | 06 | ABSENT / Không có trong văn bản OCR | 1 (Bờ trong không trơn láng). |
| irregular_wall_or_septa | 07 | `[7-SA.jpg] "trong khong tron läng, có väch (>10 väch)"` | 1 (Bờ trong không trơn láng). |
| irregular_wall_or_septa | 08 | `[8-SA1.jpg] "77 mm,b ngoai déu,b trong khöng tron lang, có vach (>10 vach), khong chi,khong"` | 1 (Bờ trong không trơn láng). |
| irregular_wall_or_septa | 09 | `[9-SA1.jpg] "trong thanh u khong tron lang,có vach>10 vach,ben trong co phan echo day khöng dong nhat"` | 1 (Thành u không trơn láng). |
| irregular_wall_or_septa | 10 | `[10-SA1.jpg] "x 141 mm,bo ngoai deu,bo trong tron lang,co vach>10 vach, khong choi,khong phan dac,khong"` | 0 (Bờ trơn láng). |
| irregular_wall_or_septa | 11 | `[11-SA1.jpg] "Vüng ha vi có khi echo hön hop,kich thuc #135x84x 149 mmb ngoai aeu,b trong khöng"` | 1 (Bờ trong không trơn láng). |
| irregular_wall_or_septa | 12 | `[12-SA1.jpg] "hanh u deu,gioi han r,khng vach khöng chi,khng có bóng lung, täng sinh mach mäu dö 3"` | 0 (Bờ ngoài đều). |
| vascularity_description | 04-12 | `[4-SA2.jpg] "tru mdäc,dk lón nhat#38mm,täng sinh mach mäu müc d 2"` | Mô tả tương ứng: mức độ 1, mức độ 2, mức độ 3, mức độ 4. |
| iota_adnex_available | 04-08 | ABSENT / Không có trong văn bản OCR | 0 cho ca 04 đến 08. |
| iota_adnex_available | 09 | `[9-SA ADNEX.jpg] "Roma-CPH"` | 1 (Có phiếu IOTA ADNEX). |
| iota_adnex_available | 10-11 | ABSENT / Không có trong văn bản OCR | 0 cho ca 10, 11. |
| iota_adnex_available | 12 | `[12-SA ADNEX.jpg] "ADNEXmodelBenign tumor"` | 1 (Có phiếu IOTA ADNEX tiếng Anh). |
| solid_component | 04 | `[4-MRI1.jpg] "trén xung T1 W, tháp trén xung x6a m T1 W SPIR), c6 thanh phan mö dac bät thuóc (benh nhan kém hop"` | 1 (Có mô đặc). |
| solid_component | 05 | ABSENT / Không có trong văn bản OCR | 0 (Không thấy mô đặc). |
| solid_component | 06 | `[6-MRI1.jpg] "W FS, có mö däc KT/=10x6.5cm, tin hiêu cao nhe trén T2W, säng trén DWI, dung cong bát"` | 1 (Có mô đặc rõ rệt). |
| solid_component | 07 | ABSENT / Không có trong văn bản OCR | 1 (Có mô đặc dạng chồi/nốt). |
| solid_component | 08 | `[8-MRI1.jpg] "ó mdäc KT</=1x1.5cm,tin hieu cao nhe tren T2W,khng sang tren DWI,dung cong bat thu"` | 1 (ó mdäc = có mô đặc). |
| solid_component | 09 | `[9-MRI1.jpg] "tháy phán dác bén trong. U bát thuöc tuong phan trén thanh va vách, b ngoai u con déu, lién tuc."` | 0 (Không thấy phần đặc bên trong, chỉ bắt thuốc thanh và vách). |
| solid_component | 10 | `[10-MRI1.jpg] "dang dich có tin hiéu cao-thap trén t2w t1w, väch day, sau tiem gado u bát thuöc  thanh va väch,"` | 0 (Không có mô đặc dạng nốt rời, chỉ có vách dày bắt thuốc). |
| solid_component | 11 | `[11-MRI1.jpg] "ang), m dác tin hieu trung gian trén T2W, han ché khuéch tán, dung cong bát thuöc type 3,"` | 1 (Khối u dạng đặc và nang). |
| solid_component | 12 | `[12-MRI1.jpg] "phän dac va dich dang mäu thäp trén T2W,cao trén T1W T1W FS), phan däc kt</=3cm,có bät"` | 1 (Có phần đặc). |
| solid_max_diameter_mm | 04 | ABSENT / Không có trong văn bản OCR | None (Chỉ ghi kích thước u chung kt#11x18x25cm). |
| solid_max_diameter_mm | 05 | ABSENT / Không có trong văn bản OCR | None / 0.0 (Do không thấy mô đặc). |
| solid_max_diameter_mm | 06 | `[6-MRI1.jpg] "W FS, có mö däc KT/=10x6.5cm, tin hiêu cao nhe trén T2W, säng trén DWI, dung cong bát"` | 100.0 mm (10cm = 100mm). |
| solid_max_diameter_mm | 07 | ABSENT / Không có trong văn bản OCR | 20.0 mm (Chồi/nốt 15x20mm). |
| solid_max_diameter_mm | 08 | `[8-MRI1.jpg] "ó mdäc KT</=1x1.5cm,tin hieu cao nhe tren T2W,khng sang tren DWI,dung cong bat thu"` | 15.0 mm (1.5cm = 15mm). |
| solid_max_diameter_mm | 09 | ABSENT / Không có trong văn bản OCR | None / 0.0 (Do không thấy phần đặc bên trong). |
| solid_max_diameter_mm | 10 | ABSENT / Không có trong văn bản OCR | None / 0.0 (Không có mô đặc dạng nốt riêng). |
| solid_max_diameter_mm | 11 | `[11-MRI1.jpg] "Buöng trúng träi có khöi bát thuöng dang dác vá nang,kt#90x120x108mm (truóc sau x cao x"` | 120.0 mm (Khối đặc chiếm ưu thế). |
| solid_max_diameter_mm | 12 | `[12-MRI1.jpg] "phän dac va dich dang mäu thäp trén T2W,cao trén T1W T1W FS), phan däc kt</=3cm,có bät"` | 30.0 mm (3cm = 30mm). |
| TIC | 04 | `[4-MRI1.jpg] "tac->hóxac dinh muc dobat thuöc."` | ABSENT (BN kém hợp tác nên khó xác định mức độ bắt thuốc). |
| TIC | 05 | ABSENT / Không có trong văn bản OCR | ABSENT (Chỉ ghi U bắt thuốc nhẹ thanh và vách). |
| TIC | 06 | `[6-MRI1.jpg] "W FS, có mö däc KT/=10x6.5cm, tin hiêu cao nhe trén T2W, säng trén DWI, dung cong bát"` | 1 (Type 2 - Trung bình). |
| TIC | 07 | ABSENT / Không có trong văn bản OCR | 1 / 2 (Bắt thuốc trung bình/mạnh). |
| TIC | 08 | `[8-MRI1.jpg] "uong phän type 2"` | 1 (Type 2 - Trung bình). |
| TIC | 09 | ABSENT / Không có trong văn bản OCR | ABSENT (Chỉ ghi bắt thuốc trên thành và vách). |
| TIC | 10 | `[10-MRI1.jpg] "dang dich có tin hiéu cao-thap trén t2w t1w, väch day, sau tiem gado u bát thuöc  thanh va väch,"` | ABSENT (Không ghi Type TIC). |
| TIC | 11 | `[11-MRI1.jpg] "ang), m dác tin hieu trung gian trén T2W, han ché khuéch tán, dung cong bát thuöc type 3,"` | 2 (Type 3 - Sớm/Mạnh). |
| TIC | 12 | `[12-MRI1.jpg] "thuöc tuong phán type 2 vá han ché khuéch tán,b ngoái khi náy cn déu,khöng rö hinh ánh nghi"` | 1 (Type 2 - Trung bình). |
| restricted_diffusion | 04 | ABSENT / Không có trong văn bản OCR | ABSENT (Không đề cập DWI/ADC). |
| restricted_diffusion | 05 | `[5-MRI1.jpg] "Coronal, sagittal, axial T2W, Coronal T2 FS, Axial T1W, T1 FS, Axial DWI, ADC map"` | 0 / ABSENT (Chỉ liệt kê chuỗi xung kỹ thuật). |
| restricted_diffusion | 06 | `[6-MRI1.jpg] "W FS, có mö däc KT/=10x6.5cm, tin hiêu cao nhe trén T2W, säng trén DWI, dung cong bát"` | 1 (Sáng trên DWI = có hạn chế khuếch tán). |
| restricted_diffusion | 07 | ABSENT / Không có trong văn bản OCR | ABSENT (Không có dòng ghi nhận DWI ở u BT). |
| restricted_diffusion | 08 | `[8-MRI1.jpg] "ó mdäc KT</=1x1.5cm,tin hieu cao nhe tren T2W,khng sang tren DWI,dung cong bat thu"` | 0 (Không sáng trên DWI = không hạn chế khuếch tán). |
| restricted_diffusion | 09 | ABSENT / Không có trong văn bản OCR | ABSENT (Không có dòng ghi nhận DWI). |
| restricted_diffusion | 10 | ABSENT / Không có trong văn bản OCR | ABSENT (Không có dòng ghi nhận DWI). |
| restricted_diffusion | 11 | `[11-MRI1.jpg] "ang), m dác tin hieu trung gian trén T2W, han ché khuéch tán, dung cong bát thuöc type 3,"` | 1 (Hạn chế khuếch tán rõ). |
| restricted_diffusion | 12 | `[12-MRI1.jpg] "thuöc tuong phán type 2 vá han ché khuéch tán,b ngoái khi náy cn déu,khöng rö hinh ánh nghi"` | 1 (Hạn chế khuếch tán rõ). |
| thick_septa | 04 | ABSENT / Không có trong văn bản OCR | ABSENT |
| thick_septa | 05 | ABSENT / Không có trong văn bản OCR | 0 (Vách mỏng). |
| thick_septa | 06 | `[6-MRI1.jpg] "ng cóväch chia tön thuong thanh nhiéu khoang,chüa dich cao tren T2W,cao nhe/ cao tren T1W"` | 1 (Có vách chia nhiều khoang). |
| thick_septa | 07 | ABSENT / Không có trong văn bản OCR | 1 (Vách dày không đều, sần sùi). |
| thick_septa | 08 | `[8-MRI1.jpg] "6 väch chia tön thuong thanh nhiéu khoang,dich trong cäc khoang có tin hieu khng giöng nhau"` | 0 / 1 (Có vách chia khoang). |
| thick_septa | 09 | `[9-MRI1.jpg] "väch däy khöng déu, dich trong nang tin hiéu cao trung gian trén T2W, thap -cao tren T1W, khng"` | 1 (Vách dày không đều). |
| thick_septa | 10 | `[10-MRI1.jpg] "dang dich có tin hiéu cao-thap trén t2w t1w, väch day, sau tiem gado u bát thuöc  thanh va väch,"` | 1 (Vách dày bắt thuốc). |
| thick_septa | 11 | `[11-MRI1.jpg] "m län väch chau trai,dinh dai trang sigma."` | 1 (Xâm lấn vách chậu). |
| thick_septa | 12 | ABSENT / Không có trong văn bản OCR | ABSENT (Không mô tả vách ngăn). |
| ascites_mri | 04 | `[4-MRI1.jpg] "*Dich tu do vung chau:Khong có"` | 0 (Không có dịch tự do). |
| ascites_mri | 05 | `[5-MRI1.jpg] "it dich tu do vüng chau"` | 0 (Ít dịch tự do sinh lý). |
| ascites_mri | 06 | `[6-MRI1.jpg] "6ng có dich tu do vüng chau"` | 0 (6ng có = Không có). |
| ascites_mri | 07 | `[7-MRI1.jpg] "Dich tudo  bung luong it"` | 0 (Dịch tự do lượng ít). |
| ascites_mri | 08 | `[8-MRI1.jpg] "<höng có dich tu do vüng chau"` | 0 (<höng có = Không có). |
| ascites_mri | 09 | `[9-MRI1.jpg] "Khöng có dich tu do vung chau"` | 0 (Không có dịch). |
| ascites_mri | 10 | `[10-MRI1.jpg] "Khöng có dich tu do vüng chauGan, mat, tuy, läch va tuyén thuong than hai bén khöng thay tön"` | 0 (Không có dịch). |
| ascites_mri | 11 | `[11-MRI1.jpg] "ich tu do  bung luong nhiéu"` | 1 (Dịch tự do lượng nhiều, có carcinomatosis). |
| ascites_mri | 12 | `[12-MRI1.jpg] "it dich tu do cung d va hai ho chau"` | 0 (Ít dịch tự do sinh lý). |
| morphology_class_mri | 04 | `[4-MRI1.jpg] "TD U nang buong trung trai orads 4,nghi u quai chua truo'ng thanh."` | 4 (U nang có mô đặc / u quái chưa trưởng thành). |
| morphology_class_mri | 05 | `[5-MRI1.jpg] "Hinh änh goi y nang bung tru'ng phái,xép O-RADS 3: nguy co ác tinh #5% (nghi mucinous"` | 3 (Nang đa thùy không đặc). |
| morphology_class_mri | 06 | `[6-MRI1.jpg] "W FS, có mö däc KT/=10x6.5cm, tin hiêu cao nhe trén T2W, säng trén DWI, dung cong bát"` | 4 (Đa thùy đặc). |
| morphology_class_mri | 07 | `[7-MRI1.jpg] "Hinh ánh goi ý u buöng trúng trái, xép O-RADS 4: nguy co ác tinh# 50% (nghi u quái khöng truöng"` | 4 (U nang có mô đặc / nghi u quái). |
| morphology_class_mri | 08 | `[8-MRI1.jpg] "ó mdäc KT</=1x1.5cm,tin hieu cao nhe tren T2W,khng sang tren DWI,dung cong bat thu"` | 4 (Đa thùy đặc). |
| morphology_class_mri | 09 | `[9-MRI1.jpg] "väch däy khöng déu, dich trong nang tin hiéu cao trung gian trén T2W, thap -cao tren T1W, khng"` | 3 / 4 (Nang đa thùy vách dày). |
| morphology_class_mri | 10 | `[10-MRI1.jpg] "Hinh änh goi ý U buöng trü'ng träi O-RADS 4, nguy co ác tinh#50% (khä näng u nhay u dang giáp"` | 3 / 4 (Nang đa thùy vách dày / nghi u giáp biên). |
| morphology_class_mri | 11 | `[11-MRI1.jpg] "inh ánh goi ý U bung trüng trái, O-RADS 5, nguy co ác tinh#90% (khá náng carcinom tuyén dich"` | 5 (U đặc xâm lấn / Carcinom tuyến). |
| morphology_class_mri | 12 | `[12-MRI1.jpg] "Hinh änh goi y U bung tru'ng phäi,O-RADS 4, nguy co äc tinh #50%(khä näng u té bao mam,.."` | 5 (U đặc xuất huyết / nghi u tế bào mầm). |
| o_rads_mri | 04 | `[4-MRI1.jpg] "TD U nang buong trung trai orads 4,nghi u quai chua truo'ng thanh."` | 3 (O-RADS 4 -> encoded 3). |
| o_rads_mri | 05 | ABSENT / Không có trong văn bản OCR | 2 (O-RADS 3 -> encoded 2). |
| o_rads_mri | 06 | ABSENT / Không có trong văn bản OCR | ABSENT (Không ghi điểm O-RADS trong text MRI ca 06). |
| o_rads_mri | 07 | `[7-MRI1.jpg] "Hinh ánh goi ý u buöng trúng trái, xép O-RADS 4: nguy co ác tinh# 50% (nghi u quái khöng truöng"` | 3 (O-RADS 4 -> encoded 3). |
| o_rads_mri | 08 | `[8-BBHC.jpg] "ORADS 4: nguy co äc tinh #50%"` | 3 (O-RADS 4 -> encoded 3). |
| o_rads_mri | 09 | `[9-BBHC.jpg] "MRIHinh anh goi y U buong trürngT,xép O-RADS 4,nguy co ac tinh#50%kha nang thuc"` | 3 (O-RADS 4 -> encoded 3). |
| o_rads_mri | 10 | `[10-MRI1.jpg] "Hinh änh goi ý U buöng trü'ng träi O-RADS 4, nguy co ác tinh#50% (khä näng u nhay u dang giáp"` | 3 (O-RADS 4 -> encoded 3). |
| o_rads_mri | 11 | `[11-MRI1.jpg] "inh ánh goi ý U bung trüng trái, O-RADS 5, nguy co ác tinh#90% (khá náng carcinom tuyén dich"` | 4 (O-RADS 5 -> encoded 4). |
| o_rads_mri | 12 | `[12-MRI1.jpg] "Hinh änh goi y U bung tru'ng phäi,O-RADS 4, nguy co äc tinh #50%(khä näng u té bao mam,.."` | 3 (O-RADS 4 -> encoded 3). |

---

## 2. PHÁT HIỆN ĐỊNH DẠNG MỚI QUA 9 CA BỆNH (CASE 04 ĐẾN CASE 12)

### 1. Phiếu Siêu âm Đa dạng & IOTA ADNEX tiếng Anh
- **Nhiều phiếu SA trong 1 ca:** Ở Case 04, 08, 09, 10, 11, 12 xuất hiện đồng thời từ 2 đến 4 phiếu siêu âm khác nhau (`SA1.jpg`, `SA2.jpg`, `SA3.jpg`, `SA ADNEX.jpg`).
- **Phiếu Siêu âm IOTA ADNEX bằng tiếng Anh (`9-SA ADNEX.jpg`, `12-SA ADNEX.jpg`):**
  - Chứa các trường dữ liệu hoàn toàn bằng tiếng Anh:
    ```text
    ADNEXmodelBenign tumor probability of benign ovarian tumour: 94.2%
    ADNEXmodelMalignantovarian tumour Risk of malignant ovarian tumour: 5.8%
    ADNEXmodelBorderline Risk of borderline ovarian tumour: 0.5%
    ADNEX modelStageI Risk of stage 1 ovarian tumour: 3.7%
    ADNEX model:Stage II -IV Risk of Stage II -IV ovarian tumour: 0.8%
    ADNEX modelMetastatic
    ```

### 2. Hai phiếu GPB riêng biệt trong cùng một ca mổ (`GPB1` và `GPB2`)
- **Xuất hiện ở Case 06 và Case 10:**
  - Case 06: `6-GPB1 buong trung.jpg` (Sinh thiết u buồng trứng) và `6-GPB2 tu cung.jpg` (Sinh thiết tử cung - phát hiện Carcinoma tuyến nội mạc tử cung).
  - Case 10: `10-GPB1.jpg` và `10-GPB2.jpg` (Sinh thiết 2 bệnh phẩm khác nhau: U buồng trứng và mô phúc mạc/tử cung).
- **Rủi ro:** Cần đảm bảo parser GPB nhận diện đúng cơ quan buồng trứng, đồng thời không bỏ sót các trường hợp có ung thư đồng thời ở cơ quan lân cận.

### 3. Dấu ấn khối u vượt ngưỡng đo (`> 10000.0`) và Viết tắt tiếng Anh
- **Case 11:** CA125 đạt giá trị cực cao ghi nhận là `> 10000.0` U/mL.
- **Biên bản hội chẩn (BBHC):** Ở Case 05, không có phiếu marker riêng, mà BBHC tóm tắt dạng `Tumor marker buöng trüng binh thung,Beta HCG: am tinh`.

### 4. Nhầm lẫn Ngữ cảnh Tử cung (U xơ, MLT) vs Buồng trứng
- **Kích thước U xơ Tử cung vs U Buồng trứng:** Case 06, 11, 12 đều có nhân xơ tử cung đi kèm (`#14x18x20mm`, `#22x16x22mm`, `#16x17x17mm`). Cần tránh lấy nhầm số đo tử cung cho u buồng trứng.
- **Tiền căn Vết mổ cũ (Mổ lấy thai):** Case 10, 11 ghi `Mo lay thai 2 lan` hoặc `Vet mo cu 2 lan`. Cần loại trừ để không tính thành tiền căn mổ u buồng trứng (`prior_ovarian_surgery = 0`).

### 5. Biến dạng Lỗi ký tự OCR nghiêm trọng ở từ khóa Phủ định & Y khoa
- Từ phủ định: `Khng`, `KhÖng`, `kh6ng`, `6ng có`, `<höng có`.
- Từ y khoa: `c6 bóng lung` (số 6 thay chữ ó), `khng chi` (chồi thành chi), `ó mdäc` (mất chữ c), `Tubi:` (tuổi thành tubi).
