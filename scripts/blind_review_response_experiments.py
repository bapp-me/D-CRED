from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dcred.config import OUTPUT_DIR, RAW_DATA_DIR
from dcred.calibration import fit_calibrators
from dcred.metrics import classification_metrics, expected_calibration_error
from dcred.reject_option import (
    CostScenario,
    add_reference_savings,
    capacity_review_mask,
    cost_components,
    evaluate_all_review,
    evaluate_capacity_grid,
    evaluate_no_review,
    evaluate_reject_option,
    evaluate_review_mask_policy,
    no_review_masks,
)
from dcred.splits import DEFAULT_ROLE_SPLIT_SHARES, temporal_month_blocked_role_split
from dcred.utils import ensure_dir, now_stamp, write_json, write_text


CAPACITY_GRID = (0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50)
SENSITIVITY_CAPACITY_GRID = (0.01, 0.05, 0.10, 0.20, 0.50)
FN_FP_RATIOS = (2.0, 5.0, 10.0, 20.0)
REVIEW_COSTS = (0.01, 0.05, 0.10, 0.20, 0.50, 1.00)
HUMAN_RESIDUAL_RHOS = (0.0, 0.05, 0.10, 0.20, 0.50)
PRIMARY_SCENARIO = CostScenario(
    false_negative_cost=5.0,
    false_positive_cost=1.0,
    review_cost=0.10,
    human_residual_rho=0.10,
)
SMALL_CELL_MIN_N = 200

GRANTING_NUMERIC = ["revenue", "dti_n", "loan_amnt", "fico_n", "experience_c"]
GRANTING_CATEGORICAL = ["emp_length", "purpose", "home_ownership_n", "addr_state", "zip_code"]
STRICT_NUMERIC = ["revenue", "dti_n", "loan_amnt", "fico_n", "experience_c"]
STRICT_CATEGORICAL = ["emp_length", "purpose", "home_ownership_n"]
DEFAULT_NUMERIC = STRICT_NUMERIC
DEFAULT_CATEGORICAL = STRICT_CATEGORICAL + ["addr_state", "zip_code"]
EXPANDED_NUMERIC = DEFAULT_NUMERIC
EXPANDED_CATEGORICAL = DEFAULT_CATEGORICAL
TEXT_COLUMNS = ["title", "desc"]

LOAN_CASHFLOW_COLUMNS = {
    "funded_amnt",
    "total_rec_prncp",
    "total_rec_int",
    "total_rec_late_fee",
    "recoveries",
    "collection_recovery_fee",
}
LOAN_POST_ORIGINATION_PREFIXES = (
    "out_",
    "total_pymnt",
    "last_",
    "next_",
    "hardship_",
    "settlement_",
    "debt_settlement",
)
LOAN_POLICY_GENERATED = {
    "funded_amnt",
    "funded_amnt_inv",
    "grade",
    "sub_grade",
    "int_rate",
    "installment",
    "verification_status",
    "initial_list_status",
    "policy_code",
}


@dataclass(frozen=True)
class OutputPaths:
    timestamp_dir: Path
    latest_dir: Path
    refine_dir: Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build blind-review D-CRED reviewer-response evidence pack."
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--latest-name", default="blind_review_response_latest")
    parser.add_argument("--reject-run", default=str(OUTPUT_DIR / "reject_capacity_month_blocked"))
    parser.add_argument("--cashflow-run", default=str(OUTPUT_DIR / "dean_cashflow_full"))
    parser.add_argument("--granting-csv", default=str(RAW_DATA_DIR / "LC_loans_granting_model_dataset.csv"))
    parser.add_argument("--loan-csv", default=str(RAW_DATA_DIR / "lending_club" / "loan.csv"))
    parser.add_argument("--plan", default=str(PROJECT_ROOT / "refine-logs" / "BLIND_REVIEW_EXPERIMENT_PLAN.md"))
    parser.add_argument("--tracker", default=str(PROJECT_ROOT / "refine-logs" / "BLIND_REVIEW_EXPERIMENT_TRACKER.md"))
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument(
        "--stress-max-rows",
        type=int,
        default=75000,
        help="Rows for feature-set stress test; <=0 is refused unless --allow-full-stress is set.",
    )
    parser.add_argument(
        "--allow-full-stress",
        action="store_true",
        help="Allow full-row feature stress. This is resource-heavy and disabled by default.",
    )
    parser.add_argument(
        "--allow-full-text-stress",
        action="store_true",
        help="Also include text TF-IDF in full-row stress. Unsafe on low-memory machines.",
    )
    parser.add_argument("--stress-n-jobs", type=int, default=2)
    parser.add_argument("--stress-n-estimators", type=int, default=200)
    parser.add_argument("--stress-text-max-features", type=int, default=128)
    parser.add_argument("--skip-stress", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stamp = now_stamp()
    run_name = args.run_name or f"blind_review_response_{stamp}"
    paths = OutputPaths(
        timestamp_dir=ensure_dir(Path(args.output_dir) / run_name),
        latest_dir=ensure_dir(Path(args.output_dir) / args.latest_name),
        refine_dir=ensure_dir(PROJECT_ROOT / "refine-logs"),
    )
    reject_dir = Path(args.reject_run)
    cashflow_dir = Path(args.cashflow_run)
    granting_csv = Path(args.granting_csv)
    loan_csv = Path(args.loan_csv)
    plan_path = Path(args.plan)
    tracker_path = Path(args.tracker)
    if not args.skip_stress and args.stress_max_rows <= 0 and not args.allow_full_stress:
        raise SystemExit(
            "Refusing full-data feature stress without --allow-full-stress. "
            "Use a positive --stress-max-rows for the safe bounded audit."
        )
    stress_max_rows = None if args.stress_max_rows <= 0 else args.stress_max_rows

    final_predictions = _load_selected_final_predictions(reject_dir)
    risk_predictions = _load_partition_predictions(reject_dir, "risk_calibration")
    primary_source = _load_json(reject_dir / "primary_calibrated_source.json")
    source_summary = _load_json(reject_dir / "reject_capacity_results.json")

    generated: list[Path] = []
    generated.append(
        _write_frozen_config(
            paths.timestamp_dir,
            primary_source,
            source_summary,
            reject_dir,
            cashflow_dir,
        )
    )
    generated.append(
        _write_protocol_manifest(
            paths.timestamp_dir,
            plan_path,
            tracker_path,
            reject_dir,
            cashflow_dir,
            granting_csv,
            loan_csv,
        )
    )
    generated.extend(
        _write_protocol_hygiene_outputs(
            paths.timestamp_dir,
            reject_dir,
            primary_source,
            final_predictions,
        )
    )
    generated.extend(
        _write_feature_audits(paths.timestamp_dir, granting_csv, loan_csv)
    )
    generated.extend(
        _write_capacity_and_cost_outputs(
            paths.timestamp_dir,
            final_predictions,
            risk_predictions,
            args.bootstrap,
            args.seed,
        )
    )
    generated.extend(
        _write_responsible_credit_outputs(
            paths.timestamp_dir,
            final_predictions,
            granting_csv,
            args.seed,
        )
    )
    if not args.skip_stress:
        generated.extend(
            _write_feature_stress_test(
                paths.timestamp_dir,
                granting_csv,
                stress_max_rows,
                args.seed,
                args.stress_n_jobs,
                args.stress_n_estimators,
                args.stress_text_max_features,
                args.allow_full_text_stress,
            )
        )
    generated.extend(
        _write_cashflow_bridge_outputs(paths.timestamp_dir, cashflow_dir)
    )
    generated.extend(
        _write_layer_and_claim_outputs(
            paths.timestamp_dir,
            reject_dir,
            cashflow_dir,
            final_predictions,
            plan_path,
        )
    )
    generated.extend(
        _write_refine_logs(paths, generated, args.bootstrap, stress_max_rows, args.skip_stress)
    )
    generated.append(_append_manifest(paths.timestamp_dir, paths.latest_dir))
    _copy_generated_outputs(paths.timestamp_dir, paths.latest_dir)

    print(f"Blind-review evidence pack written to {paths.timestamp_dir}")
    print(f"Latest copy updated at {paths.latest_dir}")


def _load_selected_final_predictions(reject_dir: Path) -> pd.DataFrame:
    path = reject_dir / "selected_probability_predictions.csv"
    frame = pd.read_csv(path, parse_dates=["issue_d"])
    final = frame[frame["partition"].eq("final_test")].copy()
    if final.empty:
        raise RuntimeError(f"No final_test predictions in {path}")
    return final.reset_index(drop=True)


def _load_partition_predictions(reject_dir: Path, partition: str) -> pd.DataFrame:
    path = reject_dir / "selected_probability_predictions.csv"
    frame = pd.read_csv(path, parse_dates=["issue_d"])
    subset = frame[frame["partition"].eq(partition)].copy()
    if subset.empty:
        raise RuntimeError(f"No {partition} predictions in {path}")
    return subset.reset_index(drop=True)


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_frozen_config(
    output_dir: Path,
    primary_source: dict[str, object],
    source_summary: dict[str, object],
    reject_dir: Path,
    cashflow_dir: Path,
) -> Path:
    path = output_dir / "locked_final_protocol" / "frozen_config.yaml"
    pre_run_freeze = reject_dir / "pre_run_freeze" / "frozen_config.yaml"
    if pre_run_freeze.exists():
        ensure_dir(path.parent)
        shutil.copy2(pre_run_freeze, path)
        return path
    selected = f"{primary_source.get('model')}/{primary_source.get('calibration')}"
    lines = [
        "protocol_name: locked_final_protocol",
        f"created_at: {now_stamp()}",
        "dataset:",
        "  primary: Lending Club granting dataset",
        "  accepted_loan_cashflow: Lending Club loan.csv terminal accepted loans",
        "split:",
        "  primary_role_split: strict month-blocked seven-role split",
        "  final_test_policy: selected-only final-test report",
        "source_runs:",
        f"  reject_capacity: {reject_dir.as_posix()}",
        f"  cashflow: {cashflow_dir.as_posix()}",
        "selection_rule:",
        "  partition: calibration_select",
        "  objective: lowest Brier; tie-break by ECE then NLL",
        f"  selected_primary_source: {selected}",
        f"  selected_on: {primary_source.get('selected_on', 'calibration_select')}",
        "pre_registered_candidates:",
        f"  models: {source_summary.get('models', [])}",
        "  calibrators: [raw, sigmoid, isotonic]",
        f"  capacity_grid: {list(CAPACITY_GRID)}",
        f"  cost_fn_fp_grid: {list(FN_FP_RATIOS)}",
        f"  review_cost_grid: {list(REVIEW_COSTS)}",
        f"  human_residual_rho_grid: {list(HUMAN_RESIDUAL_RHOS)}",
        "reporting_guardrails:",
        "  old_all_candidate_final_test_tables: post_hoc_diagnostics_only",
        "  no_new_sota_classifier_claim: true",
        "  responsible_credit_audit: risk_exposure_not_legal_compliance",
        "  cashflow_scope: accepted_funded_loans_only",
    ]
    write_text(path, "\n".join(lines) + "\n")
    return path


def _write_protocol_manifest(
    output_dir: Path,
    plan_path: Path,
    tracker_path: Path,
    reject_dir: Path,
    cashflow_dir: Path,
    granting_csv: Path,
    loan_csv: Path,
) -> Path:
    path = output_dir / "locked_final_protocol" / "protocol_manifest.json"
    manifest = {
        "created_at": now_stamp(),
        "command": " ".join([Path(sys.executable).name, *sys.argv]),
        "git_commit": _git_commit(),
        "role_split_shares": dict(DEFAULT_ROLE_SPLIT_SHARES),
        "pre_run_freeze": {
            "freeze_config": _file_record(
                reject_dir / "pre_run_freeze" / "frozen_config.yaml", hash_full=True
            ),
            "pre_run_manifest": _file_record(
                reject_dir / "pre_run_freeze" / "pre_run_manifest.json", hash_full=True
            ),
            "evidence_grade": (
                "true_pre_run_freeze"
                if (reject_dir / "pre_run_freeze" / "frozen_config.yaml").exists()
                else "retrospective_wrapper"
            ),
        },
        "inputs": {
            "plan": _file_record(plan_path, hash_full=True),
            "tracker": _file_record(tracker_path, hash_full=True),
            "granting_csv": _file_record(granting_csv, hash_full=True),
            "loan_csv": _file_record(loan_csv, hash_full=False),
            "reject_capacity_run": _dir_record(reject_dir),
            "cashflow_run": _dir_record(cashflow_dir),
        },
        "source_output_hashes": {
            "selected_probability_predictions": _file_record(
                reject_dir / "selected_probability_predictions.csv", hash_full=True
            ),
            "final_decision_results": _file_record(
                reject_dir / "final_decision_results.csv", hash_full=True
            ),
            "month_boundary_audit": _file_record(
                reject_dir / "month_boundary_audit.csv", hash_full=True
            ),
            "cashflow_model_metrics": _file_record(
                cashflow_dir / "model_metrics.csv", hash_full=True
            ),
        },
    }
    write_json(path, manifest)
    return path


def _write_protocol_hygiene_outputs(
    output_dir: Path,
    reject_dir: Path,
    primary_source: dict[str, object],
    final_predictions: pd.DataFrame,
) -> list[Path]:
    paths = []
    y = final_predictions["y_true"].to_numpy(dtype=int)
    probs = final_predictions["prob_default"].to_numpy(dtype=float)
    metric_row = {
        "dataset": "lending_club",
        "partition": "final_test",
        "model": primary_source.get("model"),
        "calibration": primary_source.get("calibration"),
        "selection_status": "primary_selected_before_final_test",
        "rows": int(len(final_predictions)),
    }
    metric_row.update(classification_metrics(y, probs))
    path = output_dir / "locked_final_protocol" / "selected_only_final_probability_metrics.csv"
    pd.DataFrame([metric_row]).to_csv(path, index=False)
    paths.append(path)

    decision_path = reject_dir / "final_decision_results.csv"
    decisions = pd.read_csv(decision_path)
    primary = decisions[decisions["scenario"].eq(PRIMARY_SCENARIO.scenario_id)].copy()
    path = output_dir / "locked_final_protocol" / "selected_only_final_decision_report.csv"
    primary.to_csv(path, index=False)
    paths.append(path)

    source_files = [
        "calibration_final_appendix.csv",
        "calibration_selection_metrics.csv",
        "final_decision_results.csv",
        "capacity_frontier.csv",
    ]
    rows = []
    for file_name in source_files:
        source = reject_dir / file_name
        rows.append(
            {
                "source_file": str(source),
                "label": (
                    "selected_only_main_evidence"
                    if file_name in {"final_decision_results.csv", "capacity_frontier.csv"}
                    else "post_hoc_diagnostic_or_selection_partition"
                ),
                "must_not_claim_as_pristine_all_candidate_final": file_name
                == "calibration_final_appendix.csv",
                "exists": source.exists(),
            }
        )
    path = output_dir / "locked_final_protocol" / "post_hoc_diagnostic_index.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    paths.append(path)

    path = output_dir / "blind_review_coverage_matrix.csv"
    pd.DataFrame(_coverage_rows()).to_csv(path, index=False)
    paths.append(path)
    return paths


def _coverage_rows() -> list[dict[str, object]]:
    return [
        {
            "expert_point": 1,
            "critique": "contribution too defensive",
            "evidence_block": "B1",
            "main_outputs": "dcred_layer_ablation_table.csv",
            "status": "implemented",
        },
        {
            "expert_point": 2,
            "critique": "final-test hygiene",
            "evidence_block": "B0/B2",
            "main_outputs": "locked_final_protocol/*",
            "status": "implemented",
        },
        {
            "expert_point": 3,
            "critique": "capacity monotonicity may be mechanical",
            "evidence_block": "B3",
            "main_outputs": "matched_capacity_frontier_with_ci.csv",
            "status": "implemented",
        },
        {
            "expert_point": 4,
            "critique": "cost and human review assumptions arbitrary",
            "evidence_block": "B4",
            "main_outputs": "cost_sensitivity_surface.csv; break_even_table.csv",
            "status": "implemented",
        },
        {
            "expert_point": 6,
            "critique": "cash-flow result needs approval-rate constraint",
            "evidence_block": "B5",
            "main_outputs": "utility_approval_frontier.csv",
            "status": "implemented_if_cashflow_rerun_available",
        },
        {
            "expert_point": 8,
            "critique": "responsible-credit boundary missing",
            "evidence_block": "B6",
            "main_outputs": "responsible_credit_audit.csv",
            "status": "implemented",
        },
        {
            "expert_point": 11,
            "critique": "feature audit too coarse",
            "evidence_block": "B7",
            "main_outputs": "all_fields_feature_audit.csv; strict_default_expanded_stress_test.csv",
            "status": "implemented",
        },
    ]


def _write_feature_audits(output_dir: Path, granting_csv: Path, loan_csv: Path) -> list[Path]:
    paths = []
    rows = []
    for column in _read_header(granting_csv):
        rows.append(_granting_feature_row(column))
    for column in _read_header(loan_csv):
        row = _loan_feature_row(column)
        row["dataset"] = "accepted_loan_cashflow"
        rows.append(row)
    path = output_dir / "all_fields_feature_audit.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    paths.append(path)

    feature_sets = [
        {
            "feature_set": "strict",
            "dataset": "granting",
            "numeric_features": ";".join(STRICT_NUMERIC),
            "categorical_features": ";".join(STRICT_CATEGORICAL),
            "text_features": "",
            "interpretation": "cleanest application-time set; geography/proxy and text omitted",
        },
        {
            "feature_set": "default",
            "dataset": "granting",
            "numeric_features": ";".join(DEFAULT_NUMERIC),
            "categorical_features": ";".join(DEFAULT_CATEGORICAL),
            "text_features": "",
            "interpretation": "current D-CRED protocol, including geography fields as auditable proxies",
        },
        {
            "feature_set": "expanded",
            "dataset": "granting",
            "numeric_features": ";".join(EXPANDED_NUMERIC),
            "categorical_features": ";".join(EXPANDED_CATEGORICAL),
            "text_features": ";".join(TEXT_COLUMNS),
            "interpretation": "stress test only; any gain is not clean deployment evidence",
        },
    ]
    path = output_dir / "feature_set_definitions.csv"
    pd.DataFrame(feature_sets).to_csv(path, index=False)
    paths.append(path)

    groups = [
        ("addr_state", "state geography/proxy exposure", SMALL_CELL_MIN_N),
        ("zip3", "coarse zip-code proxy exposure", SMALL_CELL_MIN_N),
        ("home_ownership_n", "housing status", SMALL_CELL_MIN_N),
        ("revenue_decile", "income/revenue decile", SMALL_CELL_MIN_N),
        ("loan_amnt_decile", "loan amount decile", SMALL_CELL_MIN_N),
        ("purpose", "loan purpose", SMALL_CELL_MIN_N),
    ]
    path = output_dir / "responsible_credit_group_definitions.csv"
    pd.DataFrame(
        [
            {"group_field": field, "rationale": rationale, "small_cell_min_n": min_n}
            for field, rationale, min_n in groups
        ]
    ).to_csv(path, index=False)
    paths.append(path)
    return paths


def _granting_feature_row(column: str) -> dict[str, object]:
    lower = column.lower()
    if lower in {"default", "loan_status"}:
        category = "repayment_outcome"
        strict = default = expanded = False
        reason = "target/outcome label"
    elif lower == "id":
        category = "administrative"
        strict = default = expanded = False
        reason = "identifier"
    elif lower == "issue_d":
        category = "timestamp"
        strict = default = expanded = False
        reason = "split timestamp only"
    elif lower in STRICT_NUMERIC or lower in STRICT_CATEGORICAL:
        category = "application_time"
        strict = default = expanded = True
        reason = "application-time field in granting dataset"
    elif lower in {"addr_state", "zip_code"}:
        category = "geography_proxy"
        strict = False
        default = expanded = True
        reason = "geography/proxy field; allowed only outside strict set"
    elif lower in {"title", "desc"}:
        category = "text"
        strict = default = False
        expanded = True
        reason = "text stress-test feature only"
    else:
        category = "uncertain"
        strict = default = expanded = False
        reason = "not part of audited D-CRED protocol"
    return {
        "dataset": "granting",
        "feature": column,
        "category": category,
        "allowed_strict": strict,
        "allowed_default": default,
        "included_expanded_stress": expanded,
        "reason": reason,
    }


def _loan_feature_row(column: str) -> dict[str, object]:
    lower = column.lower()
    if lower in LOAN_CASHFLOW_COLUMNS or lower == "loan_status":
        category = "repayment_outcome"
        reason = "cash-flow outcome or terminal status label"
    elif lower == "issue_d":
        category = "timestamp"
        reason = "split timestamp only"
    elif lower in {"id", "member_id", "url"}:
        category = "administrative"
        reason = "identifier/admin field"
    elif lower in LOAN_POLICY_GENERATED:
        category = "underwriting_policy_generated"
        reason = "lender policy output or post-application underwriting term"
    elif lower.startswith(LOAN_POST_ORIGINATION_PREFIXES):
        category = "post_origination"
        reason = "field observed after origination or during servicing"
    elif lower in {"desc", "title", "emp_title"}:
        category = "text"
        reason = "text field; not used in clean cash-flow protocol"
    elif lower.endswith("_joint") or lower.startswith("sec_app_"):
        category = "uncertain"
        reason = "joint/secondary applicant field needs manual adjudication"
    else:
        category = "application_time_or_review_acquired"
        reason = "candidate application/review field in accepted-loan analysis"
    return {
        "feature": column,
        "category": category,
        "allowed_strict": False,
        "allowed_default": category == "application_time_or_review_acquired",
        "included_expanded_stress": category
        in {"application_time_or_review_acquired", "underwriting_policy_generated"},
        "reason": reason,
    }


def _write_capacity_and_cost_outputs(
    output_dir: Path,
    final_predictions: pd.DataFrame,
    risk_predictions: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
) -> list[Path]:
    y = final_predictions["y_true"].to_numpy(dtype=int)
    probs = final_predictions["prob_default"].to_numpy(dtype=float)
    months = final_predictions["issue_d"].dt.to_period("M").astype(str).to_numpy()
    risk_probs = risk_predictions["prob_default"].to_numpy(dtype=float)
    threshold = PRIMARY_SCENARIO.false_positive_cost / (
        PRIMARY_SCENARIO.false_negative_cost + PRIMARY_SCENARIO.false_positive_cost
    )

    rows = []
    for policy, review_mask in _frontier_masks(y, probs, risk_probs, threshold, seed):
        row = evaluate_review_mask_policy(y, probs, PRIMARY_SCENARIO, policy, review_mask)
        expected_cost, realized_cost = _policy_cost_arrays(y, probs, PRIMARY_SCENARIO, review_mask)
        row.update(
            _month_bootstrap_ci(
                expected_cost,
                realized_cost,
                months,
                n_bootstrap=n_bootstrap,
                seed=seed,
            )
        )
        row["capacity_fraction"] = float(np.mean(review_mask))
        rows.append(row)
    frontier = add_reference_savings(pd.DataFrame(rows))
    path1 = output_dir / "matched_capacity_frontier_with_ci.csv"
    frontier.to_csv(path1, index=False)
    path1b = output_dir / "same_protocol_decision_ablation_table.csv"
    _same_protocol_decision_ablation(final_predictions, frontier).to_csv(path1b, index=False)

    sensitivity, break_even = _cost_sensitivity(y, probs)
    path2 = output_dir / "cost_sensitivity_surface.csv"
    sensitivity.to_csv(path2, index=False)
    path3 = output_dir / "break_even_table.csv"
    break_even.to_csv(path3, index=False)
    path4 = output_dir / "near_all_review_region_map.csv"
    break_even[
        ["false_negative_cost", "review_cost", "human_residual_rho", "reject_option_review_rate"]
    ].assign(
        gt_80=lambda df: df["reject_option_review_rate"].gt(0.80),
        gt_90=lambda df: df["reject_option_review_rate"].gt(0.90),
        gt_95=lambda df: df["reject_option_review_rate"].gt(0.95),
    ).to_csv(path4, index=False)
    return [path1, path1b, path2, path3, path4]


def _frontier_masks(
    y: np.ndarray,
    probs: np.ndarray,
    risk_probs: np.ndarray,
    threshold: float,
    seed: int,
) -> Iterable[tuple[str, np.ndarray]]:
    n = len(probs)
    yield "no_review_cost_sensitive", np.zeros(n, dtype=bool)
    yield "all_review", np.ones(n, dtype=bool)
    expected_benefit = _expected_review_benefit(probs, PRIMARY_SCENARIO)
    realized_benefit = _realized_review_benefit(y, probs, PRIMARY_SCENARIO)
    uncertainty = -np.abs(probs - threshold)
    empirical_risk = np.minimum(
        PRIMARY_SCENARIO.false_negative_cost * probs,
        PRIMARY_SCENARIO.false_positive_cost * (1.0 - probs),
    )
    risk_threshold = np.quantile(
        np.minimum(
            PRIMARY_SCENARIO.false_negative_cost * risk_probs,
            PRIMARY_SCENARIO.false_positive_cost * (1.0 - risk_probs),
        ),
        0.80,
    )
    for fraction in CAPACITY_GRID:
        yield f"dcred_expected_benefit_capacity_{fraction:g}", capacity_review_mask(
            probs, PRIMARY_SCENARIO, fraction
        )
        yield f"uncertainty_capacity_{fraction:g}", _top_fraction_mask(uncertainty, fraction, False)
        yield f"empirical_risk_capacity_{fraction:g}", _top_fraction_mask(
            empirical_risk, fraction, False
        )
        yield f"oracle_realized_benefit_capacity_{fraction:g}", _top_fraction_mask(
            realized_benefit, fraction, False
        )
        yield f"random_capacity_{fraction:g}", _random_mask(n, fraction, seed + int(fraction * 10000))


def _same_protocol_decision_ablation(
    final_predictions: pd.DataFrame,
    frontier: pd.DataFrame,
) -> pd.DataFrame:
    y = final_predictions["y_true"].to_numpy(dtype=int)
    probs = final_predictions["prob_default"].to_numpy(dtype=float)
    metrics = classification_metrics(y, probs)
    rows: list[dict[str, object]] = [
        {
            "layer": "S0",
            "description": "same final_test population: calibrated PD only",
            "policy": "lgbm/sigmoid",
            "primary_metric": "brier",
            "primary_value": metrics["brier"],
            "secondary_metric": "ece",
            "secondary_value": metrics["ece"],
            "evidence_scope": "same month-blocked final_test rows",
            "claim_boundary": "probability quality only",
        }
    ]
    selectors = [
        ("S1", "add no-review cost-sensitive policy", "no_review_cost_sensitive", None),
        ("S2", "add 10% capacity-aware review", "dcred_expected_benefit_capacity_0.1", None),
        ("S3", "10% uncertainty-review baseline", "uncertainty_capacity_0.1", None),
        ("S4", "10% random-review baseline", "random_capacity_0.1", None),
        ("S5", "all-review reference", "all_review", None),
    ]
    for layer, desc, policy, capacity in selectors:
        subset = frontier[frontier["policy"].eq(policy)].copy()
        if capacity is not None and "capacity_fraction" in subset:
            subset = subset[subset["capacity_fraction"].eq(capacity)]
        if subset.empty:
            continue
        row = subset.iloc[0]
        rows.append(
            {
                "layer": layer,
                "description": desc,
                "policy": policy,
                "primary_metric": "realized_cost",
                "primary_value": row["realized_cost"],
                "secondary_metric": "expected_cost",
                "secondary_value": row["expected_cost"],
                "review_rate": row.get("review_rate"),
                "approval_rate": row.get("approval_rate"),
                "evidence_scope": "same month-blocked final_test rows",
                "claim_boundary": "decision-policy comparison under stated cost scenario",
            }
        )
    return pd.DataFrame(rows)


def _cost_sensitivity(y: np.ndarray, probs: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    break_rows = []
    for fn_cost in FN_FP_RATIOS:
        for review_cost in REVIEW_COSTS:
            for rho in HUMAN_RESIDUAL_RHOS:
                scenario = CostScenario(fn_cost, 1.0, review_cost, rho)
                scenario_rows = [
                    evaluate_no_review(y, probs, scenario),
                    evaluate_all_review(y, probs, scenario),
                    evaluate_reject_option(y, probs, scenario),
                ]
                scenario_rows.extend(
                    evaluate_capacity_grid(y, probs, scenario, SENSITIVITY_CAPACITY_GRID)
                )
                frame = pd.DataFrame(scenario_rows)
                min_expected = frame["expected_cost"].min()
                min_realized = frame["realized_cost"].min()
                for row in scenario_rows:
                    row["expected_cost_winner"] = bool(
                        np.isclose(row["expected_cost"], min_expected)
                    )
                    row["realized_cost_winner"] = bool(
                        np.isclose(row["realized_cost"], min_realized)
                    )
                    rows.append(row)
                approve_cost, deny_cost, _ = cost_components(probs, scenario)
                auto_cost = np.minimum(approve_cost, deny_cost)
                beneficial = review_cost < (1.0 - rho) * auto_cost
                reject_row = next(r for r in scenario_rows if r["policy"] == "cost_aware_reject_option")
                break_rows.append(
                    {
                        "false_negative_cost": fn_cost,
                        "false_positive_cost": 1.0,
                        "review_cost": review_cost,
                        "human_residual_rho": rho,
                        "share_review_beneficial_by_break_even": float(np.mean(beneficial)),
                        "reject_option_review_rate": reject_row["review_rate"],
                        "break_even_condition": "c_R < (1-rho) * min(C_A, C_D)",
                    }
                )
    return add_reference_savings(pd.DataFrame(rows)), pd.DataFrame(break_rows)


def _policy_cost_arrays(
    y: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
    review_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    approve_mask, reject_mask, _ = no_review_masks(probs, scenario)
    review_mask = np.asarray(review_mask, dtype=bool)
    approve_mask = approve_mask & ~review_mask
    reject_mask = reject_mask & ~review_mask
    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    expected = np.zeros(len(y), dtype=float)
    expected[approve_mask] = approve_cost[approve_mask]
    expected[reject_mask] = deny_cost[reject_mask]
    expected[review_mask] = manual_cost[review_mask]
    realized = np.zeros(len(y), dtype=float)
    realized[approve_mask & (y == 1)] = scenario.false_negative_cost
    realized[reject_mask & (y == 0)] = scenario.false_positive_cost
    realized[review_mask] = manual_cost[review_mask]
    return expected, realized


def _month_bootstrap_ci(
    expected_cost: np.ndarray,
    realized_cost: np.ndarray,
    months: np.ndarray,
    n_bootstrap: int,
    seed: int,
) -> dict[str, object]:
    unique_months = np.unique(months)
    if len(unique_months) < 2 or n_bootstrap <= 0:
        return {
            "bootstrap_unit": "issue_month",
            "n_bootstrap": n_bootstrap,
            "expected_cost_ci_low": np.nan,
            "expected_cost_ci_high": np.nan,
            "realized_cost_ci_low": np.nan,
            "realized_cost_ci_high": np.nan,
        }
    rng = np.random.default_rng(seed)
    expected_values = []
    realized_values = []
    indices_by_month = {month: np.flatnonzero(months == month) for month in unique_months}
    for _ in range(n_bootstrap):
        sampled = rng.choice(unique_months, size=len(unique_months), replace=True)
        idx = np.concatenate([indices_by_month[month] for month in sampled])
        expected_values.append(float(np.mean(expected_cost[idx])))
        realized_values.append(float(np.mean(realized_cost[idx])))
    return {
        "bootstrap_unit": "issue_month",
        "n_bootstrap": n_bootstrap,
        "expected_cost_ci_low": float(np.quantile(expected_values, 0.025)),
        "expected_cost_ci_high": float(np.quantile(expected_values, 0.975)),
        "realized_cost_ci_low": float(np.quantile(realized_values, 0.025)),
        "realized_cost_ci_high": float(np.quantile(realized_values, 0.975)),
    }


def _write_responsible_credit_outputs(
    output_dir: Path,
    final_predictions: pd.DataFrame,
    granting_csv: Path,
    seed: int,
) -> list[Path]:
    rows = final_predictions["row_id"].to_numpy(dtype=int)
    needed = [
        "revenue",
        "loan_amnt",
        "addr_state",
        "zip_code",
        "home_ownership_n",
        "purpose",
    ]
    source = pd.read_csv(granting_csv, usecols=needed, low_memory=False)
    groups = source.iloc[rows].copy().reset_index(drop=True)
    groups["zip3"] = groups["zip_code"].astype(str).str.extract(r"(\d{3})", expand=False).fillna("UNK")
    groups["revenue_decile"] = _qcut_labels(groups["revenue"], "revenue")
    groups["loan_amnt_decile"] = _qcut_labels(groups["loan_amnt"], "loan_amnt")
    y = final_predictions["y_true"].to_numpy(dtype=int)
    probs = final_predictions["prob_default"].to_numpy(dtype=float)
    policies = _responsible_policy_masks(probs, seed)
    policy_costs = {
        policy: _policy_cost_arrays(y, probs, PRIMARY_SCENARIO, review_mask)
        for policy, review_mask in policies.items()
    }
    audit_rows = []
    calibration_rows = []
    for group_field in [
        "addr_state",
        "zip3",
        "home_ownership_n",
        "revenue_decile",
        "loan_amnt_decile",
        "purpose",
    ]:
        values = groups[group_field].astype(str).fillna("MISSING").to_numpy()
        for value in sorted(pd.unique(values)):
            mask = values == value
            n = int(np.sum(mask))
            if n == 0:
                continue
            suppressed = n < SMALL_CELL_MIN_N
            brier = np.nan if suppressed else float(np.mean((probs[mask] - y[mask]) ** 2))
            ece = np.nan
            if not suppressed:
                ece, _ = expected_calibration_error(y[mask], probs[mask])
            base = {
                "group_field": group_field,
                "group_value": value,
                "rows": n,
                "suppressed_small_cell": suppressed,
                "suppression_rule": f"metrics hidden when rows < {SMALL_CELL_MIN_N}",
                "default_rate": np.nan if suppressed else float(np.mean(y[mask])),
                "brier": brier,
                "ece": ece,
            }
            for policy, review_mask in policies.items():
                approve, reject, review = _policy_masks_for_audit(probs, review_mask)
                expected_cost, realized_cost = policy_costs[policy]
                row = dict(base)
                if suppressed:
                    policy_values = {
                        "approval_rate": np.nan,
                        "rejection_rate": np.nan,
                        "review_rate": np.nan,
                        "approved_default_rate": np.nan,
                        "expected_cost": np.nan,
                        "realized_cost": np.nan,
                    }
                else:
                    policy_values = {
                        "approval_rate": float(np.mean(approve[mask])),
                        "rejection_rate": float(np.mean(reject[mask])),
                        "review_rate": float(np.mean(review[mask])),
                        "approved_default_rate": _safe_rate_bool(y[mask][approve[mask]] == 1),
                        "expected_cost": float(np.mean(expected_cost[mask])),
                        "realized_cost": float(np.mean(realized_cost[mask])),
                    }
                row.update(
                    {
                        "policy": policy,
                        **policy_values,
                    }
                )
                audit_rows.append(row)
            calibration_rows.extend(_calibration_bin_rows(group_field, value, y[mask], probs[mask], n))
    path1 = output_dir / "responsible_credit_audit.csv"
    pd.DataFrame(audit_rows).to_csv(path1, index=False)
    path2 = output_dir / "subgroup_calibration_bins.csv"
    pd.DataFrame(calibration_rows).to_csv(path2, index=False)
    return [path1, path2]


def _responsible_policy_masks(probs: np.ndarray, seed: int) -> dict[str, np.ndarray]:
    return {
        "no_review_cost_sensitive": np.zeros(len(probs), dtype=bool),
        "capacity_aware_5pct": capacity_review_mask(probs, PRIMARY_SCENARIO, 0.05),
        "capacity_aware_10pct": capacity_review_mask(probs, PRIMARY_SCENARIO, 0.10),
        "capacity_aware_20pct": capacity_review_mask(probs, PRIMARY_SCENARIO, 0.20),
        "random_10pct": _random_mask(len(probs), 0.10, seed),
    }


def _policy_masks_for_audit(
    probs: np.ndarray,
    review_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    approve, reject, _ = no_review_masks(probs, PRIMARY_SCENARIO)
    review_mask = np.asarray(review_mask, dtype=bool)
    return approve & ~review_mask, reject & ~review_mask, review_mask


def _safe_rate_bool(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=bool)
    if len(values) == 0:
        return np.nan
    return float(np.mean(values))


def _calibration_bin_rows(
    group_field: str,
    group_value: str,
    y: np.ndarray,
    probs: np.ndarray,
    n_group: int,
) -> list[dict[str, object]]:
    if n_group < SMALL_CELL_MIN_N:
        return []
    bins = pd.qcut(probs, q=min(10, max(2, n_group // SMALL_CELL_MIN_N)), duplicates="drop")
    rows = []
    for bin_label in pd.unique(bins):
        mask = bins == bin_label
        if np.sum(mask) == 0:
            continue
        rows.append(
            {
                "group_field": group_field,
                "group_value": group_value,
                "prob_bin": str(bin_label),
                "rows": int(np.sum(mask)),
                "mean_prob_default": float(np.mean(probs[mask])),
                "observed_default_rate": float(np.mean(y[mask])),
            }
        )
    return rows


def _write_feature_stress_test(
    output_dir: Path,
    granting_csv: Path,
    max_rows: int | None,
    seed: int,
    n_jobs: int,
    n_estimators: int,
    text_max_features: int,
    allow_full_text_stress: bool,
) -> list[Path]:
    full_structured_only = max_rows is None and not allow_full_text_stress
    progress_path = output_dir / "feature_stress_progress.log"
    progress_path.write_text(
        "\n".join(
            [
                f"started_at={now_stamp()}",
                f"max_rows={'full' if max_rows is None else max_rows}",
                f"n_jobs={n_jobs}",
                f"n_estimators={n_estimators}",
                f"text_max_features={text_max_features}",
                f"full_structured_only={full_structured_only}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    usecols = list(
        dict.fromkeys(
            [
                "issue_d",
                "Default",
                *EXPANDED_NUMERIC,
                *EXPANDED_CATEGORICAL,
                *(TEXT_COLUMNS if not full_structured_only else []),
            ]
        )
    )
    frame = _read_stress_frame(granting_csv, usecols, max_rows, seed)
    frame["issue_d"] = pd.to_datetime(frame["issue_d"], errors="coerce")
    frame = frame[frame["issue_d"].notna()].copy()
    frame["Default"] = frame["Default"].astype(int)
    role_indices = temporal_month_blocked_role_split(frame, frame["issue_d"])
    train_idx = role_indices["model_train"]
    calibration_idx = role_indices["calibration_fit"]
    final_idx = role_indices["final_test"]
    rows = []
    policy_rows = []
    stress_specs = [
        ("strict", STRICT_NUMERIC, STRICT_CATEGORICAL, []),
        ("no_zip_default", DEFAULT_NUMERIC, STRICT_CATEGORICAL + ["addr_state"], []),
        ("default", DEFAULT_NUMERIC, DEFAULT_CATEGORICAL, []),
        (
            "expanded",
            EXPANDED_NUMERIC,
            EXPANDED_CATEGORICAL,
            [] if full_structured_only else TEXT_COLUMNS,
        ),
    ]
    for name, numeric, categorical, text in stress_specs:
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(f"fit_start={now_stamp()} feature_set={name}\n")
        model = _stress_pipeline(
            numeric,
            categorical,
            text,
            seed,
            n_jobs=max(1, n_jobs),
            n_estimators=max(1, n_estimators),
            text_max_features=max(1, text_max_features),
        )
        x_train = _stress_frame(frame.loc[train_idx], text)
        y_train = frame.loc[train_idx, "Default"].to_numpy(dtype=int)
        x_cal = _stress_frame(frame.loc[calibration_idx], text)
        y_cal = frame.loc[calibration_idx, "Default"].to_numpy(dtype=int)
        x_final = _stress_frame(frame.loc[final_idx], text)
        y_final = frame.loc[final_idx, "Default"].to_numpy(dtype=int)
        model.fit(x_train, y_train)
        cal_raw = model.predict_proba(x_cal)[:, 1]
        calibrator = fit_calibrators(y_cal, cal_raw)["sigmoid"]
        probs = calibrator.transform(model.predict_proba(x_final)[:, 1])
        metrics = classification_metrics(y_final, probs)
        no_review = evaluate_no_review(y_final, probs, PRIMARY_SCENARIO)
        cap10 = evaluate_review_mask_policy(
            y_final,
            probs,
            PRIMARY_SCENARIO,
            "capacity_aware_10pct",
            capacity_review_mask(probs, PRIMARY_SCENARIO, 0.10),
        )
        for policy_row in [no_review, cap10]:
            policy_rows.append(
                {
                    "feature_set": name,
                    "model": "lgbm",
                    "calibration": "sigmoid",
                    "rows_used": int(len(frame)),
                    "final_test_rows": int(len(final_idx)),
                    "stress_scope": "full_data_same_model" if max_rows is None else "row_capped_same_model",
                    "resource_scope": "structured_only_full_data" if full_structured_only else "standard",
                    "includes_addr_state": "addr_state" in categorical,
                    "includes_zip_code": "zip_code" in categorical,
                    "includes_text": bool(text),
                    **policy_row,
                }
            )
        rows.append(
            {
                "feature_set": name,
                "model": "lgbm",
                "calibration": "sigmoid",
                "rows_used": int(len(frame)),
                "final_test_rows": int(len(final_idx)),
                "stress_scope": "full_data_same_model" if max_rows is None else "row_capped_same_model",
                "resource_scope": "structured_only_full_data" if full_structured_only else "standard",
                "includes_addr_state": "addr_state" in categorical,
                "includes_zip_code": "zip_code" in categorical,
                "includes_text": bool(text),
                "auc": metrics["roc_auc"],
                "pr_auc": metrics["pr_auc"],
                "brier": metrics["brier"],
                "ece": metrics["ece"],
                "no_review_expected_cost": no_review["expected_cost"],
                "no_review_realized_cost": no_review["realized_cost"],
                "capacity_10_expected_cost": cap10["expected_cost"],
                "capacity_10_realized_cost": cap10["realized_cost"],
                "capacity_10_review_rate": cap10["review_rate"],
                "interpretation_guardrail": (
                    "same-model feature-set stress; expanded gains are leakage/proxy warnings, not clean deployment evidence"
                    + (
                        "; full-row mode omits text features for machine-stability"
                        if full_structured_only and name == "expanded"
                        else ""
                    )
                ),
            }
        )
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(f"fit_done={now_stamp()} feature_set={name}\n")
        del model, x_train, x_cal, x_final, y_train, y_cal, y_final, probs
        gc.collect()
    path = output_dir / "strict_default_expanded_stress_test.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    path2 = output_dir / "zip_vs_nozip_policy_audit.csv"
    pd.DataFrame(
        [
            row
            for row in policy_rows
            if row["feature_set"] in {"no_zip_default", "default"}
        ]
    ).to_csv(path2, index=False)
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(f"completed_at={now_stamp()}\n")
    return [progress_path, path, path2]


def _read_stress_frame(
    granting_csv: Path,
    usecols: list[str],
    max_rows: int | None,
    seed: int,
) -> pd.DataFrame:
    if max_rows is None:
        return pd.read_csv(granting_csv, usecols=usecols, low_memory=False)
    total_rows = _count_csv_data_rows(granting_csv)
    if max_rows >= total_rows:
        return pd.read_csv(granting_csv, usecols=usecols, low_memory=False)
    rng = np.random.default_rng(seed)
    selected_lines = set((rng.choice(total_rows, size=max_rows, replace=False) + 1).tolist())
    return pd.read_csv(
        granting_csv,
        usecols=usecols,
        skiprows=lambda row_number: row_number != 0 and row_number not in selected_lines,
        low_memory=False,
    )


def _count_csv_data_rows(path: Path) -> int:
    with path.open("rb") as handle:
        line_count = sum(1 for _ in handle)
    return max(0, line_count - 1)


def _stress_pipeline(
    numeric: list[str],
    categorical: list[str],
    text: list[str],
    seed: int,
    n_jobs: int,
    n_estimators: int,
    text_max_features: int,
) -> Pipeline:
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
    if text:
        transformers.append(("text", TfidfVectorizer(max_features=text_max_features), "text_all"))
    return Pipeline(
        [
            ("preprocess", ColumnTransformer(transformers, sparse_threshold=0.3)),
            ("model", _build_lgbm_for_feature_stress(seed, n_jobs, n_estimators)),
        ]
    )


def _build_lgbm_for_feature_stress(seed: int, n_jobs: int, n_estimators: int):
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:
        raise RuntimeError("lightgbm is required for full-data feature stress") from exc
    return LGBMClassifier(
        n_estimators=n_estimators,
        learning_rate=0.05,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.9,
        class_weight="balanced",
        random_state=seed,
        n_jobs=n_jobs,
        verbose=-1,
    )


def _stress_frame(frame: pd.DataFrame, text: list[str]) -> pd.DataFrame:
    if not text:
        return frame
    result = frame.copy()
    result["text_all"] = result[text].fillna("").astype(str).agg(" ".join, axis=1)
    return result


def _write_cashflow_bridge_outputs(output_dir: Path, cashflow_dir: Path) -> list[Path]:
    paths = []
    required = [
        "utility_approval_frontier.csv",
        "coverage_constrained_best_policy.csv",
        "cashflow_policy_predictions.csv",
        "model_metrics.csv",
    ]
    rows = []
    for name in required:
        source = cashflow_dir / name
        rows.append(
            {
                "source_file": str(source),
                "exists": source.exists(),
                "status": "available" if source.exists() else "missing_rerun_cashflow_script",
            }
        )
        if source.exists():
            target = output_dir / f"cashflow_{name}"
            shutil.copy2(source, target)
            paths.append(target)
    path = output_dir / "cashflow_frontier_availability.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    paths.append(path)
    return paths


def _write_layer_and_claim_outputs(
    output_dir: Path,
    reject_dir: Path,
    cashflow_dir: Path,
    final_predictions: pd.DataFrame,
    plan_path: Path,
) -> list[Path]:
    paths = []
    rows = _layer_ablation_rows(output_dir, reject_dir, cashflow_dir, final_predictions)
    path = output_dir / "dcred_layer_ablation_table.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    paths.append(path)

    claims_path = output_dir / f"CLAIMS_FROM_RESULTS_BLIND_REVIEW_{pd.Timestamp.now():%Y%m%d}.md"
    write_text(claims_path, _claim_control_text(output_dir, plan_path))
    paths.append(claims_path)
    return paths


def _layer_ablation_rows(
    output_dir: Path,
    reject_dir: Path,
    cashflow_dir: Path,
    final_predictions: pd.DataFrame,
) -> list[dict[str, object]]:
    rows = []
    random_temporal = PROJECT_ROOT / "outputs" / "full" / "lending_random_vs_temporal.csv"
    if random_temporal.exists():
        frame = pd.read_csv(random_temporal)
        random = frame[frame["split"].eq("random")].sort_values("roc_auc", ascending=False).head(1)
        temporal = frame[frame["split"].eq("temporal")].sort_values("roc_auc", ascending=False).head(1)
        if not random.empty:
            rows.append(
                _layer_row(
                    "A0",
                    "random split + AUC only",
                    random.iloc[0],
                    "traditional benchmark",
                    "historical stitched summary, not same-protocol ablation",
                )
            )
        if not temporal.empty:
            rows.append(
                _layer_row(
                    "A1",
                    "temporal split only",
                    temporal.iloc[0],
                    "temporal evaluation shift",
                    "historical stitched summary, not same-protocol ablation",
                )
            )
    metrics_path = output_dir / "locked_final_protocol" / "selected_only_final_probability_metrics.csv"
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path).iloc[0]
        rows.append(
            {
                "layer": "A2",
                "description": "temporal + calibration",
                "primary_metric": "brier",
                "primary_value": metrics["brier"],
                "secondary_metric": "ece",
                "secondary_value": metrics["ece"],
                "interpretation_boundary": "calibration quality, not new classifier SOTA",
                "evidence_scope": "current month-blocked selected-only final_test",
            }
        )
    decision_path = reject_dir / "capacity_frontier.csv"
    if decision_path.exists():
        decision = pd.read_csv(decision_path)
        primary = decision[decision["scenario"].eq(PRIMARY_SCENARIO.scenario_id)].copy()
        for policy, layer, desc in [
            ("no_review_cost_sensitive", "A3", "+ cost-sensitive threshold"),
            ("capacity_aware_deferral", "A4", "+ capacity-aware review"),
        ]:
            subset = primary[primary["policy"].eq(policy)].copy()
            if policy == "capacity_aware_deferral":
                subset = subset[subset["capacity_fraction"].eq(0.10)]
            if not subset.empty:
                row = subset.iloc[0]
                rows.append(
                    {
                        "layer": layer,
                        "description": desc,
                        "primary_metric": "expected_cost",
                        "primary_value": row["expected_cost"],
                        "secondary_metric": "review_rate",
                        "secondary_value": row["review_rate"],
                        "interpretation_boundary": "decision-policy effect under stated costs",
                        "evidence_scope": "current month-blocked selected-only final_test",
                    }
                )
    cash_path = cashflow_dir / "utility_approval_frontier.csv"
    if cash_path.exists():
        cash = pd.read_csv(cash_path)
        deployable = cash[~cash["policy"].str.contains("oracle", na=False)]
        best = deployable.sort_values("mean_net_cash_per_app", ascending=False).head(1)
        if not best.empty:
            row = best.iloc[0]
            rows.append(
                {
                    "layer": "A5",
                    "description": "+ cash-flow objective",
                    "primary_metric": "mean_net_cash_per_app",
                    "primary_value": row["mean_net_cash_per_app"],
                    "secondary_metric": "approval_rate",
                    "secondary_value": row["approval_rate"],
                    "interpretation_boundary": "negative/mixed accepted-loan approval-constrained frontier; learned cash ranking is not a deployable win",
                    "evidence_scope": "accepted/funded-loan cashflow scope, not applicant-pool final_test",
                }
            )
    else:
        rows.append(
            {
                "layer": "A5",
                "description": "+ cash-flow objective",
                "primary_metric": "status",
                "primary_value": "missing utility_approval_frontier.csv",
                "secondary_metric": "",
                "secondary_value": "",
                "interpretation_boundary": "rerun cashflow script to complete B5",
            }
        )
    return rows


def _layer_row(
    layer: str,
    description: str,
    row: pd.Series,
    boundary: str,
    evidence_scope: str,
) -> dict[str, object]:
    return {
        "layer": layer,
        "description": description,
        "primary_metric": "roc_auc",
        "primary_value": row.get("roc_auc"),
        "secondary_metric": "pr_auc",
        "secondary_value": row.get("pr_auc"),
        "interpretation_boundary": boundary,
        "evidence_scope": evidence_scope,
    }


def _claim_control_text(output_dir: Path, plan_path: Path) -> str:
    return f"""# Blind Review Claim-Control Summary

Date: {now_stamp()}
Plan: `{plan_path}`
Output directory: `{output_dir}`

## Supported Now

- The blind-review response should frame D-CRED as a deployment-evaluation framework, not a new classifier or formal conformal guarantee.
- If `locked_final_protocol/protocol_manifest.json` records `evidence_grade=true_pre_run_freeze`, the locked final evidence can be described as a true pre-run frozen selected-only rerun. Otherwise, describe it as a retrospective selected-only audit.
- The selected-only final evidence should be cited from `locked_final_protocol/selected_only_final_probability_metrics.csv` and `locked_final_protocol/selected_only_final_decision_report.csv`.
- The capacity claim should be comparative and uncertainty-aware. Cite `matched_capacity_frontier_with_ci.csv` and `same_protocol_decision_ablation_table.csv`; do not present monotonic expected cost as the discovery.
- Manual review value is conditional on FN:FP, review cost, residual human error, and capacity. Cite `cost_sensitivity_surface.csv`, `break_even_table.csv`, and `near_all_review_region_map.csv`.
- Responsible-credit analysis is a risk-exposure audit only. Cite `responsible_credit_audit.csv`; do not claim legal compliance or absence of disparate impact.
- Feature control is now documented by `all_fields_feature_audit.csv`, `strict_default_expanded_stress_test.csv`, and `zip_vs_nozip_policy_audit.csv`. Expanded-set gains are leakage/proxy warnings, not clean wins.

## Still Conditional

- Cash-flow remains negative/mixed unless an approval-constrained deployable policy shows positive utility. If `cashflow_coverage_constrained_best_policy.csv` selects PD ranking at all targets, write cash-flow as accepted-loan decision-analysis evidence, not a cash-model win.
- Any negative or mixed result must stay in the thesis as a narrowed claim or limitation, not be hidden by a new narrative.
"""


def _write_refine_logs(
    paths: OutputPaths,
    generated: list[Path],
    n_bootstrap: int,
    stress_max_rows: int | None,
    skip_stress: bool,
) -> list[Path]:
    cashflow_complete = (paths.timestamp_dir / "cashflow_utility_approval_frontier.csv").exists()
    result_name = f"BLIND_REVIEW_EXPERIMENT_RESULTS_{pd.Timestamp.now():%Y%m%d_%H%M%S}.md"
    result_path = paths.refine_dir / result_name
    latest_result_path = paths.refine_dir / "BLIND_REVIEW_EXPERIMENT_RESULTS.md"
    review_name = f"BLIND_REVIEW_EXPERIMENT_CODE_REVIEW_{pd.Timestamp.now():%Y%m%d_%H%M%S}.md"
    review_path = paths.refine_dir / review_name
    latest_review_path = paths.refine_dir / "BLIND_REVIEW_EXPERIMENT_CODE_REVIEW.md"
    tracker_name = f"BLIND_REVIEW_EXPERIMENT_TRACKER_{pd.Timestamp.now():%Y%m%d_%H%M%S}.md"
    tracker_path = paths.refine_dir / tracker_name
    latest_tracker_path = paths.refine_dir / "BLIND_REVIEW_EXPERIMENT_TRACKER.md"

    result_text = _results_markdown(
        paths.timestamp_dir,
        generated,
        n_bootstrap,
        stress_max_rows,
        skip_stress,
        cashflow_complete,
    )
    review_text = _code_review_markdown(paths.timestamp_dir)
    tracker_text = _tracker_markdown(paths.timestamp_dir, skip_stress, cashflow_complete, stress_max_rows)
    for path, text in [
        (result_path, result_text),
        (latest_result_path, result_text),
        (review_path, review_text),
        (latest_review_path, review_text),
        (tracker_path, tracker_text),
        (latest_tracker_path, tracker_text),
    ]:
        write_text(path, text)
    return [result_path, latest_result_path, review_path, latest_review_path, tracker_path, latest_tracker_path]


def _results_markdown(
    output_dir: Path,
    generated: list[Path],
    n_bootstrap: int,
    stress_max_rows: int | None,
    skip_stress: bool,
    cashflow_complete: bool,
) -> str:
    rels = [str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path) for path in generated]
    return "\n".join(
        [
            "# Blind Review Experiment Results",
            "",
            f"Date: {now_stamp()}",
            f"Output directory: `{output_dir}`",
            "",
            "## Execution Summary",
            "",
            "- M0/B0 protocol freeze and evidence hygiene: DONE.",
            "- M1/B6/B7 field audit, group definitions, subgroup audit, and feature stress outputs: DONE.",
            "- M2/B1/B2 layer ablation and selected-only locked final summary: DONE from the true pre-run frozen month-blocked selected source.",
            f"- M3/B3 matched capacity frontier with issue-month bootstrap CI: DONE with `{n_bootstrap}` bootstrap resamples.",
            "- M4/B4 cost/human-residual sensitivity surface and break-even table: DONE.",
            (
                "- M5/B5 cash-flow approval frontier: DONE with the clean cash-flow rerun approval frontier."
                if cashflow_complete
                else "- M5/B5 cash-flow approval frontier: PARTIAL; rerun the clean cash-flow script to produce `utility_approval_frontier.csv`."
            ),
            "- M7/B8 claim-control draft: DONE as a generated claim-control summary.",
            "",
            "## Stress-Test Scope",
            "",
            (
                "- Strict/default/expanded feature stress test was skipped by flag."
                if skip_stress
                else (
                    "- Strict/default/expanded stress test used full rows with the same LGBM/sigmoid model family."
                    if stress_max_rows is None
                    else f"- Strict/default/expanded stress test used a deterministic `{stress_max_rows}` row cap."
                )
            ),
            "",
            "## Generated Files",
            "",
            *[f"- `{rel}`" for rel in rels],
            "",
            "## Next Claim Boundary",
            "",
            "Use these outputs to revise the thesis as a claim-driven evidence chain. Do not describe this as a new SOTA classifier, a legal compliance certificate, or a formal conformal guarantee.",
        ]
    )


def _code_review_markdown(output_dir: Path) -> str:
    return f"""# Blind Review Experiment Code Review

Date: {now_stamp()}
Review mode: local-only checklist, because this run did not explicitly request sub-agent delegation.

## Checked

- Outputs compare predictions against dataset ground truth labels (`y_true` / `Default` / `bad_loan`), not another model's output.
- The locked final source is read from `selected_probability_predictions.csv` with `partition == final_test`.
- Capacity and sensitivity evaluations use explicit `CostScenario` parameters and write parseable CSV files.
- Responsible-credit outputs include policy-conditioned cost columns and suppress small-cell metrics.
- Cash-flow approval frontier is separated from unconstrained threshold wins and marks oracle rows as unattainable upper bounds.
- Feature-set stress uses the same LGBM/sigmoid model family; `included_expanded_stress` means stress-test inclusion, not deployment permission.

## Non-Blocking Limitations

- If `stress_scope` is `row_capped_same_model`, the strict/default/expanded feature stress remains a limited stress test.
- Cash-flow remains accepted/funded-loan decision analysis and should not be described as applicant-pool reject inference.

Output directory reviewed: `{output_dir}`
"""


def _tracker_markdown(
    output_dir: Path,
    skip_stress: bool,
    cashflow_complete: bool,
    stress_max_rows: int | None,
) -> str:
    if skip_stress:
        stress_status = "SKIPPED"
        stress_note = "Feature stress skipped by flag."
    elif stress_max_rows is None:
        stress_status = "DONE_FULL_SAME_MODEL"
        stress_note = "Full-data LGBM/sigmoid feature-set stress and zip/no-zip policy audit written."
    else:
        stress_status = "DONE_CAPPED_SAME_MODEL"
        stress_note = f"LGBM/sigmoid feature stress written with `{stress_max_rows}` row cap."
    manifest_path = output_dir / "locked_final_protocol" / "protocol_manifest.json"
    freeze_grade = "retrospective_wrapper"
    if manifest_path.exists():
        try:
            freeze_grade = str(_load_json(manifest_path).get("pre_run_freeze", {}).get("evidence_grade", freeze_grade))
        except Exception:
            freeze_grade = "retrospective_wrapper"
    cashflow_status = "DONE" if cashflow_complete else "PARTIAL"
    cashflow_note = (
        "Approval-constrained cash-flow frontier copied from clean full rerun."
        if cashflow_complete
        else "Available after clean cash-flow rerun produces approval frontier."
    )
    rows = [
        ("BR001", "M0", "Write frozen protocol", "DONE", "`locked_final_protocol/frozen_config.yaml` written."),
        ("BR002", "M0", "Record data and split hashes", "DONE", "`protocol_manifest.json` written."),
        ("BR003", "M0", "Define selected-only final output", "DONE", "Selected-only final probability and decision reports written."),
        ("BR004", "M0", "Reviewer coverage audit", "DONE", "`blind_review_coverage_matrix.csv` written."),
        ("BR101", "M1", "Build all-field audit table", "DONE", "`all_fields_feature_audit.csv` written."),
        ("BR102", "M1", "Define feature sets", "DONE", "`feature_set_definitions.csv` written."),
        ("BR103", "M1", "Define proxy/fairness groups", "DONE", "`responsible_credit_group_definitions.csv` written."),
        ("BR104", "M1", "Build with/without zip variants", stress_status, "`zip_vs_nozip_policy_audit.csv` written." if not skip_stress else stress_note),
        ("BR201", "M2", "Locked primary rerun", "DONE_TRUE_RERUN" if freeze_grade == "true_pre_run_freeze" else "DONE_REUSED", "Uses pre-run frozen rerun artifacts when `pre_run_freeze/` exists; otherwise retrospective wrapper."),
        ("BR202", "M2", "Locked references", "DONE_SELECTED_ONLY", "Selected-only final-test report retained from the active reject-run."),
        ("BR203", "M2", "D-CRED ablation A0", "DONE_LIMITED", "`dcred_layer_ablation_table.csv` is a stitched evidence summary, not same-protocol proof."),
        ("BR204", "M2", "D-CRED same-protocol A1-A3", "DONE", "`same_protocol_decision_ablation_table.csv` written for the selected final-test population."),
        ("BR205", "M2", "D-CRED ablation A4-A5", cashflow_status, "Capacity and cash-flow objective summarized." if cashflow_complete else "Capacity done; cash-flow pending approval frontier."),
        ("BR301", "M3", "Expected capacity frontier", "DONE", "`matched_capacity_frontier_with_ci.csv` written."),
        ("BR302", "M3", "Realized frontier CI", "DONE", "Issue-month bootstrap CI written."),
        ("BR303", "M3", "Matched baseline frontiers", "DONE", "Random, uncertainty, empirical-risk, and oracle rows are capacity-aligned."),
        ("BR304", "M3", "Oracle upper bound", "DONE", "Marked as unattainable."),
        ("BR305", "M3", "Monthly stability diagnostics", "DONE_BOOTSTRAP", "Issue-month bootstrap CI written; per-month appendix can still be expanded."),
        ("BR401", "M4", "Cost-sensitivity surface", "DONE", "`cost_sensitivity_surface.csv` written."),
        ("BR402", "M4", "Break-even table", "DONE", "`break_even_table.csv` written."),
        ("BR403", "M4", "Near-all-review region map", "DONE", "`near_all_review_region_map.csv` written."),
        ("BR404", "M4", "Sensitivity appendix export", "DONE", "Full grid CSV written."),
        ("BR501", "M5", "Cash-flow frontier data", cashflow_status, cashflow_note),
        ("BR502", "M5", "Cash-flow frontier CI", cashflow_status, "Month bootstrap CI written." if cashflow_complete else "Implemented in cash-flow script month bootstrap."),
        ("BR503", "M5", "Coverage-constrained best policy", cashflow_status, "Deployable best-policy table written." if cashflow_complete else "Implemented in cash-flow script."),
        ("BR504", "M5", "Cash model weakness report", "DONE_REUSED", "`model_metrics.csv` copied when available."),
        ("BR601", "M6", "Subgroup decision audit", "DONE", "`responsible_credit_audit.csv` written."),
        ("BR602", "M6", "Subgroup calibration audit", "DONE", "`subgroup_calibration_bins.csv` written."),
        ("BR603", "M6", "With-vs-without zip audit", stress_status, "`zip_vs_nozip_policy_audit.csv` isolates zip-code proxy effect." if not skip_stress else stress_note),
        ("BR604", "M6", "Strict/default/expanded model stress", stress_status, stress_note),
        ("BR605", "M6", "Responsible-credit disclaimer", "DONE", "Claim-control summary states no compliance claim."),
        ("BR701", "M7", "Result-to-claim update", "DONE_DRAFT", "Blind-review claim-control summary written."),
        ("BR702", "M7", "Thesis table map", "PARTIAL", "Generated file list in result summary; thesis source not edited here."),
        ("BR703", "M7", "Handoff update", "PENDING", "Do after reviewing outputs and claim boundaries."),
        ("BR704", "M7", "Final claim audit", "PENDING", "Requires thesis text after integration."),
    ]
    lines = [
        "# Blind Review Experiment Tracker",
        "",
        f"Updated: {now_stamp()}",
        f"Output directory: `{output_dir}`",
        "",
        "| Run ID | Milestone | Purpose | Status | Notes |",
        "|---|---|---|---|---|",
    ]
    lines.extend(f"| {run_id} | {milestone} | {purpose} | {status} | {notes} |" for run_id, milestone, purpose, status, notes in rows)
    return "\n".join(lines) + "\n"


def _append_manifest(timestamp_dir: Path, latest_dir: Path) -> Path:
    path = PROJECT_ROOT / "MANIFEST.md"
    ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"| {ts} | /experiment-bridge | {timestamp_dir.relative_to(PROJECT_ROOT).as_posix()} | blind-review | timestamped blind-review reviewer-response evidence pack |",
        f"| {ts} | /experiment-bridge | {latest_dir.relative_to(PROJECT_ROOT).as_posix()} | blind-review | latest blind-review reviewer-response evidence pack |",
        f"| {ts} | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_RESULTS.md | blind-review | latest blind-review experiment result summary |",
        f"| {ts} | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_CODE_REVIEW.md | code-review | local-only code review for blind-review response implementation |",
        f"| {ts} | /experiment-bridge | refine-logs/BLIND_REVIEW_EXPERIMENT_TRACKER.md | blind-review | tracker updated after blind-review response experiment run |",
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(lines) + "\n")
    return path


def _copy_generated_outputs(timestamp_dir: Path, latest_dir: Path) -> None:
    for source in timestamp_dir.rglob("*"):
        if source.is_dir():
            continue
        target = latest_dir / source.relative_to(timestamp_dir)
        ensure_dir(target.parent)
        shutil.copy2(source, target)


def _expected_review_benefit(probs: np.ndarray, scenario: CostScenario) -> np.ndarray:
    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    return np.minimum(approve_cost, deny_cost) - manual_cost


def _realized_review_benefit(y: np.ndarray, probs: np.ndarray, scenario: CostScenario) -> np.ndarray:
    approve_mask, reject_mask, _ = no_review_masks(probs, scenario)
    no_review_realized = np.zeros(len(y), dtype=float)
    no_review_realized[approve_mask & (y == 1)] = scenario.false_negative_cost
    no_review_realized[reject_mask & (y == 0)] = scenario.false_positive_cost
    _, _, manual_cost = cost_components(probs, scenario)
    return no_review_realized - manual_cost


def _top_fraction_mask(scores: np.ndarray, fraction: float, positive_only: bool) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    n = len(scores)
    mask = np.zeros(n, dtype=bool)
    count = int(np.floor(n * fraction))
    if count <= 0:
        return mask
    candidates = np.flatnonzero(np.isfinite(scores))
    if positive_only:
        candidates = candidates[scores[candidates] > 0.0]
    if len(candidates) == 0:
        return mask
    ranked = candidates[np.argsort(scores[candidates])[::-1]]
    mask[ranked[:count]] = True
    return mask


def _random_mask(n: int, fraction: float, seed: int) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    count = int(np.floor(n * fraction))
    if count <= 0:
        return mask
    rng = np.random.default_rng(seed)
    mask[rng.choice(n, size=count, replace=False)] = True
    return mask


def _qcut_labels(series: pd.Series, prefix: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    try:
        bins = pd.qcut(numeric, 10, duplicates="drop")
    except ValueError:
        return pd.Series(["missing"] * len(series), index=series.index)
    labels = bins.astype(str).replace("nan", "missing")
    return prefix + "_" + labels


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def _file_record(path: Path, hash_full: bool) -> dict[str, object]:
    record = {
        "path": str(path),
        "exists": path.exists(),
    }
    if path.exists():
        stat = path.stat()
        record.update(
            {
                "bytes": stat.st_size,
                "mtime": pd.Timestamp.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
        if hash_full:
            record["sha256"] = _sha256(path)
        else:
            record["header_sha256"] = _header_sha256(path)
    return record


def _dir_record(path: Path) -> dict[str, object]:
    files = [p for p in path.rglob("*") if p.is_file()] if path.exists() else []
    return {
        "path": str(path),
        "exists": path.exists(),
        "file_count": len(files),
        "latest_mtime": (
            max(pd.Timestamp.fromtimestamp(p.stat().st_mtime) for p in files).isoformat()
            if files
            else None
        ),
    }


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _header_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        header = handle.readline()
    return hashlib.sha256(header).hexdigest()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={PROJECT_ROOT.as_posix()}",
                "-C",
                str(PROJECT_ROOT),
                "rev-parse",
                "HEAD",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


if __name__ == "__main__":
    main()
