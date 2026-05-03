from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .decision import cost_metrics
from .metrics import clip_probs


def conformal_quantile(y_cal: np.ndarray, probs_cal: np.ndarray, alpha: float) -> float:
    y_cal = np.asarray(y_cal, dtype=int)
    probs_cal = clip_probs(probs_cal)
    true_probs = np.where(y_cal == 1, probs_cal, 1.0 - probs_cal)
    scores = 1.0 - true_probs
    n = len(scores)
    q_level = min(1.0, math.ceil((n + 1) * (1.0 - alpha)) / n)
    return float(np.quantile(scores, q_level, method="higher"))


def conformal_sets(probs: np.ndarray, q_hat: float) -> tuple[np.ndarray, np.ndarray]:
    probs = clip_probs(probs)
    include_non_default = probs <= q_hat
    include_default = (1.0 - probs) <= q_hat
    return include_non_default, include_default


def selective_table(
    dataset: str,
    split: str,
    model: str,
    calibration: str,
    y_cal: np.ndarray,
    probs_cal: np.ndarray,
    y_test: np.ndarray,
    probs_test: np.ndarray,
    threshold: float,
    alphas: tuple[float, ...],
    false_negative_cost: float,
    review_cost_multipliers: tuple[float, ...] = (0.05, 0.10, 0.20),
    uncertainty_bands: tuple[float, ...] = (0.02, 0.05, 0.10),
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    y_test = np.asarray(y_test, dtype=int)
    probs_test = clip_probs(probs_test)

    for band in uncertainty_bands:
        review_mask = np.abs(probs_test - threshold) <= band
        for mult in review_cost_multipliers:
            row = {
                "dataset": dataset,
                "split": split,
                "model": model,
                "calibration": calibration,
                "method": "uncertainty_band",
                "alpha": np.nan,
                "band": band,
                "review_cost_multiplier": mult,
            }
            row.update(
                cost_metrics(
                    y_test,
                    probs_test,
                    threshold,
                    false_negative_cost=false_negative_cost,
                    review_mask=review_mask,
                    review_cost=mult * false_negative_cost,
                )
            )
            row["coverage"] = np.nan
            rows.append(row)

    for alpha in alphas:
        q_hat = conformal_quantile(y_cal, probs_cal, alpha)
        include_non_default, include_default = conformal_sets(probs_test, q_hat)
        valid = include_non_default | include_default
        review_mask = (~valid) | (include_non_default & include_default)
        auto_approve = include_non_default & (~include_default) & (probs_test < threshold)
        auto_reject = include_default & (~include_non_default)
        review_mask = review_mask | (include_non_default & (~include_default) & ~auto_approve)
        review_mask = review_mask | (include_default & (~include_non_default) & ~auto_reject)
        true_in_set = ((y_test == 0) & include_non_default) | ((y_test == 1) & include_default)
        for mult in review_cost_multipliers:
            row = {
                "dataset": dataset,
                "split": split,
                "model": model,
                "calibration": calibration,
                "method": "split_conformal",
                "alpha": alpha,
                "band": np.nan,
                "q_hat": q_hat,
                "review_cost_multiplier": mult,
                "coverage": float(np.mean(true_in_set)),
            }
            row.update(
                cost_metrics(
                    y_test,
                    probs_test,
                    threshold,
                    false_negative_cost=false_negative_cost,
                    review_mask=review_mask,
                    review_cost=mult * false_negative_cost,
                )
            )
            rows.append(row)
    return pd.DataFrame(rows)
