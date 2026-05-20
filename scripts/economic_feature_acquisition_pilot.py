from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dcred.config import OUTPUT_DIR, RAW_DATA_DIR
from dcred.data import dataset_summary, load_lending_club
from dcred.modeling import build_preprocessor, make_pipeline, predict_default_proba
from dcred.splits import temporal_month_blocked_role_split, temporal_role_split
from dcred.utils import ensure_dir, log, now_stamp, write_json, write_text


CAPACITY_FRACTIONS = (0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a D-CRED economic utility and two-stage feature-acquisition pilot "
            "on the current Lending Club granting dataset."
        )
    )
    parser.add_argument("--raw-dir", default=str(RAW_DATA_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--run-name", default="economic_feature_acquisition_pilot")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lending-max-rows", type=int, default=None)
    parser.add_argument("--role-split-mode", choices=["row", "month"], default="month")
    parser.add_argument("--roi", type=float, default=0.10)
    parser.add_argument("--lgd", type=float, default=0.60)
    parser.add_argument("--review-cost", type=float, default=10.0)
    args = parser.parse_args()

    output_dir = ensure_dir(Path(args.output_dir) / args.run_name)
    rng = np.random.default_rng(args.seed)

    bundle = load_lending_club(Path(args.raw_dir), max_rows=args.lending_max_rows)
    log(f"Loaded Lending Club rows={len(bundle.frame)} for utility/acquisition pilot")
    dataset_summary(bundle).to_csv(output_dir / "dataset_summary.csv", index=False)

    if args.role_split_mode == "month":
        role_indices = temporal_month_blocked_role_split(bundle.frame, bundle.timestamp)
    else:
        role_indices = temporal_role_split(bundle.frame, bundle.timestamp)
    _split_summary(bundle, role_indices).to_csv(output_dir / "split_role_summary.csv", index=False)
    _month_boundary_audit(bundle, role_indices).to_csv(
        output_dir / "month_boundary_audit.csv",
        index=False,
    )

    cheap_numeric, cheap_categorical, full_numeric, full_categorical = _feature_groups(bundle)
    write_json(
        output_dir / "feature_groups.json",
        {
            "cheap_numeric": cheap_numeric,
            "cheap_categorical": cheap_categorical,
            "full_numeric": full_numeric,
            "full_categorical": full_categorical,
            "expensive_or_review_numeric": sorted(set(full_numeric) - set(cheap_numeric)),
            "expensive_or_review_categorical": sorted(set(full_categorical) - set(cheap_categorical)),
            "note": (
                "The local granting dataset has no observed cash-flow columns such as "
                "total_pymnt, recoveries, or collection_recovery_fee. This pilot uses "
                "loan_amnt with ROI/LGD assumptions as a proxy utility label."
            ),
        },
    )

    cheap_model = _fit_classifier(
        bundle,
        role_indices["model_train"],
        cheap_numeric,
        cheap_categorical,
        seed=args.seed,
    )
    full_model = _fit_classifier(
        bundle,
        role_indices["model_train"],
        full_numeric,
        full_categorical,
        seed=args.seed,
    )

    policy_idx = role_indices["policy_tune"]
    final_idx = role_indices["final_test"]
    p0_policy = predict_default_proba(cheap_model, bundle.frame.loc[policy_idx])
    p1_policy = predict_default_proba(full_model, bundle.frame.loc[policy_idx])
    p0_final = predict_default_proba(cheap_model, bundle.frame.loc[final_idx])
    p1_final = predict_default_proba(full_model, bundle.frame.loc[final_idx])

    ead_policy = _exposure(bundle, policy_idx)
    ead_final = _exposure(bundle, final_idx)
    y_final = bundle.target.loc[final_idx].astype(int).to_numpy()

    gross_value_policy = _best_expected_utility(
        p1_policy,
        ead_policy,
        args.roi,
        args.lgd,
    ) - _best_expected_utility(p0_policy, ead_policy, args.roi, args.lgd)
    gross_value_policy = np.maximum(gross_value_policy, 0.0)

    value_model = _fit_value_model(
        bundle,
        policy_idx,
        cheap_numeric,
        cheap_categorical,
        gross_value_policy,
        seed=args.seed,
    )
    predicted_gross_value = np.maximum(
        value_model.predict(bundle.frame.loc[final_idx]),
        0.0,
    )

    utility_distribution = _proxy_utility_distribution(
        bundle,
        final_idx,
        args.roi,
        args.lgd,
    )
    utility_distribution.to_csv(output_dir / "proxy_loan_utility_distribution.csv", index=False)

    threshold_rows = pd.DataFrame(
        [
            {
                "scenario": "binary_default_cost_5_to_1",
                "decision_threshold": 1.0 / 6.0,
                "note": "Original normalized FN:FP=5:1 threshold.",
            },
            {
                "scenario": f"proxy_utility_roi_{args.roi:g}_lgd_{args.lgd:g}",
                "decision_threshold": args.roi / (args.roi + args.lgd),
                "note": "Approve only when expected proxy net cash is positive.",
            },
        ]
    )
    threshold_rows.to_csv(output_dir / "binary_vs_proxy_thresholds.csv", index=False)

    rows: list[dict[str, object]] = []
    no_review = _evaluate_policy(
        "no_review_cheap_model",
        y_final,
        ead_final,
        p0_final,
        p1_final,
        np.zeros(len(final_idx), dtype=bool),
        args.roi,
        args.lgd,
        args.review_cost,
        baseline_expected=None,
    )
    rows.append(no_review)
    baseline_expected = float(no_review["mean_expected_utility"])
    all_review_mask = np.ones(len(final_idx), dtype=bool)
    rows.append(
        _evaluate_policy(
            "all_review_full_model",
            y_final,
            ead_final,
            p0_final,
            p1_final,
            all_review_mask,
            args.roi,
            args.lgd,
            args.review_cost,
            baseline_expected,
        )
    )

    utility_threshold = args.roi / (args.roi + args.lgd)
    oracle_net_value = (
        _best_expected_utility(p1_final, ead_final, args.roi, args.lgd)
        - _best_expected_utility(p0_final, ead_final, args.roi, args.lgd)
        - args.review_cost
    )
    predicted_net_value = predicted_gross_value - args.review_cost
    uncertainty_score = -np.abs(p0_final - utility_threshold)
    for fraction in CAPACITY_FRACTIONS:
        rows.append(
            _evaluate_policy(
                "random_review",
                y_final,
                ead_final,
                p0_final,
                p1_final,
                _random_mask(len(final_idx), fraction, rng),
                args.roi,
                args.lgd,
                args.review_cost,
                baseline_expected,
                {"capacity_fraction": fraction},
            )
        )
        rows.append(
            _evaluate_policy(
                "uncertainty_review",
                y_final,
                ead_final,
                p0_final,
                p1_final,
                _top_fraction_mask(uncertainty_score, fraction),
                args.roi,
                args.lgd,
                args.review_cost,
                baseline_expected,
                {"capacity_fraction": fraction},
            )
        )
        rows.append(
            _evaluate_policy(
                "predicted_value_of_information",
                y_final,
                ead_final,
                p0_final,
                p1_final,
                _top_fraction_mask(predicted_net_value, fraction, positive_only=True),
                args.roi,
                args.lgd,
                args.review_cost,
                baseline_expected,
                {"capacity_fraction": fraction},
            )
        )
        rows.append(
            _evaluate_policy(
                "oracle_value_of_information",
                y_final,
                ead_final,
                p0_final,
                p1_final,
                _top_fraction_mask(oracle_net_value, fraction, positive_only=True),
                args.roi,
                args.lgd,
                args.review_cost,
                baseline_expected,
                {"capacity_fraction": fraction, "deployable": False},
            )
        )

    frontier = pd.DataFrame(rows)
    frontier.to_csv(output_dir / "feature_acquisition_frontier.csv", index=False)
    _write_summary(
        output_dir / "EXPERIMENT_RESULTS.md",
        output_dir,
        args,
        frontier,
        utility_distribution,
    )
    _write_tracker(output_dir / "EXPERIMENT_TRACKER.md", args, output_dir)
    write_json(
        output_dir / "feature_acquisition_results.json",
        {
            "command": "scripts/economic_feature_acquisition_pilot.py",
            "timestamp": now_stamp(),
            "rows": int(len(bundle.frame)),
            "role_split_mode": args.role_split_mode,
            "roi": args.roi,
            "lgd": args.lgd,
            "review_cost": args.review_cost,
            "output_dir": str(output_dir),
            "cash_flow_limitation": (
                "No observed repayment cash-flow columns are present in the local granting dataset; "
                "results are proxy-utility pilot evidence only."
            ),
        },
    )


def _feature_groups(bundle) -> tuple[list[str], list[str], list[str], list[str]]:
    cheap_numeric = [col for col in ["revenue", "loan_amnt", "experience_c"] if col in bundle.numeric_features]
    cheap_categorical = [
        col
        for col in ["emp_length", "purpose", "home_ownership_n", "addr_state", "zip_code"]
        if col in bundle.categorical_features
    ]
    full_numeric = list(bundle.numeric_features)
    full_categorical = list(bundle.categorical_features)
    return cheap_numeric, cheap_categorical, full_numeric, full_categorical


def _fit_classifier(bundle, idx, numeric, categorical, seed: int) -> Pipeline:
    preprocessor = build_preprocessor(numeric, categorical, None, text_max_features=0)
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
    pipeline = make_pipeline(preprocessor, classifier)
    pipeline.fit(bundle.frame.loc[idx], bundle.target.loc[idx].astype(int).to_numpy())
    return pipeline


def _fit_value_model(bundle, idx, numeric, categorical, target, seed: int) -> Pipeline:
    preprocessor = build_preprocessor(numeric, categorical, None, text_max_features=0)
    regressor = SGDRegressor(
        loss="squared_error",
        penalty="l2",
        alpha=1e-4,
        max_iter=1000,
        tol=1e-3,
        random_state=seed,
    )
    pipeline = Pipeline([("preprocess", preprocessor), ("model", regressor)])
    pipeline.fit(bundle.frame.loc[idx], target)
    return pipeline


def _exposure(bundle, idx) -> np.ndarray:
    if bundle.exposure is None:
        return np.ones(len(idx), dtype=float)
    values = pd.to_numeric(bundle.exposure.loc[idx], errors="coerce").to_numpy(dtype=float)
    median = float(np.nanmedian(values)) if np.isfinite(np.nanmedian(values)) else 1.0
    return np.nan_to_num(values, nan=median, posinf=median, neginf=median)


def _expected_approve_utility(probs, exposure, roi: float, lgd: float) -> np.ndarray:
    return ((1.0 - probs) * roi * exposure) - (probs * lgd * exposure)


def _best_expected_utility(probs, exposure, roi: float, lgd: float) -> np.ndarray:
    return np.maximum(_expected_approve_utility(probs, exposure, roi, lgd), 0.0)


def _approve_mask(probs, exposure, roi: float, lgd: float) -> np.ndarray:
    return _expected_approve_utility(probs, exposure, roi, lgd) > 0.0


def _realized_utility(y_true, exposure, approve_mask, roi: float, lgd: float) -> np.ndarray:
    values = np.zeros(len(y_true), dtype=float)
    values[approve_mask & (y_true == 0)] = roi * exposure[approve_mask & (y_true == 0)]
    values[approve_mask & (y_true == 1)] = -lgd * exposure[approve_mask & (y_true == 1)]
    return values


def _evaluate_policy(
    policy: str,
    y_true,
    exposure,
    probs_cheap,
    probs_full,
    review_mask,
    roi: float,
    lgd: float,
    review_cost: float,
    baseline_expected: float | None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    review_mask = np.asarray(review_mask, dtype=bool)
    cheap_approve = _approve_mask(probs_cheap, exposure, roi, lgd)
    full_approve = _approve_mask(probs_full, exposure, roi, lgd)
    approve = np.where(review_mask, full_approve, cheap_approve)
    expected_values = np.where(
        review_mask,
        _best_expected_utility(probs_full, exposure, roi, lgd) - review_cost,
        _best_expected_utility(probs_cheap, exposure, roi, lgd),
    )
    realized_values = _realized_utility(y_true, exposure, approve, roi, lgd)
    realized_values[review_mask] -= review_cost
    mean_expected = float(np.mean(expected_values))
    review_spend = float(np.mean(review_mask) * review_cost)
    row: dict[str, object] = {
        "policy": policy,
        "capacity_fraction": np.nan,
        "rows": int(len(y_true)),
        "mean_expected_utility": mean_expected,
        "mean_realized_utility": float(np.mean(realized_values)),
        "expected_utility_per_1000_apps": mean_expected * 1000.0,
        "realized_utility_per_1000_apps": float(np.mean(realized_values) * 1000.0),
        "review_rate": float(np.mean(review_mask)),
        "automation_rate": float(np.mean(~review_mask)),
        "approval_rate": float(np.mean(approve)),
        "approved_default_rate": _safe_rate(y_true[approve] == 1),
        "review_spend_per_application": review_spend,
        "utility_lift_vs_no_review": (
            np.nan if baseline_expected is None else mean_expected - baseline_expected
        ),
        "utility_lift_per_review_dollar": (
            np.nan
            if baseline_expected is None or review_spend <= 0.0
            else (mean_expected - baseline_expected) / review_spend
        ),
        "opportunity_cost_rejected_non_default_per_app": float(
            np.mean((~approve & (y_true == 0)) * roi * exposure)
        ),
        "approved_default_loss_per_app": float(
            np.mean((approve & (y_true == 1)) * lgd * exposure)
        ),
    }
    if extra:
        row.update(extra)
    return row


def _top_fraction_mask(scores, fraction: float, positive_only: bool = False) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    mask = np.zeros(len(scores), dtype=bool)
    candidates = np.arange(len(scores))
    if positive_only:
        candidates = candidates[scores[candidates] > 0.0]
    max_reviews = int(np.floor(len(scores) * fraction))
    if max_reviews <= 0 or len(candidates) == 0:
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


def _safe_rate(mask) -> float:
    if len(mask) == 0:
        return float("nan")
    return float(np.mean(mask))


def _split_summary(bundle, role_indices) -> pd.DataFrame:
    rows = []
    for role, idx in role_indices.items():
        y = bundle.target.loc[idx].astype(int)
        timestamps = bundle.timestamp.loc[idx]
        months = timestamps.dt.to_period("M").astype(str)
        rows.append(
            {
                "partition": role,
                "rows": int(len(idx)),
                "default_rate": float(y.mean()),
                "start_month": str(months.min()),
                "end_month": str(months.max()),
                "n_issue_months": int(months.nunique()),
            }
        )
    return pd.DataFrame(rows)


def _month_boundary_audit(bundle, role_indices) -> pd.DataFrame:
    frames = []
    for role, idx in role_indices.items():
        months = bundle.timestamp.loc[idx].dt.to_period("M").astype(str)
        frames.append(pd.DataFrame({"issue_month": months, "partition": role}))
    assigned = pd.concat(frames, ignore_index=True)
    rows = []
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


def _proxy_utility_distribution(bundle, idx, roi: float, lgd: float) -> pd.DataFrame:
    y = bundle.target.loc[idx].astype(int).to_numpy()
    exposure = _exposure(bundle, idx)
    signed_proxy = np.where(y == 0, roi * exposure, -lgd * exposure)
    rows = []
    for name, values in {
        "signed_proxy_cash": signed_proxy,
        "non_default_profit_if_approved": roi * exposure[y == 0],
        "default_loss_if_approved": lgd * exposure[y == 1],
    }.items():
        series = pd.Series(values)
        rows.append(
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
    return pd.DataFrame(rows)


def _write_summary(path: Path, output_dir: Path, args, frontier: pd.DataFrame, utility_distribution: pd.DataFrame) -> None:
    primary = frontier[
        frontier["policy"].isin(["no_review_cheap_model", "all_review_full_model"])
        | (
            frontier["policy"].isin(
                ["random_review", "uncertainty_review", "predicted_value_of_information"]
            )
            & frontier["capacity_fraction"].isin([0.05, 0.10, 0.20, 0.50])
        )
    ].copy()
    lines = [
        "# Economic Utility And Feature Acquisition Pilot Results",
        "",
        f"Date: {now_stamp()}",
        f"Output directory: `{output_dir}`",
        "",
        "## Scope",
        "",
        "- Current local Lending Club granting data lacks observed repayment cash-flow fields.",
        "- This run uses `loan_amnt`, ROI, and LGD as a proxy utility label.",
        f"- ROI={args.roi:g}, LGD={args.lgd:g}, review/acquisition cost=${args.review_cost:g}.",
        f"- Role split mode: `{args.role_split_mode}`.",
        "",
        "## Proxy Utility Distribution",
        "",
        _frame_to_markdown(utility_distribution),
        "",
        "## Policy Frontier Excerpt",
        "",
        _frame_to_markdown(
            primary[
                [
                    "policy",
                    "capacity_fraction",
                    "mean_expected_utility",
                    "mean_realized_utility",
                    "review_rate",
                    "approval_rate",
                    "utility_lift_vs_no_review",
                    "utility_lift_per_review_dollar",
                ]
            ]
        ),
        "",
        "## Interpretation Guardrail",
        "",
        "This is a deployable-code pilot for the dean's proposed direction, not final loan-level cash-flow evidence. A true version needs a Lending Club accepted-loan dataset with repayment columns such as `total_pymnt`, `recoveries`, and `collection_recovery_fee`.",
    ]
    write_text(path, "\n".join(lines))


def _write_tracker(path: Path, args, output_dir: Path) -> None:
    lines = [
        "# Economic Utility And Feature Acquisition Tracker",
        "",
        f"Updated: {now_stamp()}",
        "",
        "| Run ID | Milestone | Purpose | Status | Notes |",
        "|---|---|---|---|---|",
        "| E001 | M0 | Validate current cash-flow field availability | DONE | Current granting CSV lacks observed repayment cash-flow fields; proxy utility used. |",
        f"| E002 | M0 | Build {args.role_split_mode} role split and month audit | DONE | `split_role_summary.csv` and `month_boundary_audit.csv` written. |",
        "| E101 | M1 | Train cheap-feature PD model | DONE | Cheap features simulate initial application screen. |",
        "| E102 | M1 | Train full-feature PD model | DONE | Full features simulate acquired review information. |",
        "| E201 | M2 | Train value-of-information scorer | DONE | Regresses policy-tune full-vs-cheap utility gain from cheap features. |",
        "| E301 | M3 | Compare review policies over capacity grid | DONE | `feature_acquisition_frontier.csv` written. |",
        "| E901 | M9 | Replace proxy utility with observed cash flow | BLOCKED | Requires an accepted-loan cash-flow dataset not present in this checkout. |",
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
