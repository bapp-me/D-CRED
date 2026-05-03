from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .utils import ensure_dir


def reliability_plot(
    y_true: np.ndarray,
    probs_by_label: dict[str, np.ndarray],
    path: Path,
    n_bins: int = 10,
) -> None:
    ensure_dir(path.parent)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    plt.figure(figsize=(6, 5))
    plt.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    for label, probs in probs_by_label.items():
        xs, ys = [], []
        for start, end in zip(bins[:-1], bins[1:]):
            mask = (probs >= start) & (probs < end if end < 1 else probs <= end)
            if np.any(mask):
                xs.append(float(np.mean(probs[mask])))
                ys.append(float(np.mean(y_true[mask])))
        plt.plot(xs, ys, marker="o", label=label)
    plt.xlabel("Mean predicted default probability")
    plt.ylabel("Observed default rate")
    plt.title("Reliability diagram")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def default_rate_by_period(timestamp: pd.Series, y: pd.Series, path: Path) -> None:
    ensure_dir(path.parent)
    frame = pd.DataFrame({"issue_d": timestamp, "default": y}).dropna()
    if frame.empty:
        return
    monthly = frame.set_index("issue_d").resample("QE")["default"].mean()
    plt.figure(figsize=(8, 4))
    monthly.plot()
    plt.ylabel("Default rate")
    plt.xlabel("Issue quarter")
    plt.title("Lending Club default rate over time")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
