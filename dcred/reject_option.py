from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .metrics import clip_probs


DEFAULT_REVIEW_COSTS = (0.02, 0.05, 0.10, 0.20, 0.50)
DEFAULT_HUMAN_RESIDUAL_RHOS = (0.0, 0.10, 0.25, 0.50)
DEFAULT_CAPACITY_FRACTIONS = (0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50)
DEFAULT_UNCERTAINTY_BANDS = (0.02, 0.05, 0.10)


@dataclass(frozen=True)
class CostScenario:
    false_negative_cost: float = 5.0
    false_positive_cost: float = 1.0
    review_cost: float = 0.10
    human_residual_rho: float = 0.10

    @property
    def scenario_id(self) -> str:
        return (
            f"fn_{self.false_negative_cost:g}_fp_{self.false_positive_cost:g}"
            f"_review_{self.review_cost:g}_rho_{self.human_residual_rho:g}"
        )


def cost_components(
    probs: np.ndarray,
    scenario: CostScenario,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    probs = clip_probs(probs)
    approve_cost = scenario.false_negative_cost * probs
    deny_cost = scenario.false_positive_cost * (1.0 - probs)
    auto_cost = np.minimum(approve_cost, deny_cost)
    manual_cost = scenario.review_cost + scenario.human_residual_rho * auto_cost
    return approve_cost, deny_cost, manual_cost


def no_review_masks(
    probs: np.ndarray,
    scenario: CostScenario,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    approve_cost, deny_cost, _ = cost_components(probs, scenario)
    approve_mask = approve_cost <= deny_cost
    review_mask = np.zeros_like(approve_mask, dtype=bool)
    reject_mask = ~approve_mask
    return approve_mask, reject_mask, review_mask


def reject_option_masks(
    probs: np.ndarray,
    scenario: CostScenario,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    approve_mask = (approve_cost <= deny_cost) & (approve_cost <= manual_cost)
    reject_mask = (deny_cost < approve_cost) & (deny_cost <= manual_cost)
    review_mask = ~(approve_mask | reject_mask)
    return approve_mask, reject_mask, review_mask


def capacity_review_mask(
    probs: np.ndarray,
    scenario: CostScenario,
    capacity_fraction: float,
) -> np.ndarray:
    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    auto_cost = np.minimum(approve_cost, deny_cost)
    benefit = auto_cost - manual_cost
    positive = np.flatnonzero(benefit > 0.0)
    max_reviews = int(np.floor(len(probs) * capacity_fraction))
    review_mask = np.zeros(len(probs), dtype=bool)
    if max_reviews <= 0 or len(positive) == 0:
        return review_mask
    ranked = positive[np.argsort(benefit[positive])[::-1]]
    review_mask[ranked[:max_reviews]] = True
    return review_mask


def auto_masks_with_review(
    probs: np.ndarray,
    scenario: CostScenario,
    review_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    approve_mask, reject_mask, _ = no_review_masks(probs, scenario)
    review_mask = np.asarray(review_mask, dtype=bool)
    return approve_mask & ~review_mask, reject_mask & ~review_mask, review_mask


def evaluate_policy(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
    policy: str,
    approve_mask: np.ndarray,
    reject_mask: np.ndarray,
    review_mask: np.ndarray,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    approve_mask = np.asarray(approve_mask, dtype=bool)
    reject_mask = np.asarray(reject_mask, dtype=bool)
    review_mask = np.asarray(review_mask, dtype=bool)
    if not np.all((approve_mask.astype(int) + reject_mask.astype(int) + review_mask.astype(int)) == 1):
        raise ValueError(f"Policy masks must form exactly one action per row for {policy}.")

    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    expected_cost = np.zeros_like(probs, dtype=float)
    expected_cost[approve_mask] = approve_cost[approve_mask]
    expected_cost[reject_mask] = deny_cost[reject_mask]
    expected_cost[review_mask] = manual_cost[review_mask]

    realized_cost = np.zeros_like(probs, dtype=float)
    realized_cost[approve_mask & (y_true == 1)] = scenario.false_negative_cost
    realized_cost[reject_mask & (y_true == 0)] = scenario.false_positive_cost
    realized_cost[review_mask] = manual_cost[review_mask]

    row: dict[str, object] = {
        "policy": policy,
        "scenario": scenario.scenario_id,
        "false_negative_cost": scenario.false_negative_cost,
        "false_positive_cost": scenario.false_positive_cost,
        "review_cost": scenario.review_cost,
        "human_residual_rho": scenario.human_residual_rho,
        "rows": int(len(y_true)),
        "expected_cost": float(np.mean(expected_cost)),
        "realized_cost": float(np.mean(realized_cost)),
        "approval_rate": float(np.mean(approve_mask)),
        "rejection_rate": float(np.mean(reject_mask)),
        "review_rate": float(np.mean(review_mask)),
        "automation_rate": float(np.mean(~review_mask)),
        "approved_default_rate": _safe_rate(y_true[approve_mask] == 1),
        "rejected_good_rate": _safe_rate(y_true[reject_mask] == 0),
        "n_approved": int(np.sum(approve_mask)),
        "n_rejected": int(np.sum(reject_mask)),
        "n_reviewed": int(np.sum(review_mask)),
    }
    if extra:
        row.update(extra)
    return row


def evaluate_no_review(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
) -> dict[str, object]:
    return evaluate_policy(
        y_true,
        probs,
        scenario,
        "no_review_cost_sensitive",
        *no_review_masks(probs, scenario),
    )


def evaluate_all_review(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
) -> dict[str, object]:
    review_mask = np.ones(len(probs), dtype=bool)
    approve_mask = np.zeros(len(probs), dtype=bool)
    reject_mask = np.zeros(len(probs), dtype=bool)
    return evaluate_policy(
        y_true,
        probs,
        scenario,
        "all_review",
        approve_mask,
        reject_mask,
        review_mask,
    )


def evaluate_reject_option(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
) -> dict[str, object]:
    return evaluate_policy(
        y_true,
        probs,
        scenario,
        "cost_aware_reject_option",
        *reject_option_masks(probs, scenario),
    )


def evaluate_capacity_grid(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
    capacity_fractions: tuple[float, ...] = DEFAULT_CAPACITY_FRACTIONS,
) -> list[dict[str, object]]:
    rows = []
    for fraction in capacity_fractions:
        review_mask = capacity_review_mask(probs, scenario, fraction)
        rows.append(
            evaluate_policy(
                y_true,
                probs,
                scenario,
                "capacity_aware_deferral",
                *auto_masks_with_review(probs, scenario, review_mask),
                extra={"capacity_fraction": fraction},
            )
        )
    return rows


def evaluate_review_mask_policy(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
    policy: str,
    review_mask: np.ndarray,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    return evaluate_policy(
        y_true,
        probs,
        scenario,
        policy,
        *auto_masks_with_review(probs, scenario, review_mask),
        extra=extra,
    )


def add_reference_savings(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["savings_vs_no_review"] = np.nan
    result["savings_vs_all_review"] = np.nan
    keys = ["scenario"]
    for _, group in result.groupby(keys, dropna=False):
        no_review = group.loc[group["policy"] == "no_review_cost_sensitive", "expected_cost"]
        all_review = group.loc[group["policy"] == "all_review", "expected_cost"]
        idx = group.index
        if not no_review.empty:
            result.loc[idx, "savings_vs_no_review"] = float(no_review.iloc[0]) - result.loc[
                idx, "expected_cost"
            ]
        if not all_review.empty:
            result.loc[idx, "savings_vs_all_review"] = float(all_review.iloc[0]) - result.loc[
                idx, "expected_cost"
            ]
    return result


def _safe_rate(mask: np.ndarray) -> float:
    if len(mask) == 0:
        return float("nan")
    return float(np.mean(mask))
