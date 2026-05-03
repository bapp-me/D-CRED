from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


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
