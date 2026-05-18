from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import clip_probs


def cost_metrics(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float,
    false_negative_cost: float,
    false_positive_cost: float = 1.0,
    review_mask: np.ndarray | None = None,
    review_cost: float = 0.0,
) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    reject = probs >= threshold
    if review_mask is None:
        review_mask = np.zeros_like(y_true, dtype=bool)
    else:
        review_mask = np.asarray(review_mask, dtype=bool)
    auto = ~review_mask
    approve = (~reject) & auto
    auto_reject = reject & auto

    costs = cost_values(
        y_true,
        probs,
        threshold,
        false_negative_cost=false_negative_cost,
        false_positive_cost=false_positive_cost,
        review_mask=review_mask,
        review_cost=review_cost,
    )

    approved_count = int(np.sum(approve))
    rejected_count = int(np.sum(auto_reject))
    reviewed_count = int(np.sum(review_mask))
    return {
        "threshold": float(threshold),
        "expected_cost": float(np.mean(costs)),
        "approval_rate": float(np.mean(approve)),
        "rejection_rate": float(np.mean(auto_reject)),
        "review_rate": float(np.mean(review_mask)),
        "automation_rate": float(np.mean(auto)),
        "approved_default_rate": _safe_rate(y_true[approve] == 1),
        "rejected_good_rate": _safe_rate(y_true[auto_reject] == 0),
        "n_approved": approved_count,
        "n_rejected": rejected_count,
        "n_reviewed": reviewed_count,
    }


def cost_values(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float,
    false_negative_cost: float,
    false_positive_cost: float = 1.0,
    review_mask: np.ndarray | None = None,
    review_cost: float = 0.0,
) -> np.ndarray:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    reject = probs >= threshold
    if review_mask is None:
        review_mask = np.zeros_like(y_true, dtype=bool)
    else:
        review_mask = np.asarray(review_mask, dtype=bool)
    auto = ~review_mask
    approve = (~reject) & auto
    auto_reject = reject & auto

    costs = np.zeros_like(probs, dtype=float)
    costs[approve & (y_true == 1)] = false_negative_cost
    costs[auto_reject & (y_true == 0)] = false_positive_cost
    # Reviewed cases are modeled as paying review cost only; residual manual-review
    # error is an explicit reporting limitation, not estimated here.
    costs[review_mask] = review_cost
    return costs


def profit_metrics(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float,
    exposure: np.ndarray | None,
    lgd: float,
    roi: float,
) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    approve = probs < threshold
    if exposure is None:
        ead = np.ones_like(probs, dtype=float)
    else:
        ead = np.asarray(exposure, dtype=float)
        ead = np.nan_to_num(ead, nan=np.nanmedian(ead), posinf=np.nanmedian(ead))
    realized_profit = np.zeros_like(probs, dtype=float)
    realized_profit[approve & (y_true == 0)] = roi * ead[approve & (y_true == 0)]
    realized_profit[approve & (y_true == 1)] = -lgd * ead[approve & (y_true == 1)]
    expected_profit = np.zeros_like(probs, dtype=float)
    expected_profit[approve] = (
        (1.0 - probs[approve]) * roi * ead[approve]
        - probs[approve] * lgd * ead[approve]
    )
    return {
        "threshold": float(threshold),
        "mean_realized_profit": float(np.mean(realized_profit)),
        "mean_expected_profit": float(np.mean(expected_profit)),
        "approval_rate": float(np.mean(approve)),
        "approved_default_rate": _safe_rate(y_true[approve] == 1),
    }


def f1_optimal_threshold(y_true: np.ndarray, probs: np.ndarray) -> float:
    from sklearn.metrics import f1_score

    thresholds = np.linspace(0.01, 0.99, 99)
    values = [f1_score(y_true, probs >= threshold) for threshold in thresholds]
    return float(thresholds[int(np.nanargmax(values))])


def cost_threshold(false_negative_cost: float, false_positive_cost: float = 1.0) -> float:
    return float(false_positive_cost / (false_negative_cost + false_positive_cost))


def profit_threshold(lgd: float, roi: float) -> float:
    return float(roi / (roi + lgd))


def robust_cost_threshold(
    y_val: np.ndarray,
    probs_val: np.ndarray,
    cost_ratios: tuple[float, ...],
) -> float:
    thresholds = np.linspace(0.01, 0.99, 99)
    worst_costs = []
    for threshold in thresholds:
        scenario_costs = [
            cost_metrics(y_val, probs_val, threshold, ratio)["expected_cost"]
            for ratio in cost_ratios
        ]
        worst_costs.append(max(scenario_costs))
    return float(thresholds[int(np.argmin(worst_costs))])


def robust_profit_threshold(
    y_val: np.ndarray,
    probs_val: np.ndarray,
    exposure_val: np.ndarray | None,
    lgds: tuple[float, ...],
    rois: tuple[float, ...],
) -> float:
    thresholds = np.linspace(0.01, 0.99, 99)
    worst_profits = []
    for threshold in thresholds:
        scenario_profits = [
            profit_metrics(y_val, probs_val, threshold, exposure_val, lgd, roi)[
                "mean_realized_profit"
            ]
            for lgd in lgds
            for roi in rois
        ]
        worst_profits.append(min(scenario_profits))
    return float(thresholds[int(np.argmax(worst_profits))])


def decision_table(
    dataset: str,
    split: str,
    model: str,
    calibration: str,
    y_val: np.ndarray,
    probs_val: np.ndarray,
    y_test: np.ndarray,
    probs_test: np.ndarray,
    exposure_val: np.ndarray | None,
    exposure_test: np.ndarray | None,
    cost_ratios: tuple[float, ...],
    lgds: tuple[float, ...],
    rois: tuple[float, ...],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    y_select, probs_select, exposure_select = _threshold_selection_subset(
        y_val,
        probs_val,
        exposure_val,
        max_rows=50_000,
    )
    thresholds = {
        "fixed_0.5": 0.5,
        "f1_validation": f1_optimal_threshold(y_select, probs_select),
        "robust_cost": robust_cost_threshold(y_select, probs_select, cost_ratios),
        "robust_profit": robust_profit_threshold(
            y_select, probs_select, exposure_select, lgds, rois
        ),
    }
    for ratio in cost_ratios:
        thresholds[f"cost_{ratio:g}_to_1"] = cost_threshold(ratio)
    for lgd in lgds:
        for roi in rois:
            thresholds[f"profit_lgd_{lgd:g}_roi_{roi:g}"] = profit_threshold(lgd, roi)

    for policy, threshold in thresholds.items():
        for ratio in cost_ratios:
            row = {
                "dataset": dataset,
                "split": split,
                "model": model,
                "calibration": calibration,
                "policy": policy,
                "scenario": f"cost_fn_{ratio:g}_fp_1",
                "false_negative_cost": ratio,
                "false_positive_cost": 1.0,
            }
            row.update(cost_metrics(y_test, probs_test, threshold, ratio))
            rows.append(row)
        for lgd in lgds:
            for roi in rois:
                row = {
                    "dataset": dataset,
                    "split": split,
                    "model": model,
                    "calibration": calibration,
                    "policy": policy,
                    "scenario": f"profit_lgd_{lgd:g}_roi_{roi:g}",
                    "lgd": lgd,
                    "roi": roi,
                }
                row.update(profit_metrics(y_test, probs_test, threshold, exposure_test, lgd, roi))
                rows.append(row)
    return pd.DataFrame(rows)


def _threshold_selection_subset(
    y_val: np.ndarray,
    probs_val: np.ndarray,
    exposure_val: np.ndarray | None,
    max_rows: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    y_val = np.asarray(y_val, dtype=int)
    probs_val = clip_probs(probs_val)
    if len(y_val) <= max_rows:
        return y_val, probs_val, exposure_val
    rng = np.random.default_rng(0)
    idx = rng.choice(len(y_val), size=max_rows, replace=False)
    idx.sort()
    exposure_subset = None if exposure_val is None else np.asarray(exposure_val)[idx]
    return y_val[idx], probs_val[idx], exposure_subset


def _safe_rate(mask: np.ndarray) -> float:
    if len(mask) == 0:
        return float("nan")
    return float(np.mean(mask))
