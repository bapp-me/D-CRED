from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)


EPS = 1e-7


def clip_probs(probs: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(probs, dtype=float), EPS, 1.0 - EPS)


def expected_calibration_error(
    y_true: np.ndarray,
    probs: np.ndarray,
    n_bins: int = 10,
) -> tuple[float, float]:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    for start, end in zip(bins[:-1], bins[1:]):
        if end == 1.0:
            mask = (probs >= start) & (probs <= end)
        else:
            mask = (probs >= start) & (probs < end)
        if not np.any(mask):
            continue
        conf = float(np.mean(probs[mask]))
        acc = float(np.mean(y_true[mask]))
        gap = abs(conf - acc)
        ece += gap * float(np.mean(mask))
        mce = max(mce, gap)
    return ece, mce


def classification_metrics(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float = 0.5,
    n_bins: int = 10,
) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    y_pred = (probs >= threshold).astype(int)
    ece, mce = expected_calibration_error(y_true, probs, n_bins=n_bins)
    metrics = {
        "roc_auc": _safe_metric(roc_auc_score, y_true, probs),
        "pr_auc": _safe_metric(average_precision_score, y_true, probs),
        "f1": _safe_metric(f1_score, y_true, y_pred),
        "balanced_accuracy": _safe_metric(balanced_accuracy_score, y_true, y_pred),
        "brier": _safe_metric(brier_score_loss, y_true, probs),
        "nll": _safe_metric(log_loss, y_true, probs, labels=[0, 1]),
        "ece": ece,
        "mce": mce,
    }
    return metrics


def _safe_metric(func, *args, **kwargs) -> float:
    try:
        return float(func(*args, **kwargs))
    except ValueError:
        return float("nan")


def metrics_row(
    dataset: str,
    split: str,
    model: str,
    calibration: str,
    partition: str,
    y_true: np.ndarray,
    probs: np.ndarray,
) -> dict[str, object]:
    row: dict[str, object] = {
        "dataset": dataset,
        "split": split,
        "model": model,
        "calibration": calibration,
        "partition": partition,
        "rows": int(len(y_true)),
        "default_rate": float(np.mean(y_true)),
    }
    row.update(classification_metrics(y_true, probs))
    return row


def bootstrap_ci(
    y_true: np.ndarray,
    probs: np.ndarray,
    metric_name: str,
    metric_func,
    n_bootstrap: int,
    seed: int,
) -> dict[str, float | str]:
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=int)
    probs = clip_probs(probs)
    values = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        value = metric_func(y_true[idx], probs[idx])
        if np.isfinite(value):
            values.append(float(value))
    if not values:
        return {
            "metric": metric_name,
            "mean": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }
    arr = np.asarray(values)
    return {
        "metric": metric_name,
        "mean": float(np.mean(arr)),
        "ci_low": float(np.quantile(arr, 0.025)),
        "ci_high": float(np.quantile(arr, 0.975)),
    }


def paired_bootstrap_delta_ci(
    baseline_values: np.ndarray,
    candidate_values: np.ndarray,
    metric_name: str,
    n_bootstrap: int,
    seed: int,
) -> dict[str, float | str]:
    rng = np.random.default_rng(seed)
    baseline_values = np.asarray(baseline_values, dtype=float)
    candidate_values = np.asarray(candidate_values, dtype=float)
    if len(baseline_values) != len(candidate_values):
        raise ValueError("baseline_values and candidate_values must have the same length.")

    deltas = []
    n = len(baseline_values)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        value = float(np.mean(candidate_values[idx] - baseline_values[idx]))
        if np.isfinite(value):
            deltas.append(value)
    if not deltas:
        return {
            "metric": metric_name,
            "delta_mean": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }
    arr = np.asarray(deltas)
    return {
        "metric": metric_name,
        "delta_mean": float(np.mean(arr)),
        "ci_low": float(np.quantile(arr, 0.025)),
        "ci_high": float(np.quantile(arr, 0.975)),
    }


def write_metric_table(path, rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return frame
