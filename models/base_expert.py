"""Shared implementation for modality-specific expert classifiers."""

from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


VALID_MODEL_TYPES = ("logistic", "random_forest", "lightgbm")


class BaseExpert:
    """Common model and preprocessing logic for all expert modalities."""

    def __init__(
        self,
        feature_list: Iterable[str],
        model_type: str = "logistic",
        random_state: int = 42,
        modality_name: Optional[str] = None,
    ):
        if model_type not in VALID_MODEL_TYPES:
            raise ValueError(
                f"model_type='{model_type}' không hợp lệ. "
                f"Chọn một trong: {VALID_MODEL_TYPES}"
            )

        self.feature_list = list(feature_list)
        if not self.feature_list:
            raise ValueError("feature_list không được rỗng")

        self.model_type = model_type
        self.random_state = random_state
        self.modality_name = modality_name
        self.feature_names = []
        self.categorical_levels_: Dict[str, list] = {}

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
            self.lgbm = None
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
            self.lgbm = None
        else:
            self.lgbm = LGBMClassifier(
                n_estimators=100,
                class_weight="balanced",
                min_child_samples=1,
                random_state=random_state,
                verbose=-1,
            )
            self.pipeline = None

    def _select_numeric_cols(self, X: pd.DataFrame):
        numeric_cols = [
            column for column in self.feature_list
            if pd.api.types.is_numeric_dtype(X[column])
        ]
        dropped = [column for column in self.feature_list if column not in numeric_cols]
        if dropped:
            print(
                f"  [INFO - {self.model_type}] Bỏ qua {len(dropped)} cột non-numeric "
                f"khi đưa vào SimpleImputer: {dropped}"
            )
        return X[numeric_cols], numeric_cols

    def _prepare_lightgbm_data(
        self, X: pd.DataFrame, is_fit: bool = True
    ) -> pd.DataFrame:
        X_copy = X[self.feature_list].copy()

        if is_fit:
            self.categorical_levels_ = {}
            for column in X_copy.columns:
                if not pd.api.types.is_numeric_dtype(X_copy[column]):
                    X_copy[column] = X_copy[column].astype("category")
                    self.categorical_levels_[column] = X_copy[column].cat.categories.tolist()
        else:
            for column, categories in self.categorical_levels_.items():
                X_copy[column] = pd.Categorical(X_copy[column], categories=categories)

        return X_copy

    def _validate_input(self, X: pd.DataFrame) -> None:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X phải là pandas.DataFrame")
        missing_columns = [column for column in self.feature_list if column not in X.columns]
        if missing_columns:
            raise ValueError(f"Thiếu feature bắt buộc: {missing_columns}")

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self._validate_input(X)
        if len(np.unique(y)) < 2:
            raise ValueError(
                "Cần ít nhất hai lớp nhãn khác nhau để huấn luyện expert."
            )

        if self.model_type in ("logistic", "random_forest"):
            X_num, self.feature_names = self._select_numeric_cols(X)
            if not self.feature_names:
                raise ValueError("Không có feature số để huấn luyện model này.")
            self.pipeline.fit(X_num, y)

            imputer = self.pipeline.named_steps["imputer"]
            if imputer.n_features_in_ != imputer.get_feature_names_out().shape[0]:
                dropped_cols = [
                    self.feature_names[index]
                    for index, statistic in enumerate(imputer.statistics_)
                    if np.isnan(statistic)
                ]
                print(
                    f"\n[CẢNH BÁO - {self.model_type}] SimpleImputer đã XÓA "
                    f"{len(dropped_cols)} cột toàn NaN: {dropped_cols}"
                )
        else:
            self.feature_names = list(self.feature_list)
            X_lgbm = self._prepare_lightgbm_data(X, is_fit=True)
            self.lgbm.fit(X_lgbm, y)

        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        self._validate_input(X)
        if not self.feature_names:
            raise RuntimeError("Expert chưa được fit.")

        if self.model_type in ("logistic", "random_forest"):
            probas = self.pipeline.predict_proba(X[self.feature_names])
        else:
            X_lgbm = self._prepare_lightgbm_data(X, is_fit=False)
            probas = self.lgbm.predict_proba(X_lgbm)
        return probas[:, 1]

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)

    def evaluate(self, X: pd.DataFrame, y: pd.Series, threshold: float = 0.5):
        predictions = self.predict(X, threshold=threshold)
        return {
            "accuracy": float(np.mean(predictions == np.asarray(y))),
            "n_samples": len(y),
        }
