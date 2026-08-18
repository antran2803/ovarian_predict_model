"""
Nơi DUY NHẤT định nghĩa:
- Ngưỡng missing tối đa cho phép từng modality
- Danh sách + THỨ TỰ feature cố định của từng modality

Khi bệnh viện đổi ngưỡng hoặc thêm/bớt feature → chỉ sửa file này,
không đụng vào logic ở core/.

--- LỊCH SỬ THAY ĐỔI SCHEMA ---
2026-08-15 (v1): 2 clinical + 5 biochemical + 8 ultrasound + 8 mri
2026-08-15 (v2): Cập nhật theo Data_dictionary trong du_lieu_benh_nhan_ubt.xlsx:
  - clinical: thêm 7 trường mới từ data dictionary bệnh viện
  - ultrasound: thêm 6 trường mới (laterality, solid_component_present,
    multilocular, irregular_wall_or_septa, vascularity_description,
    iota_adnex_available)
  - mri: đổi tên + kiểu 2 trường:
      DWI_ADC (float mm²/s) → restricted_diffusion (binary 0/1)
      septa_thickness (float mm) → thick_septa (binary 0/1)
  - biochemical: GIỮ NGUYÊN key riêng (tiện cho cấu trúc dữ liệu),
    nhưng ngưỡng missing áp dụng GỘP cùng clinical — xem MISSING_THRESHOLD
2026-08-15 (v3): Chỉnh encoding theo tài liệu nghiên cứu chính thức:
  - prior_ovarian_surgery: ordinal 0/1/2/3 (không phải binary)
  - TIC: ordinal 0/1/2 (không phải 1-3)
  - o_rads_mri: ordinal 0-4 (không phải 1-5)
  - clinical+biochemical: cùng 1 ngưỡng missing 30% (theo mục 2.3.4.1)
2026-08-15 (v4): GỘP "clinical" + "biochemical" → 1 nhóm duy nhất "tabular" (14 biến).
  - Theo mục 2.3.4.1: đây là MỘT nhóm thống nhất, 30% ngưỡng chung.
  - Loại bỏ COMBINED_CLINICAL_BIOCHEMICAL_THRESHOLD (không cần nữa).
  - Tất cả công cụ dùng key "tabular" trong dữ liệu vào (data, scripts).

QUAN TRỌNG: Thứ tự feature trong mỗi modality là CỐ ĐỊNH.
feature_mask phụ thuộc vào thứ tự này — thêm feature mới phải thêm
vào CUỐI danh sách để không làm hỏng mask của data cũ đã lưu.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Ngưỡng missing tối đa cho phép
# Nguồn: mục 2.3.4.1 tài liệu nghiên cứu chính thức
# ─────────────────────────────────────────────────────────────────────────────
MISSING_THRESHOLD = {
    # tabular: nhóm lâm sàng + sinh hóa gộp (14 biến).
    # Tiêu chuẩn loại trừ (mục 2.3.4.1): loại bệnh nhân nếu tỷ lệ khuyết thiếu
    # vượt quá 30% tổng số biến (tối đa 4/14 biến được phép None).
    "tabular": 0.30,

    # Ultrasound: 25% TẠM ĐẶT — chưa có quy định rõ trong tài liệu nghiên cứu.
    # Với 14 trường, 25% = tối đa 3-4 trường được None.
    "ultrasound": 0.25,

    # MRI: 25% TẠM ĐẶT — chưa có quy định rõ trong tài liệu nghiên cứu.
    # Với 8 trường, 25% = tối đa 2 trường được None.
    "mri": 0.25,
}


# ─────────────────────────────────────────────────────────────────────────────
# Danh sách + thứ tự feature cố định từng modality
# ─────────────────────────────────────────────────────────────────────────────
MODALITY_FEATURES = {

    # --- TABULAR (14 trường) ---
    # Nhóm duy nhất gộp Lâm sàng (9) + Sinh hóa (5) theo tài liệu nghiên cứu
    # mục 2.5.1.1 và 2.3.4.1 (một ngưỡng missing chung 30%).
    # Nguồn: thu thập trước phẫu thuật từ hồ sơ bệnh án
    "tabular": [
        # -- Lâm sàng (9 biến) --
        "age",                          # Tuổi (năm, integer)
        "menopause",                    # Tình trạng mãn kinh (binary 0/1)
        "pregnancy_status",             # Tình trạng thai nghén (binary 0/1)
        "bilateral_lesion",             # Tổn thương hai bên buồng trứng (binary 0/1)
        "months_detection_to_surgery",  # Thời gian phát hiện → phẫu thuật (tháng, float)
        "prior_ovarian_surgery",        # Tiền căn mổ u BT: ordinal 0/1/2/3
                                        #   0: Không có tiền căn phẫu thuật u BT
                                        #   1: Có tiền căn phẫu thuật nhưng không rõ kết quả GPB
                                        #   2: Có tiền căn phẫu thuật, GPB là u lành tính
                                        #   3: Có tiền căn phẫu thuật, GPB là u giáp biên ác
        "other_cancer_history",         # Tiền căn ung thư khác (binary 0/1)
        "other_cancer_primary_site",    # Trường văn bản phụ trợ (str, NOT a standalone ML feature)
                                        # → ghi nhận vị trí GPB nguyên phát khi other_cancer_history=1
                                        # → None nếu other_cancer_history=0
        "oncology_center_flag",         # BV/Trung tâm ung bướu phụ khoa (binary 0/1)
        # -- Sinh hóa (5 biến) --
        "CA125",        # CA-125 (U/mL, float)
        "HE4",          # HE4 (pmol/L, float)
        "AFP",          # AFP (ng/mL, float)
        "beta_hCG",     # β-hCG (mIU/mL, float)
        "ROMA",         # ROMA (%, float)
    ],

    # --- ULTRASOUND IOTA (14 trường) ---
    # Nguồn: phiếu siêu âm trước mổ (IOTA protocol)
    "ultrasound": [
        # 8 trường IOTA cốt lõi (giữ nguyên từ v1, KHÔNG đổi thứ tự)
        "lesion_max_diameter_mm",   # Đường kính lớn nhất khối u (mm, float)
        "solid_max_diameter_mm",    # Đường kính lớn nhất phần đặc (mm, float)
        "papillary_count",          # Số chồi (ordinal 0-4, 0=không có)
        "more_than_10_locules",     # Trên 10 thùy (binary 0/1)
        "acoustic_shadow",          # Bóng lưng (binary 0/1)
        "ascites",                  # Dịch ổ bụng (binary 0/1)
        "doppler_score",            # Điểm màu Doppler (ordinal 1-4)
        "morphology_class",         # Hình thái khối u IOTA (category 1-7)
        # 6 trường mới từ data_dictionary v2 (thêm vào CUỐI để giữ mask cũ)
        "laterality",               # Bên tổn thương (str: "left"/"right"/"bilateral")
        "solid_component_present",  # Có thành phần đặc (binary 0/1)
        "multilocular",             # Đa thùy (binary 0/1)
        "irregular_wall_or_septa",  # Thành/vách không đều (binary 0/1)
        "vascularity_description",  # Mô tả tưới máu (str/category)
        "iota_adnex_available",     # Có kết quả IOTA ADNEX (binary 0/1)
    ],

    # --- MRI O-RADS (8 trường) ---
    # Nguồn: MRI trước mổ (O-RADS protocol)
    # THAY ĐỔI TỪ v1:
    #   - DWI_ADC (float mm²/s) → restricted_diffusion (binary 0/1)
    #     0 = tín hiệu thấp hoặc không hạn chế khuếch tán
    #     1 = tín hiệu cao trên DWI + thấp trên ADC (hạn chế khuếch tán rõ)
    #   - septa_thickness (float mm) → thick_septa (binary 0/1)
    #     0 = không có vách hoặc vách mỏng <3mm
    #     1 = vách dày ≥3mm
    "mri": [
        "solid_component",          # Có mô đặc (binary 0/1)
        "solid_max_diameter_mm",    # Đường kính lớn nhất phần đặc MRI (mm, float)
        "TIC",                      # Đường cong bắt thuốc TIC (ordinal 0/1/2)
                                        #   0: Bắt thuốc kém/chậm (Type 1)
                                        #   1: Bắt thuốc trung bình (Type 2)
                                        #   2: Bắt thuốc mạnh/sớm (Type 3)
        "restricted_diffusion",     # Hạn chế khuếch tán DWI/ADC (binary 0/1) [ĐỔI TỪ DWI_ADC]
        "thick_septa",              # Vách dày ≥3mm (binary 0/1) [ĐỔI TỪ septa_thickness]
        "ascites_mri",              # Dịch tự do ổ bụng MRI (binary 0/1)
        "morphology_class_mri",     # Hình thái khối u MRI (category 1-7)
        "o_rads_mri",               # O-RADS MRI: ordinal 0-4 (mã hóa từ điểm số gốc)
                                        #   0=O-RADS 1 | 1=O-RADS 2 | 2=O-RADS 3
                                        #   3=O-RADS 4 | 4=O-RADS 5
    ],
}

MODALITY_NAMES = list(MODALITY_FEATURES.keys())
