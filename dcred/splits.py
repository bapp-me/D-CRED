from __future__ import annotations

from collections import OrderedDict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


DEFAULT_ROLE_SPLIT_SHARES: "OrderedDict[str, float]" = OrderedDict(
    [
        ("model_train", 0.50),
        ("model_dev", 0.10),
        ("calibration_fit", 0.10),
        ("calibration_select", 0.10),
        ("policy_tune", 0.10),
        ("risk_calibration", 0.05),
        ("final_test", 0.05),
    ]
)


def stratified_60_20_20(
    frame: pd.DataFrame,
    target: pd.Series,
    seed: int,
) -> tuple[pd.Index, pd.Index, pd.Index]:
    train_idx, tmp_idx = train_test_split(
        frame.index,
        train_size=0.60,
        random_state=seed,
        stratify=target,
    )
    tmp_y = target.loc[tmp_idx]
    val_idx, test_idx = train_test_split(
        tmp_idx,
        train_size=0.50,
        random_state=seed,
        stratify=tmp_y,
    )
    return pd.Index(train_idx), pd.Index(val_idx), pd.Index(test_idx)


def temporal_60_20_20(
    frame: pd.DataFrame,
    timestamp: pd.Series,
) -> tuple[pd.Index, pd.Index, pd.Index]:
    valid = timestamp.notna()
    ordered = frame.loc[valid].assign(_dcred_timestamp=timestamp.loc[valid])
    ordered = ordered.sort_values("_dcred_timestamp", kind="mergesort")
    indices = ordered.index.to_numpy()
    n = len(indices)
    if n < 10:
        raise ValueError("Not enough timestamp-valid rows for temporal split.")
    cut_train = int(np.floor(n * 0.60))
    cut_val = int(np.floor(n * 0.80))
    return (
        pd.Index(indices[:cut_train]),
        pd.Index(indices[cut_train:cut_val]),
        pd.Index(indices[cut_val:]),
    )


def temporal_role_split(
    frame: pd.DataFrame,
    timestamp: pd.Series,
    shares: "OrderedDict[str, float]" | None = None,
) -> dict[str, pd.Index]:
    if shares is None:
        shares = DEFAULT_ROLE_SPLIT_SHARES
    total_share = float(sum(shares.values()))
    if not np.isclose(total_share, 1.0):
        raise ValueError(f"Role split shares must sum to 1.0, got {total_share:.6f}.")

    valid = timestamp.notna()
    ordered = frame.loc[valid].assign(_dcred_timestamp=timestamp.loc[valid])
    ordered = ordered.sort_values("_dcred_timestamp", kind="mergesort")
    indices = ordered.index.to_numpy()
    n = len(indices)
    if n < len(shares) * 2:
        raise ValueError("Not enough timestamp-valid rows for chronological role split.")

    role_indices: dict[str, pd.Index] = {}
    start = 0
    cumulative = 0.0
    items = list(shares.items())
    for i, (role, share) in enumerate(items):
        cumulative += float(share)
        if i == len(items) - 1:
            stop = n
        else:
            stop = int(np.floor(n * cumulative))
        if stop <= start:
            raise ValueError(f"Role split produced an empty partition for {role}.")
        role_indices[role] = pd.Index(indices[start:stop])
        start = stop
    return role_indices
