"""MRI expert using the shared BaseExpert implementation."""

from config.schema_config import MODALITY_FEATURES
from models.base_expert import BaseExpert


class MRIExpert(BaseExpert):
    def __init__(self, model_type: str = "logistic", random_state: int = 42):
        super().__init__(
            feature_list=MODALITY_FEATURES["mri"],
            model_type=model_type,
            random_state=random_state,
            modality_name="mri",
        )
