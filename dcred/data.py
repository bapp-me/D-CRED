from __future__ import annotations

import shutil
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import (
    GERMAN_CREDIT_URL,
    GERMAN_CREDIT_ZIP,
    LENDING_CLUB_FILENAME,
    LENDING_CLUB_MD5,
    LENDING_CLUB_URL,
    RAW_DATA_DIR,
    UCI_DEFAULT_URL,
    UCI_DEFAULT_ZIP,
)
from .utils import ensure_dir, log, md5sum


@dataclass(frozen=True)
class DatasetBundle:
    name: str
    frame: pd.DataFrame
    target: pd.Series
    timestamp: pd.Series | None
    exposure: pd.Series | None
    audit: pd.DataFrame
    numeric_features: list[str]
    categorical_features: list[str]
    text_feature: str | None = None


def download_file(url: str, destination: Path, expected_md5: str | None = None) -> Path:
    ensure_dir(destination.parent)
    if destination.exists():
        if expected_md5 and md5sum(destination) != expected_md5:
            log(f"Checksum mismatch for {destination.name}; re-downloading.")
            destination.unlink()
        else:
            return destination

    tmp = destination.with_suffix(destination.suffix + ".tmp")
    log(f"Downloading {url} -> {destination}")
    with urllib.request.urlopen(url) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp.replace(destination)

    if expected_md5:
        actual = md5sum(destination)
        if actual != expected_md5:
            raise RuntimeError(
                f"MD5 mismatch for {destination}: expected {expected_md5}, got {actual}"
            )
    return destination


def ensure_lending_club(raw_dir: Path = RAW_DATA_DIR) -> Path:
    return download_file(
        LENDING_CLUB_URL,
        raw_dir / LENDING_CLUB_FILENAME,
        expected_md5=LENDING_CLUB_MD5,
    )


def ensure_uci_default(raw_dir: Path = RAW_DATA_DIR) -> Path:
    zip_path = download_file(UCI_DEFAULT_URL, raw_dir / UCI_DEFAULT_ZIP)
    extract_dir = ensure_dir(raw_dir / "uci_default")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    matches = list(extract_dir.rglob("*.xls")) + list(extract_dir.rglob("*.xlsx"))
    if not matches:
        raise FileNotFoundError(f"No Excel file found after extracting {zip_path}")
    return matches[0]


def ensure_german_credit(raw_dir: Path = RAW_DATA_DIR) -> Path:
    zip_path = download_file(GERMAN_CREDIT_URL, raw_dir / GERMAN_CREDIT_ZIP)
    extract_dir = ensure_dir(raw_dir / "german_credit")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    matches = [p for p in extract_dir.rglob("german.data") if p.name == "german.data"]
    if not matches:
        raise FileNotFoundError(f"german.data not found after extracting {zip_path}")
    return matches[0]


def _normalize_columns(columns: Iterable[str]) -> list[str]:
    clean = []
    for col in columns:
        value = str(col).strip().replace(" ", "_").replace("-", "_")
        value = value.replace("/", "_").replace("(", "").replace(")", "")
        clean.append(value)
    return clean


def _coerce_binary_target(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int)
    text = series.astype(str).str.lower().str.strip()
    return text.isin({"1", "yes", "true", "default", "charged off", "bad"}).astype(int)


def load_lending_club(
    raw_dir: Path = RAW_DATA_DIR,
    max_rows: int | None = None,
    include_text: bool = False,
) -> DatasetBundle:
    csv_path = ensure_lending_club(raw_dir)
    frame = pd.read_csv(csv_path, nrows=max_rows, low_memory=False)
    frame.columns = _normalize_columns(frame.columns)

    lower_map = {col.lower(): col for col in frame.columns}
    target_col = lower_map.get("default")
    timestamp_col = lower_map.get("issue_d")
    if target_col is None:
        raise KeyError("Lending Club dataset must contain a Default target column.")
    if timestamp_col is None:
        raise KeyError("Lending Club dataset must contain issue_d for temporal splits.")

    frame[timestamp_col] = pd.to_datetime(frame[timestamp_col], errors="coerce")
    target = _coerce_binary_target(frame[target_col])

    allowed_numeric = [
        col
        for col in ["revenue", "dti_n", "loan_amnt", "fico_n", "experience_c"]
        if col in frame.columns
    ]
    allowed_categorical = [
        col
        for col in ["emp_length", "purpose", "home_ownership_n", "addr_state", "zip_code"]
        if col in frame.columns
    ]
    text_cols = [col for col in ["title", "desc"] if col in frame.columns]

    if include_text and text_cols:
        frame["text_all"] = (
            frame[text_cols].fillna("").astype(str).agg(" ".join, axis=1).str.strip()
        )
        text_feature = "text_all"
    else:
        text_feature = None

    audit = lending_feature_audit(frame.columns, include_text=include_text)
    keep_columns = [
        target_col,
        timestamp_col,
        *allowed_numeric,
        *allowed_categorical,
    ]
    if text_feature:
        keep_columns.append(text_feature)
    keep_columns = list(dict.fromkeys(keep_columns))
    frame = frame.loc[:, keep_columns].copy()
    target = _coerce_binary_target(frame[target_col])
    timestamp = frame[timestamp_col]
    exposure = frame["loan_amnt"] if "loan_amnt" in frame.columns else None

    return DatasetBundle(
        name="lending_club",
        frame=frame,
        target=target,
        timestamp=timestamp,
        exposure=exposure,
        audit=audit,
        numeric_features=allowed_numeric,
        categorical_features=allowed_categorical,
        text_feature=text_feature,
    )


def lending_feature_audit(columns: Iterable[str], include_text: bool = False) -> pd.DataFrame:
    rows = []
    for col in columns:
        lower = col.lower()
        if lower in {"default", "loan_status"}:
            role = "target"
            allowed = False
            reason = "Outcome label; never used as a feature."
        elif lower == "id":
            role = "administrative_id"
            allowed = False
            reason = "Identifier removed from model training."
        elif lower == "issue_d":
            role = "timestamp"
            allowed = False
            reason = "Used only for temporal split and drift summaries."
        elif lower in {"revenue", "dti_n", "loan_amnt", "fico_n", "experience_c"}:
            role = "allowed_application_numeric"
            allowed = True
            reason = "Application-time numeric feature in granting dataset."
        elif lower in {"emp_length", "purpose", "home_ownership_n", "addr_state", "zip_code"}:
            role = "allowed_application_categorical"
            allowed = True
            reason = "Application-time categorical feature in granting dataset."
        elif lower in {"title", "desc", "text_all"}:
            role = "application_text"
            allowed = include_text and lower == "text_all"
            reason = (
                "Optional text feature enabled by --include-text."
                if allowed
                else "Raw text kept out of default tabular benchmark; enable --include-text for NLP features."
            )
        else:
            role = "excluded_unknown_or_non_protocol"
            allowed = False
            reason = "Not part of the clean D-CRED protocol for this implementation."
        rows.append(
            {
                "feature": col,
                "role": role,
                "allowed_for_training": allowed,
                "exclusion_reason": "" if allowed else reason,
            }
        )
    return pd.DataFrame(rows)


def load_uci_default(raw_dir: Path = RAW_DATA_DIR) -> DatasetBundle:
    xls_path = ensure_uci_default(raw_dir)
    frame = pd.read_excel(xls_path, header=1)
    frame.columns = _normalize_columns(frame.columns)
    target_candidates = [col for col in frame.columns if "default" in col.lower()]
    if not target_candidates:
        raise KeyError("UCI Default target column not found.")
    target_col = target_candidates[-1]
    target = _coerce_binary_target(frame[target_col])
    feature_cols = [col for col in frame.columns if col not in {target_col, "ID"}]
    numeric_features = [col for col in feature_cols if pd.api.types.is_numeric_dtype(frame[col])]
    categorical_features = [col for col in feature_cols if col not in numeric_features]
    audit = pd.DataFrame(
        [
            {
                "feature": col,
                "role": "id" if col == "ID" else "reduced_protocol_feature",
                "allowed_for_training": col in feature_cols,
                "exclusion_reason": "Identifier removed." if col == "ID" else "",
            }
            for col in frame.columns
        ]
    )
    exposure = frame["LIMIT_BAL"] if "LIMIT_BAL" in frame.columns else None
    return DatasetBundle(
        name="uci_default",
        frame=frame,
        target=target,
        timestamp=None,
        exposure=exposure,
        audit=audit,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )


def load_german_credit(raw_dir: Path = RAW_DATA_DIR) -> DatasetBundle:
    data_path = ensure_german_credit(raw_dir)
    columns = [f"Attribute{i}" for i in range(1, 21)] + ["target"]
    frame = pd.read_csv(data_path, sep=r"\s+", header=None, names=columns, engine="python")
    target = (frame["target"].astype(int) == 2).astype(int)
    feature_cols = columns[:-1]
    numeric_features = [
        col for col in feature_cols if pd.api.types.is_numeric_dtype(frame[col])
    ]
    categorical_features = [col for col in feature_cols if col not in numeric_features]
    audit = pd.DataFrame(
        [
            {
                "feature": col,
                "role": "reduced_protocol_feature" if col != "target" else "target",
                "allowed_for_training": col != "target",
                "exclusion_reason": "" if col != "target" else "Outcome label.",
            }
            for col in columns
        ]
    )
    exposure = frame["Attribute5"]
    return DatasetBundle(
        name="german_credit",
        frame=frame,
        target=target,
        timestamp=None,
        exposure=exposure,
        audit=audit,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )


def dataset_summary(bundle: DatasetBundle) -> pd.DataFrame:
    y = bundle.target.astype(int)
    return pd.DataFrame(
        [
            {
                "dataset": bundle.name,
                "rows": int(len(y)),
                "features_numeric": len(bundle.numeric_features),
                "features_categorical": len(bundle.categorical_features),
                "text_feature": bool(bundle.text_feature),
                "default_rate": float(y.mean()),
                "n_default": int(y.sum()),
                "n_non_default": int((1 - y).sum()),
                "has_timestamp": bundle.timestamp is not None,
            }
        ]
    )


def summarize_splits(
    dataset_name: str,
    split_name: str,
    y_train: pd.Series,
    y_val: pd.Series,
    y_test: pd.Series,
    t_train: pd.Series | None = None,
    t_val: pd.Series | None = None,
    t_test: pd.Series | None = None,
) -> pd.DataFrame:
    rows = []
    for part, y_part, t_part in [
        ("train", y_train, t_train),
        ("validation", y_val, t_val),
        ("test", y_test, t_test),
    ]:
        row = {
            "dataset": dataset_name,
            "split": split_name,
            "partition": part,
            "rows": int(len(y_part)),
            "default_rate": float(np.mean(y_part)),
            "n_default": int(np.sum(y_part)),
        }
        if t_part is not None:
            row["start_date"] = str(pd.Series(t_part).min().date())
            row["end_date"] = str(pd.Series(t_part).max().date())
        rows.append(row)
    return pd.DataFrame(rows)
