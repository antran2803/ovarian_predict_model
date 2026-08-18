"""
Late Fusion Module.
Nhận xác suất P(cancer) từ các Expert khả dụng, tổng hợp thành 1 xác suất cuối.

Chiến lược hiện hỗ trợ:
  - "simple_average": Trung bình cộng đơn giản các Expert khả dụng.
  - (reserved) "weighted_average": Trung bình có trọng số — khi có dữ liệu thật
    để tối ưu trọng số, truyền vào qua tham số weights.

LƯU Ý KIẾN TRÚC:
  Module này CHỈ lo kết hợp output của các Expert.
  Không gọi fit/predict bên trong — P(cancer) phải được tính bên ngoài
  (ví dụ: từ LOOCV) trước khi truyền vào đây.
"""


class LateFusion:
    """
    Late Fusion Module — kết hợp xác suất từ nhiều Expert độc lập.

    Cách dùng:
        fuser = LateFusion()
        result = fuser.fuse(
            expert_probas={"tabular": 0.87, "us": None, "mri": 0.91},
            strategy="simple_average",
        )
        # result = {"P_fusion": 0.89, "experts_used": ["mri", "tabular"], "strategy": "simple_average"}
    """

    VALID_STRATEGIES = ("simple_average",)

    def fuse(
        self,
        expert_probas: dict,
        weights: dict = None,
        strategy: str = "simple_average",
    ) -> dict:
        """
        Tổng hợp xác suất từ các Expert khả dụng.

        Tham số:
          expert_probas : dict ánh xạ tên Expert → P(cancer) hoặc None.
                          Ví dụ: {"tabular": 0.87, "us": None, "mri": 0.91}
          weights       : dict ánh xạ tên Expert → trọng số (reserved, chưa dùng).
                          Khi strategy="simple_average", tham số này bị bỏ qua.
          strategy      : chiến lược fusion. Hiện chỉ hỗ trợ "simple_average".

        Trả về:
          dict với các key:
            "P_fusion"     : float hoặc None nếu không có Expert nào khả dụng.
            "experts_used" : list tên Expert đã được dùng (theo thứ tự alphabet).
            "strategy"     : chiến lược đã áp dụng.

        QUAN TRỌNG: Trả về P_fusion=None (không phải 0.5 hay bất kỳ giá trị nào)
        khi không có Expert nào khả dụng — để caller tự hiển thị "không đủ dữ liệu
        để dự đoán" thay vì âm thầm ra 1 con số vô nghĩa.
        """
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"strategy='{strategy}' không hợp lệ. Chọn một trong: {self.VALID_STRATEGIES}"
            )

        # Lọc chỉ lấy Expert có giá trị thực (không None)
        available = {
            name: prob
            for name, prob in expert_probas.items()
            if prob is not None
        }

        # Không có Expert nào khả dụng → không dự đoán được
        if not available:
            return {
                "P_fusion": None,
                "experts_used": [],
                "strategy": strategy,
            }

        experts_used = sorted(available.keys())

        if strategy == "simple_average":
            p_fusion = sum(available[e] for e in experts_used) / len(experts_used)
        # (reserved) elif strategy == "weighted_average": ...

        return {
            "P_fusion": round(p_fusion, 4),
            "experts_used": experts_used,
            "strategy": strategy,
        }
