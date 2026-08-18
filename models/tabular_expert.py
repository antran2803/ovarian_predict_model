"""
Tabular Expert Model
Xử lý dữ liệu dạng bảng (Clinical, Biochemical).

Lộ trình model (theo thứ tự học):
  Bước 1: Logistic Regression  — XONG (Baseline tuyến tính)
  Bước 2: Random Forest        — XONG (Tree-based ensemble)
  Bước 3: LightGBM             — XONG (Native NaN handling & Native Categorical support)
  Bước 4: Late Fusion          — TODO (cần ≥ 2 expert)
"""

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
import pandas as pd
import numpy as np

# Các giá trị hợp lệ cho tham số model_type
VALID_MODEL_TYPES = ("logistic", "random_forest", "lightgbm")


class TabularExpert:
    def __init__(self, model_type: str = "logistic", random_state: int = 42):
        """
        Khởi tạo mô hình Tabular Expert.

        Tham số:
          model_type   : "logistic", "random_forest", hoặc "lightgbm"
          random_state : hạt giống ngẫu nhiên để kết quả tái lặp 100%

        LƯU Ý KỸ THUẬT:
          - "logistic" & "random_forest": Dùng Pipeline với SimpleImputer(median).
            Chỉ lọc các cột số (numeric) vì SimpleImputer không nhận cột text.
          - "lightgbm": Bỏ hoàn toàn SimpleImputer. Dùng Native Missing Value Handling
            và Native Categorical Support của LightGBM.
        """
        if model_type not in VALID_MODEL_TYPES:
            raise ValueError(
                f"model_type='{model_type}' không hợp lệ. "
                f"Chọn một trong: {VALID_MODEL_TYPES}"
            )

        self.model_type = model_type
        self.random_state = random_state
        self.feature_names = []
        self.categorical_levels_ = {}  # Lưu danh sách categories cố định khi fit()

        if model_type == "logistic":
            classifier = LogisticRegression(
                random_state=random_state,
                class_weight="balanced",
                max_iter=1000,
            )
            self.pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("classifier", classifier),
            ])
        elif model_type == "random_forest":
            classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=random_state,
                class_weight="balanced",
            )
            self.pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("classifier", classifier),
            ])
        else:  # lightgbm
            # LightGBM Classifier:
            #   - Native NaN Handling: Tự động học hướng phân nhánh tối ưu cho NaN tại mỗi nút cây.
            #   - class_weight='balanced': Tự động điều chỉnh trọng số lớp nghịch đảo tần suất
            #     để tối đa hóa Độ nhạy (Sensitivity), tránh âm tính giả (bỏ sót ác tính).
            #   - min_child_samples=1: Cho phép phân nhánh trên tập dữ liệu mẫu nhỏ (< 20 mẫu),
            #     ngăn mô hình thoái hóa thành 1 lá với xác suất 0.5 mặc định.
            #   - verbose=-1: Tắt log C++ nội bộ.
            self.lgbm = LGBMClassifier(
                n_estimators=100,
                class_weight="balanced",
                min_child_samples=1,
                random_state=random_state,
                verbose=-1,
            )
            self.pipeline = None  # LightGBM không cần sklearn Pipeline với Imputer

    def _select_numeric_cols(self, X: pd.DataFrame):
        """
        Lọc ra chỉ các cột số (int/float) cho Logistic và Random Forest
        vì SimpleImputer(median) không xử lý được cột text/category.
        """
        numeric_cols = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
        dropped = [c for c in X.columns if c not in numeric_cols]
        if dropped:
            print(
                f"  [INFO - {self.model_type}] Bỏ qua {len(dropped)} cột non-numeric "
                f"khi đưa vào SimpleImputer: {dropped}"
            )
        return X[numeric_cols], numeric_cols

    def _prepare_lightgbm_data(self, X: pd.DataFrame, is_fit: bool = True) -> pd.DataFrame:
        """
        Tiền xử lý dữ liệu dành riêng cho LightGBM:
          - Đổi các cột chuỗi/object/str sang kiểu `category`.
          - ĐẶC BIỆT QUAN TRỌNG: Lưu danh sách `categories` lúc fit() và ép lại
            y hệt lúc predict() để tránh sai lệch mã hóa số âm thầm.
        """
        X_copy = X.copy()
        
        if is_fit:
            self.categorical_levels_ = {}
            for col in X_copy.columns:
                if not pd.api.types.is_numeric_dtype(X_copy[col]):
                    X_copy[col] = X_copy[col].astype("category")
                    self.categorical_levels_[col] = X_copy[col].cat.categories.tolist()
        else:
            for col, categories in self.categorical_levels_.items():
                if col in X_copy.columns:
                    X_copy[col] = pd.Categorical(X_copy[col], categories=categories)
                    
        return X_copy

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Huấn luyện mô hình."""
        if self.model_type in ("logistic", "random_forest"):
            X_num, self.feature_names = self._select_numeric_cols(X)
            self.pipeline.fit(X_num, y)

            # Kiểm tra cột bị SimpleImputer xóa âm thầm
            imputer = self.pipeline.named_steps["imputer"]
            n_in = imputer.n_features_in_
            n_out = imputer.get_feature_names_out().shape[0]

            if n_in != n_out:
                dropped_cols = [
                    self.feature_names[i]
                    for i, stat in enumerate(imputer.statistics_)
                    if np.isnan(stat)
                ]
                print(
                    f"\n[CẢNH BÁO - {self.model_type}] SimpleImputer đã XÓA "
                    f"{len(dropped_cols)} cột toàn NaN: {dropped_cols}"
                )
        else:  # lightgbm
            self.feature_names = list(X.columns)
            X_lgbm = self._prepare_lightgbm_data(X, is_fit=True)
            self.lgbm.fit(X_lgbm, y)

        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Dự đoán xác suất ung thư P(cancer)."""
        if self.model_type in ("logistic", "random_forest"):
            X_num = X[self.feature_names]
            probas = self.pipeline.predict_proba(X_num)
        else:  # lightgbm
            X_lgbm = X[self.feature_names]
            X_lgbm_prep = self._prepare_lightgbm_data(X_lgbm, is_fit=False)
            probas = self.lgbm.predict_proba(X_lgbm_prep)

        return probas[:, 1]
