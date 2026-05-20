from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.metrics import (
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dcred.config import OUTPUT_DIR, RAW_DATA_DIR
from dcred.splits import DEFAULT_ROLE_SPLIT_SHARES
from dcred.utils import ensure_dir, now_stamp, write_json, write_text


GOOD_STATUSES = {
    "Fully Paid",
    "Does not meet the credit policy. Status:Fully Paid",
}
BAD_STATUSES = {
    "Charged Off",
    "Default",
    "Does not meet the credit policy. Status:Charged Off",
}
TERMINAL_STATUSES = GOOD_STATUSES | BAD_STATUSES

CASHFLOW_COLUMNS = [
    "funded_amnt",
    "total_rec_prncp",
    "total_rec_int",
    "total_rec_late_fee",
    "recoveries",
    "collection_recovery_fee",
]

CHEAP_NUMERIC = ["loan_amnt", "annual_inc"]
CHEAP_CATEGORICAL = ["term", "emp_length", "purpose", "home_ownership", "addr_state", "zip_code"]
REVIEW_NUMERIC = [
    "dti",
    "delinq_2yrs",
    "inq_last_6mths",
    "mths_since_last_delinq",
    "mths_since_last_record",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
    "collections_12_mths_ex_med",
    "mths_since_last_major_derog",
    "acc_now_delinq",
    "tot_coll_amt",
    "tot_cur_bal",
    "open_acc_6m",
    "open_act_il",
    "open_il_12m",
    "open_il_24m",
    "mths_since_rcnt_il",
    "total_bal_il",
    "il_util",
    "open_rv_12m",
    "open_rv_24m",
    "max_bal_bc",
    "all_util",
    "total_rev_hi_lim",
    "inq_fi",
    "inq_last_12m",
    "acc_open_past_24mths",
    "avg_cur_bal",
    "bc_open_to_buy",
    "bc_util",
    "num_accts_ever_120_pd",
    "num_actv_bc_tl",
    "num_actv_rev_tl",
    "num_bc_sats",
    "num_bc_tl",
    "num_il_tl",
    "num_op_rev_tl",
    "num_rev_accts",
    "num_rev_tl_bal_gt_0",
    "num_sats",
    "pct_tl_nvr_dlq",
    "percent_bc_gt_75",
    "pub_rec_bankruptcies",
    "tax_liens",
    "tot_hi_cred_lim",
    "total_bal_ex_mort",
    "total_bc_limit",
    "total_il_high_credit_limit",
]
REVIEW_CATEGORICAL = ["verification_status", "application_type", "initial_list_status"]

CAPACITY_FRACTIONS = (0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50)
DIRECT_REVIEW_COSTS = (5.0, 10.0, 20.0, 30.0, 50.0, 100.0)
LOSS_PROFIT_RATIOS = (1.0, 2.0, 5.0, 10.0, 11.4, 15.0, 20.0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run dean-proposed Lending Club cash-flow and feature acquisition experiments."
    )
    parser.add_argument(
        "--loan-csv",
        default=str(RAW_DATA_DIR / "lending_club" / "loan.csv"),
        help="Path to Lending Club accepted-loan CSV with cash-flow columns.",
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--run-name", default="dean_cashflow_full")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--primary-review-cost", type=float, default=10.0)
    parser.add_argument("--hourly-wage", type=float, default=35.66)
    parser.add_argument("--target-scale", type=float, default=1000.0)
    args = parser.parse_args()

    np.random.seed(args.seed)
    output_dir = ensure_dir(Path(args.output_dir) / args.run_name)
    loan_path = Path(args.loan_csv)
    raw_columns = _read_header(loan_path)
    feature_groups = _resolve_feature_groups(raw_columns)
    frame = _load_terminal_frame(loan_path, raw_columns, feature_groups, args.max_rows)
    _write_audits(output_dir, raw_columns, feature_groups, frame)

    role_indices = _month_blocked_role_split(frame, frame["issue_d"])
    _split_summary(frame, role_indices).to_csv(output_dir / "split_role_summary.csv", index=False)
    _month_boundary_audit(frame, role_indices).to_csv(
        output_dir / "month_boundary_audit.csv",
        index=False,
    )

    models = _fit_models(frame, role_indices, feature_groups, args.seed, args.target_scale)
    metrics = _model_metrics(frame, role_indices, models, args.target_scale)
    metrics.to_csv(output_dir / "model_metrics.csv", index=False)

    predictions = _prediction_bundle(frame, role_indices, models, args.target_scale)
    predictions.update(_policy_thresholds(frame, predictions))
    exp1 = _economic_utility_table(frame, predictions)
    exp1.to_csv(output_dir / "economic_utility_decisions.csv", index=False)

    voi_model = _fit_voi_model(frame, role_indices, feature_groups, predictions, args.seed, args.target_scale)
    predictions["voi_pred_gross"] = voi_model.predict(frame.loc[role_indices["final_test"]]) * args.target_scale
    frontier = _capacity_frontier(
        frame,
        role_indices,
        predictions,
        review_cost=args.primary_review_cost,
    )
    frontier.to_csv(output_dir / "feature_acquisition_frontier.csv", index=False)

    cost_sensitivity = _review_cost_sensitivity(frame, role_indices, predictions)
    cost_sensitivity.to_csv(output_dir / "review_cost_sensitivity.csv", index=False)

    wage_grid = _wage_review_cost_grid(args.hourly_wage)
    wage_grid.to_csv(output_dir / "review_cost_anchor_grid.csv", index=False)

    ratio_sensitivity = _loss_profit_ratio_sensitivity(
        frame,
        role_indices,
        predictions,
        review_cost=args.primary_review_cost,
    )
    ratio_sensitivity.to_csv(output_dir / "loss_profit_ratio_sensitivity.csv", index=False)

    _write_results(output_dir, frame, role_indices, exp1, frontier, cost_sensitivity, ratio_sensitivity)
    _write_tracker(output_dir / "EXPERIMENT_TRACKER.md")
    write_json(
        output_dir / "cashflow_feature_acquisition_results.json",
        {
            "timestamp": now_stamp(),
            "loan_csv": str(loan_path),
            "rows_terminal": int(len(frame)),
            "run_name": args.run_name,
            "primary_review_cost": args.primary_review_cost,
            "outputs": {
                "economic_utility_decisions": str(output_dir / "economic_utility_decisions.csv"),
                "feature_acquisition_frontier": str(output_dir / "feature_acquisition_frontier.csv"),
                "review_cost_sensitivity": str(output_dir / "review_cost_sensitivity.csv"),
                "loss_profit_ratio_sensitivity": str(output_dir / "loss_profit_ratio_sensitivity.csv"),
            },
        },
    )


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.readline().strip("\n").split(",")


def _resolve_feature_groups(columns: list[str]) -> dict[str, list[str]]:
    present = set(columns)
    outcome_columns = set(CASHFLOW_COLUMNS)
    cheap_numeric = [col for col in CHEAP_NUMERIC if col in present and col not in outcome_columns]
    cheap_categorical = [col for col in CHEAP_CATEGORICAL if col in present]
    review_numeric = [col for col in REVIEW_NUMERIC if col in present and col not in outcome_columns]
    review_categorical = [col for col in REVIEW_CATEGORICAL if col in present]
    return {
        "cheap_numeric": cheap_numeric,
        "cheap_categorical": cheap_categorical,
        "full_numeric": list(dict.fromkeys([*cheap_numeric, *review_numeric])),
        "full_categorical": list(dict.fromkeys([*cheap_categorical, *review_categorical])),
        "review_numeric": review_numeric,
        "review_categorical": review_categorical,
    }


def _load_terminal_frame(
    path: Path,
    raw_columns: list[str],
    feature_groups: dict[str, list[str]],
    max_rows: int | None,
) -> pd.DataFrame:
    required = [
        "issue_d",
        "loan_status",
        *CASHFLOW_COLUMNS,
        *feature_groups["full_numeric"],
        *feature_groups["full_categorical"],
    ]
    usecols = [col for col in dict.fromkeys(required) if col in raw_columns]
    frame = pd.read_csv(path, usecols=usecols, nrows=max_rows, low_memory=False)
    frame["loan_status"] = frame["loan_status"].astype(str).str.strip()
    frame = frame[frame["loan_status"].isin(TERMINAL_STATUSES)].copy()
    frame["issue_d"] = pd.to_datetime(frame["issue_d"], format="%b-%Y", errors="coerce")
    frame = frame[frame["issue_d"].notna()].copy()
    frame["bad_loan"] = frame["loan_status"].isin(BAD_STATUSES).astype(int)
    for col in CASHFLOW_COLUMNS + feature_groups["full_numeric"]:
        if col in frame.columns:
            frame[col] = _numeric_series(frame[col])
    frame["net_cash"] = (
        frame["total_rec_prncp"].fillna(0.0)
        + frame["total_rec_int"].fillna(0.0)
        + frame["total_rec_late_fee"].fillna(0.0)
        + frame["recoveries"].fillna(0.0)
        - frame["funded_amnt"].fillna(0.0)
        - frame["collection_recovery_fee"].fillna(0.0)
    )
    frame["profit_if_approved"] = np.maximum(frame["net_cash"], 0.0)
    frame["loss_if_approved"] = np.maximum(-frame["net_cash"], 0.0)
    return frame.reset_index(drop=True)


def _numeric_series(series: pd.Series) -> pd.Series:
    if series.dtype == object:
        clean = series.astype(str).str.replace("%", "", regex=False).str.strip()
        clean = clean.replace({"": np.nan, "nan": np.nan, "None": np.nan})
        return pd.to_numeric(clean, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def _month_blocked_role_split(frame: pd.DataFrame, timestamp: pd.Series) -> dict[str, pd.Index]:
    ordered = frame.assign(_dcred_month=timestamp.dt.to_period("M").astype(str))
    ordered = ordered.sort_values("issue_d", kind="mergesort")
    month_counts = ordered.groupby("_dcred_month", sort=True).size()
    months = month_counts.index.to_numpy()
    if len(months) < len(DEFAULT_ROLE_SPLIT_SHARES):
        raise ValueError(f"Need at least {len(DEFAULT_ROLE_SPLIT_SHARES)} months, got {len(months)}")
    total_rows = int(month_counts.sum())
    cumulative_counts = month_counts.cumsum().to_numpy()
    role_indices: dict[str, pd.Index] = {}
    start_month = 0
    cumulative_share = 0.0
    items = list(DEFAULT_ROLE_SPLIT_SHARES.items())
    for i, (role, share) in enumerate(items):
        cumulative_share += float(share)
        if i == len(items) - 1:
            stop_month = len(months)
        else:
            remaining = len(items) - i - 1
            candidates = np.arange(start_month + 1, len(months) - remaining + 1)
            target = total_rows * cumulative_share
            counts = cumulative_counts[candidates - 1]
            stop_month = int(candidates[np.argmin(np.abs(counts - target))])
        selected = set(months[start_month:stop_month])
        role_indices[role] = pd.Index(ordered[ordered["_dcred_month"].isin(selected)].index)
        start_month = stop_month
    return role_indices


def _build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    transformers = []
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=50)),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transformers, sparse_threshold=0.3)


def _fit_models(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    feature_groups: dict[str, list[str]],
    seed: int,
    target_scale: float,
) -> dict[str, Pipeline]:
    train_idx = role_indices["model_train"]
    cash_target = frame.loc[train_idx, "net_cash"].to_numpy(dtype=float)
    cash_low, cash_high = np.quantile(cash_target, [0.01, 0.99])
    clipped_cash_target = np.clip(cash_target, cash_low, cash_high) / target_scale
    models: dict[str, Pipeline] = {}
    for scope in ["cheap", "full"]:
        numeric = feature_groups[f"{scope}_numeric"]
        categorical = feature_groups[f"{scope}_categorical"]
        preprocessor = _build_preprocessor(numeric, categorical)
        classifier = SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-4,
            average=True,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=5,
            class_weight="balanced",
            random_state=seed,
        )
        pd_model = Pipeline([("preprocess", preprocessor), ("model", classifier)])
        pd_model.fit(frame.loc[train_idx], frame.loc[train_idx, "bad_loan"].to_numpy())
        models[f"{scope}_pd"] = pd_model

        cash_preprocessor = _build_preprocessor(numeric, categorical)
        regressor = _cash_regressor(seed)
        cash_model = Pipeline([("preprocess", cash_preprocessor), ("model", regressor)])
        cash_model.fit(frame.loc[train_idx], clipped_cash_target)
        models[f"{scope}_cash"] = cash_model
    return models


def _cash_regressor(seed: int):
    try:
        from lightgbm import LGBMRegressor

        return LGBMRegressor(
            objective="regression_l1",
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=seed,
            n_jobs=-1,
            verbosity=-1,
        )
    except Exception:
        return SGDRegressor(
            loss="huber",
            penalty="l2",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-4,
            random_state=seed,
        )


def _fit_voi_model(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    feature_groups: dict[str, list[str]],
    predictions: dict[str, np.ndarray],
    seed: int,
    target_scale: float,
) -> Pipeline:
    idx = role_indices["policy_tune"]
    cheap_threshold = float(predictions["cheap_cash_threshold"])
    full_threshold = float(predictions["full_cash_threshold"])
    cheap_policy_value = np.where(
        predictions["cheap_cash_policy"] > cheap_threshold,
        predictions["cheap_cash_policy"],
        0.0,
    )
    full_policy_value = np.where(
        predictions["full_cash_policy"] > full_threshold,
        predictions["full_cash_policy"],
        0.0,
    )
    gross_value = full_policy_value - cheap_policy_value
    gross_value = np.maximum(gross_value, 0.0)
    gross_value = np.clip(gross_value, 0.0, np.quantile(gross_value, 0.99))
    preprocessor = _build_preprocessor(
        feature_groups["cheap_numeric"],
        feature_groups["cheap_categorical"],
    )
    regressor = _cash_regressor(seed)
    model = Pipeline([("preprocess", preprocessor), ("model", regressor)])
    model.fit(frame.loc[idx], gross_value / target_scale)
    return model


def _prediction_bundle(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    models: dict[str, Pipeline],
    target_scale: float,
) -> dict[str, np.ndarray]:
    bundle = {}
    for role in ["policy_tune", "risk_calibration", "final_test"]:
        idx = role_indices[role]
        for scope in ["cheap", "full"]:
            bundle[f"{scope}_pd_{role}"] = models[f"{scope}_pd"].predict_proba(frame.loc[idx])[:, 1]
            bundle[f"{scope}_cash_{role}"] = (
                models[f"{scope}_cash"].predict(frame.loc[idx]) * target_scale
            )
    bundle["cheap_cash_policy"] = bundle["cheap_cash_policy_tune"]
    bundle["full_cash_policy"] = bundle["full_cash_policy_tune"]
    return bundle


def _economic_utility_table(frame: pd.DataFrame, predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    y_policy = frame.loc[_role_idx(frame, "policy_tune"), "net_cash"].to_numpy(dtype=float)
    y_final = frame.loc[_role_idx(frame, "final_test"), "net_cash"].to_numpy(dtype=float)
    pd_policy = predictions["full_pd_policy_tune"]
    pd_final = predictions["full_pd_final_test"]
    cash_policy = predictions["full_cash_policy_tune"]
    cash_final = predictions["full_cash_final_test"]
    pd_threshold = _tune_pd_threshold(pd_policy, y_policy)
    cash_threshold = _tune_cash_threshold(cash_policy, y_policy)
    rows = [
        _decision_row("fixed_pd_threshold_0.5", y_final, pd_final < 0.5, {"threshold": 0.5}),
        _decision_row("tuned_pd_threshold", y_final, pd_final < pd_threshold, {"threshold": pd_threshold}),
        _decision_row("direct_cash_model_0", y_final, cash_final > 0.0, {"threshold": 0.0}),
        _decision_row(
            "tuned_cash_model",
            y_final,
            cash_final > cash_threshold,
            {"threshold": cash_threshold},
        ),
    ]
    return pd.DataFrame(rows)


def _tune_pd_threshold(probs: np.ndarray, net_cash: np.ndarray) -> float:
    thresholds = np.linspace(0.01, 0.99, 99)
    utilities = []
    for threshold in thresholds:
        utilities.append(float(np.mean(np.where(probs < threshold, net_cash, 0.0))))
    return float(thresholds[int(np.argmax(utilities))])


def _tune_cash_threshold(predicted_cash: np.ndarray, net_cash: np.ndarray) -> float:
    finite = predicted_cash[np.isfinite(predicted_cash)]
    if len(finite) == 0:
        return 0.0
    thresholds = np.unique(np.quantile(finite, np.linspace(0.01, 0.99, 99)))
    utilities = []
    for threshold in thresholds:
        utilities.append(float(np.mean(np.where(predicted_cash > threshold, net_cash, 0.0))))
    return float(thresholds[int(np.argmax(utilities))])


def _policy_thresholds(frame: pd.DataFrame, predictions: dict[str, np.ndarray]) -> dict[str, float]:
    y_policy = frame.loc[_role_idx(frame, "policy_tune"), "net_cash"].to_numpy(dtype=float)
    return {
        "cheap_cash_threshold": _tune_cash_threshold(predictions["cheap_cash_policy"], y_policy),
        "full_cash_threshold": _tune_cash_threshold(predictions["full_cash_policy"], y_policy),
    }


def _decision_row(
    policy: str,
    net_cash: np.ndarray,
    approve_mask: np.ndarray,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    values = np.where(approve_mask, net_cash, 0.0)
    row: dict[str, object] = {
        "policy": policy,
        "mean_realized_utility": float(np.mean(values)),
        "realized_utility_per_1000_apps": float(np.mean(values) * 1000.0),
        "approval_rate": float(np.mean(approve_mask)),
        "accepted_profit_per_app": float(np.mean(np.where(approve_mask & (net_cash > 0), net_cash, 0.0))),
        "approved_loss_per_app": float(np.mean(np.where(approve_mask & (net_cash < 0), -net_cash, 0.0))),
        "rejected_profitable_opportunity_cost_per_app": float(
            np.mean(np.where((~approve_mask) & (net_cash > 0), net_cash, 0.0))
        ),
        "rejected_loss_avoided_per_app": float(np.mean(np.where((~approve_mask) & (net_cash < 0), -net_cash, 0.0))),
    }
    if extra:
        row.update(extra)
    return row


def _capacity_frontier(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    predictions: dict[str, np.ndarray],
    review_cost: float,
) -> pd.DataFrame:
    final_idx = role_indices["final_test"]
    risk_idx = role_indices["risk_calibration"]
    net_cash = frame.loc[final_idx, "net_cash"].to_numpy(dtype=float)
    cheap_cash = predictions["cheap_cash_final_test"]
    full_cash = predictions["full_cash_final_test"]
    cheap_pd = predictions["cheap_pd_final_test"]
    cheap_threshold = float(predictions["cheap_cash_threshold"])
    full_threshold = float(predictions["full_cash_threshold"])
    risk_residual = np.abs(
        frame.loc[risk_idx, "net_cash"].to_numpy(dtype=float)
        - predictions["cheap_cash_risk_calibration"]
    )
    q90 = float(np.quantile(risk_residual, 0.90))
    scores = {
        "random_review": None,
        "uncertainty_review": -np.abs(cheap_cash),
        "conformal_interval_review": q90 - np.abs(cheap_cash - cheap_threshold),
        "dcred_stylized_benefit_rank": _dcred_stylized_benefit(cheap_pd),
        "predicted_value_of_information": predictions["voi_pred_gross"] - review_cost,
        "oracle_value_of_information": _oracle_voi(
            net_cash,
            cheap_cash,
            full_cash,
            review_cost,
            cheap_threshold,
            full_threshold,
        ),
    }
    rows = [
        _review_policy_row(
            "no_review_cheap_model",
            net_cash,
            cheap_cash,
            full_cash,
            np.zeros(len(net_cash), dtype=bool),
            review_cost,
            capacity_fraction=np.nan,
            baseline_utility=None,
            cheap_threshold=cheap_threshold,
            full_threshold=full_threshold,
        )
    ]
    baseline = float(rows[0]["mean_realized_utility"])
    rows.append(
        _review_policy_row(
            "all_review_full_model",
            net_cash,
            cheap_cash,
            full_cash,
            np.ones(len(net_cash), dtype=bool),
            review_cost,
            capacity_fraction=np.nan,
            baseline_utility=baseline,
            cheap_threshold=cheap_threshold,
            full_threshold=full_threshold,
        )
    )
    rng = np.random.default_rng(0)
    for fraction in CAPACITY_FRACTIONS:
        for policy, score in scores.items():
            if score is None:
                mask = _random_mask(len(net_cash), fraction, rng)
            else:
                positive_only = policy in {
                    "predicted_value_of_information",
                    "oracle_value_of_information",
                    "conformal_interval_review",
                    "dcred_stylized_benefit_rank",
                }
                mask = _top_fraction_mask(score, fraction, positive_only=positive_only)
            rows.append(
                _review_policy_row(
                    policy,
                    net_cash,
                    cheap_cash,
                    full_cash,
                    mask,
                    review_cost,
                    capacity_fraction=fraction,
                    baseline_utility=baseline,
                    cheap_threshold=cheap_threshold,
                    full_threshold=full_threshold,
                )
            )
    return pd.DataFrame(rows)


def _review_cost_sensitivity(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    rows = []
    for cost in DIRECT_REVIEW_COSTS:
        frontier = _capacity_frontier(frame, role_indices, predictions, review_cost=cost)
        subset = frontier[
            frontier["policy"].isin(
                [
                    "no_review_cheap_model",
                    "all_review_full_model",
                    "uncertainty_review",
                    "conformal_interval_review",
                    "predicted_value_of_information",
                    "dcred_stylized_benefit_rank",
                ]
            )
        ].copy()
        if "review_cost" not in subset.columns:
            subset.insert(0, "review_cost", cost)
        rows.append(subset)
    return pd.concat(rows, ignore_index=True)


def _loss_profit_ratio_sensitivity(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    predictions: dict[str, np.ndarray],
    review_cost: float,
) -> pd.DataFrame:
    final_idx = role_indices["final_test"]
    risk_idx = role_indices["risk_calibration"]
    base_cash = frame.loc[final_idx, "net_cash"].to_numpy(dtype=float)
    positives = base_cash[base_cash > 0.0]
    losses = -base_cash[base_cash < 0.0]
    mean_profit = float(np.mean(positives)) if len(positives) else 1.0
    mean_loss = float(np.mean(losses)) if len(losses) else 1.0
    cheap_threshold = float(predictions["cheap_cash_threshold"])
    full_threshold = float(predictions["full_cash_threshold"])
    risk_residual = np.abs(
        frame.loc[risk_idx, "net_cash"].to_numpy(dtype=float)
        - predictions["cheap_cash_risk_calibration"]
    )
    q90 = float(np.quantile(risk_residual, 0.90))
    rows = []
    for ratio in LOSS_PROFIT_RATIOS:
        scale = (ratio * mean_profit / mean_loss) if mean_loss > 0 else 1.0
        stressed = np.where(base_cash < 0.0, base_cash * scale, base_cash)
        cheap_cash = predictions["cheap_cash_final_test"]
        full_cash = predictions["full_cash_final_test"]
        scores = {
            "conformal_interval_review": q90 - np.abs(cheap_cash - cheap_threshold),
            "predicted_value_of_information": predictions["voi_pred_gross"] - review_cost,
        }
        baseline = _review_policy_row(
            "no_review_cheap_model",
            stressed,
            cheap_cash,
            full_cash,
            np.zeros(len(stressed), dtype=bool),
            review_cost,
            capacity_fraction=np.nan,
            baseline_utility=None,
            cheap_threshold=cheap_threshold,
            full_threshold=full_threshold,
        )["mean_realized_utility"]
        for fraction in CAPACITY_FRACTIONS:
            for policy, score in scores.items():
                mask = _top_fraction_mask(score, fraction, positive_only=True)
                row = _review_policy_row(
                    policy,
                    stressed,
                    cheap_cash,
                    full_cash,
                    mask,
                    review_cost,
                    capacity_fraction=fraction,
                    baseline_utility=float(baseline),
                    cheap_threshold=cheap_threshold,
                    full_threshold=full_threshold,
                )
                row["loss_profit_ratio_target"] = ratio
                row["negative_loss_scale"] = scale
                rows.append(row)
    return pd.DataFrame(rows)


def _review_policy_row(
    policy: str,
    net_cash: np.ndarray,
    cheap_cash_pred: np.ndarray,
    full_cash_pred: np.ndarray,
    review_mask: np.ndarray,
    review_cost: float,
    capacity_fraction: float,
    baseline_utility: float | None,
    cheap_threshold: float = 0.0,
    full_threshold: float = 0.0,
) -> dict[str, object]:
    review_mask = np.asarray(review_mask, dtype=bool)
    cheap_approve = cheap_cash_pred > cheap_threshold
    full_approve = full_cash_pred > full_threshold
    approve = np.where(review_mask, full_approve, cheap_approve)
    values = np.where(approve, net_cash, 0.0)
    values = values - review_mask.astype(float) * review_cost
    expected_values = np.where(
        review_mask,
        np.where(full_approve, full_cash_pred, 0.0) - review_cost,
        np.where(cheap_approve, cheap_cash_pred, 0.0),
    )
    mean_realized = float(np.mean(values))
    review_spend = float(np.mean(review_mask) * review_cost)
    row: dict[str, object] = {
        "policy": policy,
        "capacity_fraction": capacity_fraction,
        "review_cost": review_cost,
        "mean_expected_utility": float(np.mean(expected_values)),
        "mean_realized_utility": mean_realized,
        "realized_utility_per_1000_apps": mean_realized * 1000.0,
        "review_rate": float(np.mean(review_mask)),
        "automation_rate": float(np.mean(~review_mask)),
        "approval_rate": float(np.mean(approve)),
        "review_spend_per_app": review_spend,
        "utility_lift_vs_no_review": (
            np.nan if baseline_utility is None else mean_realized - baseline_utility
        ),
        "utility_lift_per_review_dollar": (
            np.nan
            if baseline_utility is None or review_spend <= 0.0
            else (mean_realized - baseline_utility) / review_spend
        ),
        "accepted_profit_per_app": float(np.mean(np.where(approve & (net_cash > 0), net_cash, 0.0))),
        "approved_loss_per_app": float(np.mean(np.where(approve & (net_cash < 0), -net_cash, 0.0))),
        "rejected_profitable_opportunity_cost_per_app": float(
            np.mean(np.where((~approve) & (net_cash > 0), net_cash, 0.0))
        ),
        "rejected_loss_avoided_per_app": float(np.mean(np.where((~approve) & (net_cash < 0), -net_cash, 0.0))),
    }
    return row


def _oracle_voi(
    net_cash: np.ndarray,
    cheap_cash: np.ndarray,
    full_cash: np.ndarray,
    review_cost: float,
    cheap_threshold: float,
    full_threshold: float,
) -> np.ndarray:
    cheap_approve = cheap_cash > cheap_threshold
    full_approve = full_cash > full_threshold
    cheap_value = np.where(cheap_approve, net_cash, 0.0)
    full_value = np.where(full_approve, net_cash, 0.0) - review_cost
    return full_value - cheap_value


def _dcred_stylized_benefit(probs: np.ndarray) -> np.ndarray:
    approve_cost = 5.0 * probs
    deny_cost = 1.0 * (1.0 - probs)
    auto_cost = np.minimum(approve_cost, deny_cost)
    manual_cost = 0.1 + 0.1 * auto_cost
    return auto_cost - manual_cost


def _top_fraction_mask(scores: np.ndarray, fraction: float, positive_only: bool) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    mask = np.zeros(len(scores), dtype=bool)
    max_reviews = int(np.floor(len(scores) * fraction))
    if max_reviews <= 0:
        return mask
    candidates = np.arange(len(scores))
    finite = np.isfinite(scores)
    candidates = candidates[finite[candidates]]
    if positive_only:
        candidates = candidates[scores[candidates] > 0.0]
    if len(candidates) == 0:
        return mask
    ranked = candidates[np.argsort(scores[candidates])[::-1]]
    mask[ranked[:max_reviews]] = True
    return mask


def _random_mask(n: int, fraction: float, rng: np.random.Generator) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    max_reviews = int(np.floor(n * fraction))
    if max_reviews <= 0:
        return mask
    mask[rng.choice(n, size=max_reviews, replace=False)] = True
    return mask


def _model_metrics(
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    models: dict[str, Pipeline],
    target_scale: float,
) -> pd.DataFrame:
    rows = []
    for role in ["policy_tune", "risk_calibration", "final_test"]:
        idx = role_indices[role]
        y = frame.loc[idx, "bad_loan"].to_numpy()
        cash = frame.loc[idx, "net_cash"].to_numpy(dtype=float)
        for scope in ["cheap", "full"]:
            probs = models[f"{scope}_pd"].predict_proba(frame.loc[idx])[:, 1]
            cash_pred = models[f"{scope}_cash"].predict(frame.loc[idx]) * target_scale
            rows.append(
                {
                    "partition": role,
                    "model_scope": scope,
                    "pd_auc": _safe_auc(y, probs),
                    "pd_brier": float(brier_score_loss(y, np.clip(probs, 1e-6, 1.0 - 1e-6))),
                    "cash_mae": float(mean_absolute_error(cash, cash_pred)),
                    "cash_rmse": float(np.sqrt(mean_squared_error(cash, cash_pred))),
                    "cash_r2": float(r2_score(cash, cash_pred)),
                }
            )
    return pd.DataFrame(rows)


def _safe_auc(y: np.ndarray, probs: np.ndarray) -> float:
    try:
        return float(roc_auc_score(y, probs))
    except ValueError:
        return float("nan")


def _role_idx(frame: pd.DataFrame, role: str) -> pd.Index:
    if "_role_indices" not in frame.attrs:
        raise RuntimeError("Role indices not stored on frame attrs.")
    return frame.attrs["_role_indices"][role]


def _split_summary(frame: pd.DataFrame, role_indices: dict[str, pd.Index]) -> pd.DataFrame:
    frame.attrs["_role_indices"] = role_indices
    rows = []
    for role, idx in role_indices.items():
        subset = frame.loc[idx]
        months = subset["issue_d"].dt.to_period("M").astype(str)
        rows.append(
            {
                "partition": role,
                "rows": int(len(subset)),
                "bad_rate": float(subset["bad_loan"].mean()),
                "mean_net_cash": float(subset["net_cash"].mean()),
                "median_net_cash": float(subset["net_cash"].median()),
                "start_month": str(months.min()),
                "end_month": str(months.max()),
                "n_issue_months": int(months.nunique()),
            }
        )
    return pd.DataFrame(rows)


def _month_boundary_audit(frame: pd.DataFrame, role_indices: dict[str, pd.Index]) -> pd.DataFrame:
    rows = []
    pieces = []
    for role, idx in role_indices.items():
        pieces.append(
            pd.DataFrame(
                {
                    "issue_month": frame.loc[idx, "issue_d"].dt.to_period("M").astype(str).to_numpy(),
                    "partition": role,
                }
            )
        )
    assigned = pd.concat(pieces, ignore_index=True)
    for month, group in assigned.groupby("issue_month", sort=True):
        roles = sorted(group["partition"].unique())
        rows.append(
            {
                "issue_month": month,
                "rows": int(len(group)),
                "roles": ";".join(roles),
                "n_roles": int(len(roles)),
                "status": "OK_NO_SHARED_MONTH" if len(roles) == 1 else "SHARED_MONTH",
            }
        )
    return pd.DataFrame(rows)


def _write_audits(
    output_dir: Path,
    raw_columns: list[str],
    feature_groups: dict[str, list[str]],
    frame: pd.DataFrame,
) -> None:
    rows = []
    for col in raw_columns:
        if col in CASHFLOW_COLUMNS or col in {"loan_status", "last_pymnt_d", "last_pymnt_amnt"}:
            role = "outcome_or_post_origination"
            allowed = False
        elif col in feature_groups["cheap_numeric"] or col in feature_groups["cheap_categorical"]:
            role = "cheap_application_feature"
            allowed = True
        elif col in feature_groups["review_numeric"] or col in feature_groups["review_categorical"]:
            role = "review_acquired_feature"
            allowed = True
        elif col == "issue_d":
            role = "split_timestamp"
            allowed = False
        else:
            role = "unused_or_post_origination"
            allowed = False
        rows.append({"feature": col, "role": role, "allowed_as_predictor": allowed})
    pd.DataFrame(rows).to_csv(output_dir / "feature_audit_loan_csv.csv", index=False)

    status = frame["loan_status"].value_counts().rename_axis("loan_status").reset_index(name="rows")
    status.to_csv(output_dir / "terminal_status_summary.csv", index=False)

    cash_rows = []
    for name, values in {
        "net_cash": frame["net_cash"],
        "profit_if_approved": frame["profit_if_approved"],
        "loss_if_approved": frame["loss_if_approved"],
    }.items():
        series = pd.Series(values)
        cash_rows.append(
            {
                "quantity": name,
                "count": int(series.count()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "p25": float(series.quantile(0.25)),
                "p75": float(series.quantile(0.75)),
                "p95": float(series.quantile(0.95)),
            }
        )
    pd.DataFrame(cash_rows).to_csv(output_dir / "cashflow_distribution.csv", index=False)


def _wage_review_cost_grid(hourly_wage: float) -> pd.DataFrame:
    rows = []
    for minutes in [5, 10, 20, 30]:
        for overhead in [1.0, 1.3, 1.5, 2.0]:
            rows.append(
                {
                    "hourly_wage": hourly_wage,
                    "review_minutes": minutes,
                    "overhead_multiplier": overhead,
                    "review_cost": hourly_wage * overhead * minutes / 60.0,
                }
            )
    return pd.DataFrame(rows)


def _write_results(
    output_dir: Path,
    frame: pd.DataFrame,
    role_indices: dict[str, pd.Index],
    exp1: pd.DataFrame,
    frontier: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    ratio_sensitivity: pd.DataFrame,
) -> None:
    status_counts = frame["loan_status"].value_counts()
    primary = frontier[
        frontier["policy"].isin(
            [
                "no_review_cheap_model",
                "all_review_full_model",
                "uncertainty_review",
                "conformal_interval_review",
                "dcred_stylized_benefit_rank",
                "predicted_value_of_information",
                "oracle_value_of_information",
            ]
        )
        & (frontier["capacity_fraction"].isin([0.05, 0.10, 0.20, 0.50]) | frontier["capacity_fraction"].isna())
    ].copy()
    lines = [
        "# Dean Cash-Flow And Feature Acquisition Results",
        "",
        f"Date: {now_stamp()}",
        f"Output directory: `{output_dir}`",
        "",
        "## Dataset",
        "",
        f"- Terminal accepted-loan rows: `{len(frame)}`",
        f"- Good terminal rows: `{int(frame['loan_status'].isin(GOOD_STATUSES).sum())}`",
        f"- Bad terminal rows: `{int(frame['loan_status'].isin(BAD_STATUSES).sum())}`",
        f"- Final-test rows: `{len(role_indices['final_test'])}`",
        "",
        "## Experiment 1: Economic Utility Decisions",
        "",
        _frame_to_markdown(
            exp1[
                [
                    "policy",
                    "mean_realized_utility",
                    "realized_utility_per_1000_apps",
                    "approval_rate",
                    "accepted_profit_per_app",
                    "approved_loss_per_app",
                    "rejected_profitable_opportunity_cost_per_app",
                ]
            ]
        ),
        "",
        "## Experiments 2-3: Information Acquisition And Capacity Frontier",
        "",
        _frame_to_markdown(
            primary[
                [
                    "policy",
                    "capacity_fraction",
                    "review_cost",
                    "mean_realized_utility",
                    "realized_utility_per_1000_apps",
                    "review_rate",
                    "approval_rate",
                    "utility_lift_vs_no_review",
                    "utility_lift_per_review_dollar",
                ]
            ]
        ),
        "",
        "## Experiment 4: Review-Cost Sensitivity",
        "",
        _frame_to_markdown(
            cost_sensitivity[
                cost_sensitivity["policy"].isin(
                    ["conformal_interval_review", "predicted_value_of_information"]
                )
                & cost_sensitivity["capacity_fraction"].isin([0.05, 0.10, 0.20])
            ][
                [
                    "policy",
                    "review_cost",
                    "capacity_fraction",
                    "mean_realized_utility",
                    "review_rate",
                    "utility_lift_vs_no_review",
                    "utility_lift_per_review_dollar",
                ]
            ].head(36)
        ),
        "",
        "## Experiment 4b: Loss-Profit Ratio Sensitivity",
        "",
        _frame_to_markdown(
            ratio_sensitivity[
                ratio_sensitivity["policy"].isin(
                    ["conformal_interval_review", "predicted_value_of_information"]
                )
                & ratio_sensitivity["capacity_fraction"].eq(0.10)
            ][
                [
                    "policy",
                    "loss_profit_ratio_target",
                    "capacity_fraction",
                    "mean_realized_utility",
                    "review_rate",
                    "utility_lift_vs_no_review",
                    "utility_lift_per_review_dollar",
                ]
            ]
        ),
        "",
        "## Interpretation Guardrails",
        "",
        "- This is accepted/funded-loan policy evaluation, not rejected-applicant inference.",
        "- Non-terminal loans are excluded because their cash flows are censored.",
        "- Cash-flow and post-origination fields are outcome labels only, never predictors.",
        "- FICO-specific claims are not made because this `loan.csv` header does not expose FICO fields.",
    ]
    write_text(output_dir / "EXPERIMENT_RESULTS.md", "\n".join(lines))


def _write_tracker(path: Path) -> None:
    lines = [
        "# Dean Cash-Flow Experiment Tracker",
        "",
        f"Updated: {now_stamp()}",
        "",
        "| Run ID | Milestone | Status | Notes |",
        "|---|---|---|---|",
        "| C001 | M0 | DONE | `loan.csv` schema and feature audit written. |",
        "| C002 | M0 | DONE | Terminal accepted-loan sample built; censored statuses excluded. |",
        "| C003 | M0 | DONE | `net_cash` outcome constructed from observed repayment fields. |",
        "| C004 | M0 | DONE | Month-blocked roles and month audit written. |",
        "| C101-C103 | M1 | DONE | PD/cash models and economic utility policies evaluated. |",
        "| C201 | M2 | DONE | Predicted value-of-information scorer trained. |",
        "| C301 | M3 | DONE | Capacity frontier baselines evaluated. |",
        "| C401-C403 | M4 | DONE | Review-cost and loss/profit sensitivity tables written. |",
        "| C501 | M5 | DONE | Markdown/CSV/JSON results written. |",
    ]
    write_text(path, "\n".join(lines))


def _frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                values.append("" if np.isnan(value) else f"{value:.6g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
