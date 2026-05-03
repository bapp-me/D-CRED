from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from .metrics import clip_probs


@dataclass
class ProbabilityCalibrator:
    name: str
    model: object | None = None

    def transform(self, probs: np.ndarray) -> np.ndarray:
        probs = clip_probs(probs)
        if self.name == "raw":
            return probs
        if self.name == "sigmoid":
            logits = _logit(probs).reshape(-1, 1)
            return clip_probs(self.model.predict_proba(logits)[:, 1])
        if self.name == "isotonic":
            return clip_probs(self.model.predict(probs))
        raise ValueError(f"Unknown calibrator: {self.name}")


def fit_calibrators(y_val: np.ndarray, probs_val: np.ndarray) -> dict[str, ProbabilityCalibrator]:
    y_val = np.asarray(y_val, dtype=int)
    probs_val = clip_probs(probs_val)
    calibrators: dict[str, ProbabilityCalibrator] = {
        "raw": ProbabilityCalibrator("raw", None)
    }

    sigmoid = LogisticRegression(max_iter=1000, solver="lbfgs")
    sigmoid.fit(_logit(probs_val).reshape(-1, 1), y_val)
    calibrators["sigmoid"] = ProbabilityCalibrator("sigmoid", sigmoid)

    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(probs_val, y_val)
    calibrators["isotonic"] = ProbabilityCalibrator("isotonic", isotonic)
    return calibrators


def _logit(probs: np.ndarray) -> np.ndarray:
    probs = clip_probs(probs)
    return np.log(probs / (1.0 - probs))
