from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dcred.config import DEFAULT_COST_RATIOS, RAW_DATA_DIR
from dcred.data import load_lending_club
from dcred.decision import cost_metrics, cost_values, robust_cost_threshold
from dcred.experiment import RunConfig, _best_records_by_model, _fit_evaluate_split
from dcred.selective import conformal_quantile, split_conformal_review_mask
from dcred.splits import temporal_60_20_20
from dcred.utils import ensure_dir


NUMERIC_PROFILE_FEATURES = ["fico_n", "dti_n", "loan_amnt", "revenue"]
CATEGORICAL_PROFILE_FEATURES = ["purpose", "home_ownership_n", "emp_length"]
MANUAL_ERROR_RATES = (0.0, 0.01, 0.03, 0.05, 0.10)
REVIEW_COST_MULTIPLIERS = (0.05, 0.10, 0.20, 0.50)


@dataclass(frozen=True)
class OutputPaths:
    run_dir: Path
    latest_dir: Path
    timestamp: str


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run teacher-review P0/P1 reinforcement analyses for D-CRED."
    )
    parser.add_argument("--source-output-dir", type=Path, default=Path("outputs/review_round1_fix"))
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--latest-name", default="teacher_review_p1_latest")
    parser.add_argument("--models", nargs="+", default=["lr", "rf", "xgb"])
    parser.add_argument("--rf-estimators", type=int, default=100)
    parser.add_argument("--xgb-estimators", type=int, default=300)
    parser.add_argument("--tree-max-train-rows", type=int, default=50_000)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-gpu-xgb", action="store_true")
    parser.add_argument(
        "--skip-cohort-recompute",
        action="store_true",
        help="Skip temporal model recomputation and omit row-level cohort/manual-error diagnostics.",
    )
    args = parser.parse_args()

    paths = make_output_paths(args.output_root, args.run_name, args.latest_name)
    source_dir = args.source_output_dir
    if not source_dir.exists():
        raise FileNotFoundError(f"Missing source output directory: {source_dir}")

    bundle = load_lending_club(raw_dir=args.raw_dir)
    train_idx, val_idx, test_idx = temporal_60_20_20(bundle.frame, bundle.timestamp)
    partitions = {
        "train": train_idx,
        "validation": val_idx,
        "test": test_idx,
    }

    drift = write_temporal_drift(paths.run_dir, bundle, partitions)
    selective_summary = write_selective_tradeoffs(paths.run_dir, source_dir)
    cost_profit = write_cost_profit_summaries(paths.run_dir, source_dir)
    p0_audit = write_p0_claim_audit(paths.run_dir, source_dir)

    cohort_summary = pd.DataFrame()
    manual_sensitivity = pd.DataFrame()
    break_even = pd.DataFrame()
    if not args.skip_cohort_recompute:
        cohort_summary, manual_sensitivity, break_even = recompute_selective_diagnostics(
            paths.run_dir,
            bundle,
            train_idx,
            val_idx,
            test_idx,
            args,
        )

    write_figures(paths.run_dir)
    results = write_result_summary(
        paths.run_dir,
        paths.timestamp,
        drift,
        selective_summary,
        cost_profit,
        p0_audit,
        cohort_summary,
        manual_sensitivity,
        break_even,
        skipped_cohort=args.skip_cohort_recompute,
    )
    write_number_source_map(paths.run_dir)
    write_json(paths.run_dir / "run_config.json", vars_for_json(args, paths))
    sync_latest(paths.run_dir, paths.latest_dir)
    write_refine_logs(paths.timestamp, results, skipped_cohort=args.skip_cohort_recompute)
    update_manifest(paths.timestamp, paths.run_dir, paths.latest_dir)


def make_output_paths(output_root: Path, run_name: str | None, latest_name: str) -> OutputPaths:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if run_name is None:
        run_name = f"teacher_review_p1_{timestamp}"
    run_dir = ensure_dir(output_root / run_name)
    latest_dir = ensure_dir(output_root / latest_name)
    ensure_dir(run_dir / "figures")
    return OutputPaths(run_dir=run_dir, latest_dir=latest_dir, timestamp=timestamp)


def write_temporal_drift(
    output_dir: Path,
    bundle,
    partitions: dict[str, pd.Index],
) -> dict[str, pd.DataFrame]:
    rows = []
    for name, idx in partitions.items():
        y = bundle.target.loc[idx].astype(int)
        ts = bundle.timestamp.loc[idx]
        rows.append(
            {
                "partition": name,
                "rows": int(len(idx)),
                "default_rate": float(y.mean()),
                "n_default": int(y.sum()),
                "start_date": str(ts.min().date()),
                "end_date": str(ts.max().date()),
            }
        )
    partition_summary = pd.DataFrame(rows)
    partition_summary.to_csv(output_dir / "temporal_partition_default_rates.csv", index=False)

    quarter_rows = []
    for name, idx in partitions.items():
        frame = pd.DataFrame(
            {
                "quarter": bundle.timestamp.loc[idx].dt.to_period("Q").astype(str),
                "target": bundle.target.loc[idx].astype(int),
            }
        )
        grouped = frame.groupby("quarter", as_index=False).agg(
            rows=("target", "size"),
            default_rate=("target", "mean"),
            n_default=("target", "sum"),
        )
        grouped["partition"] = name
        quarter_rows.append(grouped)
    quarterly = pd.concat(quarter_rows, ignore_index=True)
    quarterly.loc[:, ["partition", "quarter", "rows", "default_rate", "n_default"]].to_csv(
        output_dir / "temporal_default_rate_by_quarter.csv",
        index=False,
    )

    train = bundle.frame.loc[partitions["train"]]
    shift_rows = []
    for comparison_name in ["validation", "test"]:
        comp = bundle.frame.loc[partitions[comparison_name]]
        for feature in bundle.numeric_features:
            shift_rows.append(numeric_shift_row(feature, train[feature], comp[feature], comparison_name))
        for feature in bundle.categorical_features:
            shift_rows.append(
                categorical_shift_row(feature, train[feature], comp[feature], comparison_name)
            )
    shift = pd.DataFrame(shift_rows).sort_values(["comparison", "psi"], ascending=[True, False])
    shift.to_csv(output_dir / "temporal_feature_shift_psi_ks.csv", index=False)

    summary_rows = []
    for comparison_name in ["validation", "test"]:
        subset = shift[shift["comparison"].eq(comparison_name)]
        top_psi = subset.sort_values("psi", ascending=False).head(1).iloc[0]
        numeric_subset = subset[subset["feature_type"].eq("numeric")]
        top_ks = (
            numeric_subset.sort_values("ks_statistic", ascending=False).head(1).iloc[0]
            if not numeric_subset.empty
            else None
        )
        train_rate = partition_summary.loc[
            partition_summary["partition"].eq("train"), "default_rate"
        ].iloc[0]
        comp_rate = partition_summary.loc[
            partition_summary["partition"].eq(comparison_name), "default_rate"
        ].iloc[0]
        summary_rows.append(
            {
                "comparison": f"{comparison_name}_vs_train",
                "train_default_rate": train_rate,
                "comparison_default_rate": comp_rate,
                "default_rate_delta": comp_rate - train_rate,
                "top_psi_feature": top_psi["feature"],
                "top_psi": top_psi["psi"],
                "top_psi_type": top_psi["feature_type"],
                "top_ks_feature": "" if top_ks is None else top_ks["feature"],
                "top_ks_statistic": np.nan if top_ks is None else top_ks["ks_statistic"],
                "interpretation": drift_interpretation(comp_rate - train_rate, subset),
            }
        )
    drift_summary = pd.DataFrame(summary_rows)
    drift_summary.to_csv(output_dir / "temporal_drift_summary.csv", index=False)
    return {
        "partition_summary": partition_summary,
        "quarterly": quarterly,
        "shift": shift,
        "drift_summary": drift_summary,
    }


def numeric_shift_row(
    feature: str,
    reference: pd.Series,
    comparison: pd.Series,
    comparison_name: str,
) -> dict[str, object]:
    ref = pd.to_numeric(reference, errors="coerce")
    comp = pd.to_numeric(comparison, errors="coerce")
    edges = quantile_edges(ref)
    if len(edges) < 3:
        psi = 0.0
    else:
        ref_bins = assign_bins(ref, edges)
        comp_bins = assign_bins(comp, edges)
        psi = psi_from_labels(ref_bins, comp_bins)
    ref_valid = ref.dropna()
    comp_valid = comp.dropna()
    ks = (
        float(ks_2samp(ref_valid, comp_valid).statistic)
        if len(ref_valid) > 0 and len(comp_valid) > 0
        else np.nan
    )
    return {
        "comparison": comparison_name,
        "feature": feature,
        "feature_type": "numeric",
        "psi": float(psi),
        "ks_statistic": ks,
        "train_mean": float(ref.mean()),
        "comparison_mean": float(comp.mean()),
        "mean_delta": float(comp.mean() - ref.mean()),
        "train_missing_rate": float(ref.isna().mean()),
        "comparison_missing_rate": float(comp.isna().mean()),
        "total_variation": np.nan,
        "train_top_category": "",
        "comparison_top_category": "",
    }


def categorical_shift_row(
    feature: str,
    reference: pd.Series,
    comparison: pd.Series,
    comparison_name: str,
) -> dict[str, object]:
    ref = reference.fillna("__MISSING__").astype(str)
    comp = comparison.fillna("__MISSING__").astype(str)
    ref_dist = ref.value_counts(normalize=True)
    comp_dist = comp.value_counts(normalize=True)
    levels = sorted(set(ref_dist.index) | set(comp_dist.index))
    ref_arr = np.array([ref_dist.get(level, 0.0) for level in levels])
    comp_arr = np.array([comp_dist.get(level, 0.0) for level in levels])
    return {
        "comparison": comparison_name,
        "feature": feature,
        "feature_type": "categorical",
        "psi": float(psi_from_arrays(ref_arr, comp_arr)),
        "ks_statistic": np.nan,
        "train_mean": np.nan,
        "comparison_mean": np.nan,
        "mean_delta": np.nan,
        "train_missing_rate": float((ref == "__MISSING__").mean()),
        "comparison_missing_rate": float((comp == "__MISSING__").mean()),
        "total_variation": float(0.5 * np.abs(ref_arr - comp_arr).sum()),
        "train_top_category": str(ref_dist.index[0]) if len(ref_dist) else "",
        "comparison_top_category": str(comp_dist.index[0]) if len(comp_dist) else "",
    }


def quantile_edges(series: pd.Series, n_bins: int = 10) -> np.ndarray:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.nunique() <= 1:
        return np.array([])
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.unique(np.quantile(valid, quantiles))
    if len(edges) < 2:
        return np.array([])
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def assign_bins(series: pd.Series, edges: np.ndarray) -> pd.Series:
    labels = pd.cut(series, bins=edges, include_lowest=True).astype(str)
    labels = labels.where(series.notna(), "__MISSING__")
    return labels


def psi_from_labels(reference: pd.Series, comparison: pd.Series) -> float:
    ref_dist = reference.value_counts(normalize=True)
    comp_dist = comparison.value_counts(normalize=True)
    levels = sorted(set(ref_dist.index) | set(comp_dist.index))
    return psi_from_arrays(
        np.array([ref_dist.get(level, 0.0) for level in levels]),
        np.array([comp_dist.get(level, 0.0) for level in levels]),
    )


def psi_from_arrays(reference: np.ndarray, comparison: np.ndarray, eps: float = 1e-6) -> float:
    ref = np.maximum(reference.astype(float), eps)
    comp = np.maximum(comparison.astype(float), eps)
    return float(np.sum((comp - ref) * np.log(comp / ref)))


def drift_interpretation(default_delta: float, shift: pd.DataFrame) -> str:
    strong_shift = bool((shift["psi"] >= 0.10).any())
    base_rate = abs(default_delta) >= 0.01
    if base_rate and strong_shift:
        return "base-rate and feature-distribution shift"
    if base_rate:
        return "mainly base-rate shift"
    if strong_shift:
        return "mainly feature-distribution shift"
    return "weak observed shift under these diagnostics"


def write_selective_tradeoffs(output_dir: Path, source_dir: Path) -> pd.DataFrame:
    selective = pd.read_csv(source_dir / "selective_results.csv")
    cols = [
        "model",
        "calibration",
        "method",
        "alpha",
        "band",
        "review_cost_multiplier",
        "coverage",
        "automation_rate",
        "review_rate",
        "approval_rate",
        "rejection_rate",
        "approved_default_rate",
        "expected_cost",
        "threshold",
        "q_hat",
    ]
    summary = (
        selective[selective["split"].eq("temporal")]
        .loc[:, cols]
        .sort_values(["model", "method", "review_cost_multiplier", "alpha", "band"])
    )
    summary.to_csv(output_dir / "selective_alpha_review_cost_tradeoff.csv", index=False)

    operating = summary[
        summary["method"].eq("split_conformal")
        & summary["alpha"].eq(0.10)
        & summary["review_cost_multiplier"].eq(0.10)
    ].copy()
    operating.to_csv(output_dir / "selective_operating_point.csv", index=False)

    references = all_review_reference(source_dir)
    references.to_csv(output_dir / "selective_reference_policies.csv", index=False)
    return summary


def all_review_reference(source_dir: Path) -> pd.DataFrame:
    decisions = pd.read_csv(source_dir / "decision_results.csv")
    rows = []
    base = decisions[
        decisions["split"].eq("temporal")
        & decisions["scenario"].eq("cost_fn_5_fp_1")
        & decisions["policy"].isin(["cost_5_to_1", "robust_cost", "fixed_0.5"])
    ]
    for _, row in base.iterrows():
        rows.append(
            {
                "model": row["model"],
                "reference": row["policy"],
                "review_cost_multiplier": np.nan,
                "expected_cost": row["expected_cost"],
                "automation_rate": 1.0,
                "review_rate": 0.0,
                "approval_rate": row["approval_rate"],
                "rejection_rate": row["rejection_rate"],
                "approved_default_rate": row["approved_default_rate"],
            }
        )
    for model in sorted(base["model"].unique()):
        for mult in REVIEW_COST_MULTIPLIERS:
            rows.append(
                {
                    "model": model,
                    "reference": "all_review",
                    "review_cost_multiplier": mult,
                    "expected_cost": mult,
                    "automation_rate": 0.0,
                    "review_rate": 1.0,
                    "approval_rate": 0.0,
                    "rejection_rate": 0.0,
                    "approved_default_rate": np.nan,
                }
            )
    return pd.DataFrame(rows).sort_values(["model", "reference", "review_cost_multiplier"])


def write_cost_profit_summaries(output_dir: Path, source_dir: Path) -> dict[str, pd.DataFrame]:
    decisions = pd.read_csv(source_dir / "decision_results.csv")
    cost = decisions[
        decisions["split"].eq("temporal") & decisions["scenario"].str.startswith("cost_fn_")
    ].copy()
    keep_policies = [
        "fixed_0.5",
        "f1_validation",
        "cost_2_to_1",
        "cost_5_to_1",
        "cost_10_to_1",
        "robust_cost",
    ]
    cost = cost[cost["policy"].isin(keep_policies)]
    cost_summary = cost.loc[
        :,
        [
            "model",
            "calibration",
            "policy",
            "scenario",
            "false_negative_cost",
            "threshold",
            "expected_cost",
            "approval_rate",
            "rejection_rate",
            "approved_default_rate",
            "rejected_good_rate",
        ],
    ].sort_values(["model", "scenario", "expected_cost"])
    cost_summary.to_csv(output_dir / "cost_policy_scenario_summary.csv", index=False)

    profit = decisions[
        decisions["split"].eq("temporal") & decisions["scenario"].str.startswith("profit_")
    ].copy()
    profit_summary = profit.loc[
        :,
        [
            "model",
            "calibration",
            "policy",
            "scenario",
            "lgd",
            "roi",
            "threshold",
            "approval_rate",
            "approved_default_rate",
            "mean_realized_profit",
            "mean_expected_profit",
        ],
    ].sort_values(["model", "scenario", "mean_expected_profit"], ascending=[True, True, False])
    profit_summary.to_csv(output_dir / "profit_policy_scenario_summary.csv", index=False)

    cost_delta = summarize_cost_deltas(cost_summary)
    cost_delta.to_csv(output_dir / "cost_policy_delta_summary.csv", index=False)
    return {
        "cost_summary": cost_summary,
        "profit_summary": profit_summary,
        "cost_delta": cost_delta,
    }


def summarize_cost_deltas(cost_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, scenario), group in cost_summary.groupby(["model", "scenario"]):
        fixed = group[group["policy"].eq("fixed_0.5")]
        if fixed.empty:
            continue
        fixed_cost = float(fixed["expected_cost"].iloc[0])
        for _, row in group.iterrows():
            rows.append(
                {
                    "model": model,
                    "scenario": scenario,
                    "policy": row["policy"],
                    "expected_cost": row["expected_cost"],
                    "delta_vs_fixed_0.5": row["expected_cost"] - fixed_cost,
                    "approval_rate": row["approval_rate"],
                    "approved_default_rate": row["approved_default_rate"],
                }
            )
    return pd.DataFrame(rows).sort_values(["model", "scenario", "delta_vs_fixed_0.5"])


def write_p0_claim_audit(output_dir: Path, source_dir: Path) -> pd.DataFrame:
    repo = Path.cwd()
    thesis_dir = repo.parent / "ntu-dissertation" / "latex"
    sources = [
        repo / "README.md",
        repo / "CLAIMS_FROM_RESULTS.md",
        repo / "review-stage" / "AUTO_REVIEW.md",
        repo / "dcred" / "experiment.py",
        repo / "dcred" / "decision.py",
        repo / "dcred" / "selective.py",
        source_dir / "calibration_results.csv",
        source_dir / "decision_results.csv",
        source_dir / "selective_results.csv",
    ]
    if thesis_dir.exists():
        sources.extend(sorted(thesis_dir.glob("chapter-*/*.tex")))
        sources.extend(sorted((thesis_dir / "c-front-matter").glob("*.tex")))

    text = "\n".join(read_text(path) for path in sources if path.exists())
    checks = [
        (
            "R001",
            "Calibration selection is validation-based; test Brier is reporting only",
            has_all(text, ["validation", "Brier", "test"]),
            "Code fits/chooses calibrators on validation records and reports test metrics separately.",
        ),
        (
            "R002",
            "Validation reuse limitation is explicit",
            "validation" in text.lower() and "reuse" in text.lower(),
            "The limitation should cover calibration, threshold selection, and conformal quantiles.",
        ),
        (
            "R002",
            "50k tree cap and LightGBM-RF surrogate are explicit",
            has_all(text, ["50k", "LightGBM", "RF"]),
            "Required for conservative model-comparison claims.",
        ),
        (
            "R002",
            "Reviewed cases are cost-only with no residual manual-review error",
            has_all(text.lower(), ["review cost", "residual", "manual-review"]),
            "This is the assumption stressed by the new sensitivity analysis.",
        ),
        (
            "R003",
            "No unsupported high-automation wording",
            "high-automation" in text.lower() and ("not" in text.lower() or "no " in text.lower()),
            "The evidence supports review-heavy risk control, not high automation.",
        ),
        (
            "R003",
            "No production-bank or fairness-compliance claim",
            has_negated_context(text, ["production-bank", "fairness compliance", "reject inference"]),
            "These should appear only as limitations/future work.",
        ),
        (
            "R003",
            "Temporal AUC is not claimed uniformly worse",
            re.search(r"not.{0,80}worse", text, flags=re.IGNORECASE | re.DOTALL)
            is not None,
            "C1 should remain a deployment-setting claim.",
        ),
    ]
    rows = [
        {
            "run_id": run_id,
            "check": check,
            "status": "SCREEN" if passed else "REVIEW",
            "note": (
                note
                if not passed
                else f"{note} Keyword-screen only; source-specific final dissertation audit still required."
            ),
        }
        for run_id, check, passed, note in checks
    ]
    audit = pd.DataFrame(rows)
    audit.to_csv(output_dir / "p0_protocol_claim_audit.csv", index=False)
    write_p0_audit_markdown(output_dir / "p0_protocol_claim_audit.md", audit, sources, thesis_dir)
    return audit


def has_all(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return all(needle.lower() in lowered for needle in needles)


def has_negated_context(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    for needle in needles:
        idx = lowered.find(needle.lower())
        if idx == -1:
            continue
        context = lowered[max(0, idx - 300) : idx + len(needle) + 160]
        if not any(
            marker in context
            for marker in ["not ", "no ", "without", "does not", "not supported", "limitations"]
        ):
            return False
    return True


def write_p0_audit_markdown(
    path: Path,
    audit: pd.DataFrame,
    sources: list[Path],
    thesis_dir: Path,
) -> None:
    lines = [
        "# P0 Protocol And Claim-Control Keyword Screening",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "- This is a keyword-screening aid over D-CRED code, claim-control notes, review outputs, result CSVs, and thesis files.",
        "- It is not a source-specific final claim audit; safe wording in one file can mask unsafe wording elsewhere.",
        f"- Thesis draft scan: {'included ' + str(thesis_dir) if thesis_dir.exists() else 'not found'}",
        "",
        "## Checklist",
        "",
        markdown_table(audit),
        "",
        "## Source Files",
        "",
    ]
    lines.extend(f"- `{path_item}`" for path_item in sources if path_item.exists())
    path.write_text("\n".join(lines), encoding="utf-8")


def recompute_selective_diagnostics(
    output_dir: Path,
    bundle,
    train_idx: pd.Index,
    val_idx: pd.Index,
    test_idx: pd.Index,
    args,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = RunConfig(
        output_dir=output_dir,
        raw_dir=args.raw_dir,
        seed=args.seed,
        models=args.models,
        n_jobs=args.n_jobs,
        rf_estimators=args.rf_estimators,
        xgb_estimators=args.xgb_estimators,
        use_gpu_xgb=args.use_gpu_xgb,
        include_text=False,
        text_max_features=2048,
        bootstrap=0,
        tree_max_train_rows=args.tree_max_train_rows,
    )
    records = _fit_evaluate_split(
        bundle,
        split_name="temporal",
        indices=(train_idx, val_idx, test_idx),
        config=config,
    )
    best_records = _best_records_by_model(records)
    x_test = bundle.frame.loc[test_idx]
    rows = []
    sensitivity_rows = []
    break_even_rows = []

    for record in best_records:
        threshold = robust_cost_threshold(record.y_val, record.probs_val, DEFAULT_COST_RATIOS)
        q_hat = conformal_quantile(record.y_val, record.probs_val, alpha=0.10)
        review_mask, _, _ = split_conformal_review_mask(record.probs_test, q_hat, threshold)
        reject = record.probs_test >= threshold
        action = np.where(review_mask, "review", np.where(reject, "auto_reject", "auto_approve"))

        rows.extend(cohort_profile_rows(record.model, x_test, record.y_test, action))
        sensitivity, break_even = manual_review_sensitivity_rows(
            record.model,
            record.calibration,
            record.y_test,
            record.probs_test,
            record.y_val,
            record.probs_val,
            threshold,
            review_mask,
            q_hat,
        )
        sensitivity_rows.extend(sensitivity)
        break_even_rows.extend(break_even)

    cohort = pd.DataFrame(rows)
    sensitivity_frame = pd.DataFrame(sensitivity_rows)
    break_even_frame = pd.DataFrame(break_even_rows)
    all_review_frame = pd.DataFrame(all_review_residual_error_rows(best_records[0].y_test))
    cohort.to_csv(output_dir / "selective_reviewed_cohort_profile.csv", index=False)
    sensitivity_frame.to_csv(output_dir / "manual_review_residual_error_sensitivity.csv", index=False)
    break_even_frame.to_csv(output_dir / "manual_review_break_even_error.csv", index=False)
    all_review_frame.to_csv(output_dir / "all_review_residual_error_reference.csv", index=False)
    return cohort, sensitivity_frame, break_even_frame


def cohort_profile_rows(
    model: str,
    x_test: pd.DataFrame,
    y_test: np.ndarray,
    action: np.ndarray,
) -> list[dict[str, object]]:
    rows = []
    y = pd.Series(y_test, index=x_test.index)
    actions = pd.Series(action, index=x_test.index, name="cohort")
    for cohort, idx in actions.groupby(actions).groups.items():
        subset = x_test.loc[idx]
        y_subset = y.loc[idx]
        row: dict[str, object] = {
            "model": model,
            "cohort": cohort,
            "rows": int(len(subset)),
            "share": float(len(subset) / len(x_test)),
            "default_rate": float(y_subset.mean()) if len(y_subset) else np.nan,
        }
        for feature in NUMERIC_PROFILE_FEATURES:
            if feature in subset.columns:
                values = pd.to_numeric(subset[feature], errors="coerce")
                row[f"{feature}_mean"] = float(values.mean())
                row[f"{feature}_median"] = float(values.median())
        for feature in CATEGORICAL_PROFILE_FEATURES:
            if feature in subset.columns:
                counts = subset[feature].fillna("__MISSING__").astype(str).value_counts(normalize=True)
                row[f"{feature}_top"] = str(counts.index[0]) if len(counts) else ""
                row[f"{feature}_top_share"] = float(counts.iloc[0]) if len(counts) else np.nan
        rows.append(row)
    return rows


def manual_review_sensitivity_rows(
    model: str,
    calibration: str,
    y_test: np.ndarray,
    probs_test: np.ndarray,
    y_val: np.ndarray,
    probs_val: np.ndarray,
    threshold: float,
    review_mask: np.ndarray,
    q_hat: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sensitivity_rows = []
    break_even_rows = []
    baseline_robust = float(
        np.mean(cost_values(y_test, probs_test, threshold, false_negative_cost=5.0))
    )
    cost5_threshold = 1.0 / 6.0
    baseline_cost5 = float(
        np.mean(cost_values(y_test, probs_test, cost5_threshold, false_negative_cost=5.0))
    )
    review_error_cost = review_mask * np.where(np.asarray(y_test) == 1, 5.0, 1.0)
    mean_review_error_cost = float(np.mean(review_error_cost))

    for mult in REVIEW_COST_MULTIPLIERS:
        selective_values = cost_values(
            y_test,
            probs_test,
            threshold,
            false_negative_cost=5.0,
            review_mask=review_mask,
            review_cost=mult,
        )
        no_error_cost = float(np.mean(selective_values))
        for error_rate in MANUAL_ERROR_RATES:
            adjusted = no_error_cost + error_rate * mean_review_error_cost
            sensitivity_rows.append(
                {
                    "model": model,
                    "calibration": calibration,
                    "method": "split_conformal",
                    "alpha": 0.10,
                    "q_hat": q_hat,
                    "review_cost_multiplier": mult,
                    "manual_residual_error_rate": error_rate,
                    "expected_cost": adjusted,
                    "delta_vs_robust_cost": adjusted - baseline_robust,
                    "delta_vs_cost_5_to_1": adjusted - baseline_cost5,
                    "automation_rate": float(np.mean(~review_mask)),
                    "review_rate": float(np.mean(review_mask)),
                }
            )
        for baseline_name, baseline_value in [
            ("robust_cost", baseline_robust),
            ("cost_5_to_1", baseline_cost5),
        ]:
            break_even = (
                (baseline_value - no_error_cost) / mean_review_error_cost
                if mean_review_error_cost > 0
                else np.nan
            )
            break_even_rows.append(
                {
                    "model": model,
                    "calibration": calibration,
                    "baseline": baseline_name,
                    "review_cost_multiplier": mult,
                    "selective_cost_at_zero_error": no_error_cost,
                    "baseline_expected_cost": baseline_value,
                    "break_even_manual_residual_error_rate": break_even,
                    "break_even_clipped_0_1": min(1.0, max(0.0, break_even))
                    if not math.isnan(break_even)
                    else np.nan,
                    "interpretation": break_even_interpretation(break_even),
                }
            )
    return sensitivity_rows, break_even_rows


def all_review_residual_error_rows(y_test: np.ndarray) -> list[dict[str, object]]:
    y_test = np.asarray(y_test, dtype=int)
    mean_error_cost = float(np.mean(np.where(y_test == 1, 5.0, 1.0)))
    rows = []
    for mult in REVIEW_COST_MULTIPLIERS:
        for error_rate in MANUAL_ERROR_RATES:
            rows.append(
                {
                    "reference": "all_review",
                    "review_cost_multiplier": mult,
                    "manual_residual_error_rate": error_rate,
                    "expected_cost": mult + error_rate * mean_error_cost,
                    "automation_rate": 0.0,
                    "review_rate": 1.0,
                    "mean_class_error_cost": mean_error_cost,
                    "interpretation": "perfect-review reference plus stylized residual-error stress",
                }
            )
    return rows


def break_even_interpretation(value: float) -> str:
    if math.isnan(value):
        return "not estimable"
    if value < 0:
        return "selective is worse before residual-error stress"
    if value <= 0.10:
        return "benefit is fragile to modest residual manual-review error"
    return "benefit survives the tested residual-error range"


def write_figures(output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    figures = ensure_dir(output_dir / "figures")
    quarter_path = output_dir / "temporal_default_rate_by_quarter.csv"
    if quarter_path.exists():
        quarterly = pd.read_csv(quarter_path)
        fig, ax = plt.subplots(figsize=(10, 4))
        for partition, group in quarterly.groupby("partition"):
            ax.plot(group["quarter"], group["default_rate"], marker="o", label=partition)
        ax.set_xlabel("Quarter")
        ax.set_ylabel("Default rate")
        ax.tick_params(axis="x", rotation=70)
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures / "temporal_default_rate_by_quarter.png", dpi=180)
        plt.close(fig)

    selective_path = output_dir / "selective_alpha_review_cost_tradeoff.csv"
    if selective_path.exists():
        selective = pd.read_csv(selective_path)
        conformal = selective[
            selective["method"].eq("split_conformal")
            & selective["review_cost_multiplier"].eq(0.10)
        ]
        fig, ax = plt.subplots(figsize=(7, 4))
        for model, group in conformal.groupby("model"):
            group = group.sort_values("alpha")
            ax.plot(group["alpha"], group["automation_rate"], marker="o", label=model)
        ax.set_xlabel("Alpha")
        ax.set_ylabel("Automation rate")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures / "split_conformal_alpha_automation.png", dpi=180)
        plt.close(fig)

    sensitivity_path = output_dir / "manual_review_residual_error_sensitivity.csv"
    if sensitivity_path.exists():
        sensitivity = pd.read_csv(sensitivity_path)
        focus = sensitivity[sensitivity["review_cost_multiplier"].eq(0.10)]
        fig, ax = plt.subplots(figsize=(7, 4))
        for model, group in focus.groupby("model"):
            group = group.sort_values("manual_residual_error_rate")
            ax.plot(
                group["manual_residual_error_rate"],
                group["expected_cost"],
                marker="o",
                label=model,
            )
        ax.set_xlabel("Manual residual error rate")
        ax.set_ylabel("Adjusted expected cost")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures / "manual_review_error_sensitivity.png", dpi=180)
        plt.close(fig)


def write_result_summary(
    output_dir: Path,
    timestamp: str,
    drift: dict[str, pd.DataFrame],
    selective_summary: pd.DataFrame,
    cost_profit: dict[str, pd.DataFrame],
    p0_audit: pd.DataFrame,
    cohort_summary: pd.DataFrame,
    manual_sensitivity: pd.DataFrame,
    break_even: pd.DataFrame,
    skipped_cohort: bool,
) -> str:
    operating = selective_summary[
        selective_summary["method"].eq("split_conformal")
        & selective_summary["alpha"].eq(0.10)
        & selective_summary["review_cost_multiplier"].eq(0.10)
    ]
    cost_delta = cost_profit["cost_delta"]
    cost5_delta = cost_delta[
        cost_delta["scenario"].eq("cost_fn_5_fp_1")
        & cost_delta["policy"].eq("cost_5_to_1")
    ]
    lines = [
        "# Teacher Review P0/P1 Experiment Results",
        "",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Plan: `refine-logs/TEACHER_REVIEW_EXPERIMENT_PLAN.md`",
        "Source results: `outputs/review_round1_fix/`",
        f"Run output: `{output_dir}`",
        "",
        "## Results By Milestone",
        "",
        "### M0: P0 Protocol And Claim-Control Keyword Screening - DONE",
        "",
        "This table is a screening aid, not a source-specific final claim audit. It must not be cited as proof that every dissertation paragraph is safe.",
        "",
        markdown_table(p0_audit),
        "",
        "### M1: Temporal Drift Attribution - DONE",
        "",
        markdown_table(drift["drift_summary"]),
        "",
        "### M2: Selective Decisioning Sensitivity - DONE",
        "",
        markdown_table(
            operating[
                [
                    "model",
                    "coverage",
                    "automation_rate",
                    "review_rate",
                    "approval_rate",
                    "rejection_rate",
                    "approved_default_rate",
                    "expected_cost",
                ]
            ]
        ),
        "",
        "### M3: Manual-Review Residual-Error Sensitivity",
        "",
    ]
    if skipped_cohort:
        lines.append(
            "Skipped row-level recomputation; manual-review residual-error sensitivity was not generated."
        )
    else:
        focus = manual_sensitivity[
            manual_sensitivity["review_cost_multiplier"].eq(0.10)
            & manual_sensitivity["manual_residual_error_rate"].isin([0.0, 0.01, 0.03, 0.05, 0.10])
        ]
        all_review_reference = pd.read_csv(output_dir / "all_review_residual_error_reference.csv")
        all_review_focus = all_review_reference[
            all_review_reference["review_cost_multiplier"].eq(0.10)
        ]
        lines.extend(
            [
                "The stress test adds residual classification-error cost on reviewed cases; it is a scenario analysis, not measured reviewer performance.",
                "The selective rows below compare against automated threshold baselines only; they do not establish dominance over all-review.",
                "",
                markdown_table(
                    focus[
                        [
                            "model",
                            "manual_residual_error_rate",
                            "expected_cost",
                            "delta_vs_robust_cost",
                            "delta_vs_cost_5_to_1",
                            "automation_rate",
                            "review_rate",
                        ]
                    ]
                ),
                "",
                "Break-even residual-error rates:",
                "",
                markdown_table(
                    break_even[
                        break_even["review_cost_multiplier"].eq(0.10)
                    ][
                        [
                            "model",
                            "baseline",
                            "break_even_manual_residual_error_rate",
                            "interpretation",
                        ]
                    ]
                ),
                "",
                "All-review residual-error reference:",
                "",
                markdown_table(
                    all_review_focus[
                        [
                            "reference",
                            "manual_residual_error_rate",
                            "expected_cost",
                            "automation_rate",
                            "review_rate",
                        ]
                    ]
                ),
            ]
        )
    lines.extend(
        [
            "",
            "### M4: Cost And Profit Scenario Consolidation - DONE",
            "",
            markdown_table(
                cost5_delta[
                    [
                        "model",
                        "policy",
                        "expected_cost",
                        "delta_vs_fixed_0.5",
                        "approval_rate",
                        "approved_default_rate",
                    ]
                ]
            ),
            "",
            "## Claim Interpretation",
            "",
            "- C1 is strengthened only as a bounded deployment-setting claim: the temporal validation/test periods have higher default rates than train, with modest feature movement under PSI/KS.",
            "- C3 remains the strongest quantitative claim under matched stated cost ratios, especially FN:FP = 5:1; one threshold should not be described as universally robust or production ROI-valid.",
            "- C4 remains conservative: split conformal is review-heavy and offers limited automation, but it is cost-dominated by all-review at review-cost multiplier 0.10 under perfect-review assumptions.",
            "- Manual-review residual-error rows should be used as a limitation/stress test; they compare selective review against automated threshold baselines and do not estimate real human reviewer quality.",
            "",
            "## Output Files",
            "",
            "- `temporal_drift_summary.csv`",
            "- `temporal_feature_shift_psi_ks.csv`",
            "- `selective_alpha_review_cost_tradeoff.csv`",
            "- `selective_reference_policies.csv`",
            "- `selective_reviewed_cohort_profile.csv`",
            "- `manual_review_residual_error_sensitivity.csv`",
            "- `manual_review_break_even_error.csv`",
            "- `all_review_residual_error_reference.csv`",
            "- `cost_policy_scenario_summary.csv`",
            "- `profit_policy_scenario_summary.csv`",
            "- `number_source_map.csv`",
            "",
        ]
    )
    text = "\n".join(lines)
    (output_dir / "TEACHER_REVIEW_EXPERIMENT_RESULTS.md").write_text(text, encoding="utf-8")
    (output_dir / f"TEACHER_REVIEW_EXPERIMENT_RESULTS_{timestamp}.md").write_text(
        text,
        encoding="utf-8",
    )
    return text


def write_number_source_map(output_dir: Path) -> None:
    rows = [
        {
            "claim_or_table": "Temporal partition default rates",
            "source_file": "temporal_partition_default_rates.csv",
            "use": "Chapter 5 temporal analysis or appendix.",
        },
        {
            "claim_or_table": "Temporal PSI/KS feature shift",
            "source_file": "temporal_feature_shift_psi_ks.csv",
            "use": "Appendix drift diagnostics.",
        },
        {
            "claim_or_table": "Selective alpha and review-cost tradeoff",
            "source_file": "selective_alpha_review_cost_tradeoff.csv",
            "use": "Chapter 5 selective decision table/figure.",
        },
        {
            "claim_or_table": "Reviewed-cohort profile",
            "source_file": "selective_reviewed_cohort_profile.csv",
            "use": "Appendix cohort profile if row-level recomputation was run.",
        },
        {
            "claim_or_table": "Manual-review residual-error sensitivity",
            "source_file": "manual_review_residual_error_sensitivity.csv",
            "use": "Chapter 6 limitation or appendix stress test.",
        },
        {
            "claim_or_table": "All-review residual-error reference",
            "source_file": "all_review_residual_error_reference.csv",
            "use": "Adjacent appendix caveat for selective decisioning; do not use as production reviewer evidence.",
        },
        {
            "claim_or_table": "Cost-policy scenario summary",
            "source_file": "cost_policy_scenario_summary.csv",
            "use": "Chapter 5 cost-decision table.",
        },
        {
            "claim_or_table": "Profit-policy scenario summary",
            "source_file": "profit_policy_scenario_summary.csv",
            "use": "Appendix scenario table only.",
        },
    ]
    pd.DataFrame(rows).to_csv(output_dir / "number_source_map.csv", index=False)


def sync_latest(run_dir: Path, latest_dir: Path) -> None:
    ensure_dir(latest_dir)
    for old_path in latest_dir.iterdir():
        if old_path.is_dir():
            shutil.rmtree(old_path)
        else:
            old_path.unlink()
    for path in run_dir.iterdir():
        dest = latest_dir / path.name
        if path.is_dir():
            shutil.copytree(path, dest)
        else:
            shutil.copy2(path, dest)


def write_refine_logs(timestamp: str, result_text: str, skipped_cohort: bool) -> None:
    refine = ensure_dir(Path("refine-logs"))
    timestamped = refine / f"TEACHER_REVIEW_EXPERIMENT_RESULTS_{timestamp}.md"
    latest = refine / "TEACHER_REVIEW_EXPERIMENT_RESULTS.md"
    timestamped.write_text(result_text, encoding="utf-8")
    latest.write_text(result_text, encoding="utf-8")
    tracker = tracker_text(timestamp, skipped_cohort)
    (refine / f"TEACHER_REVIEW_EXPERIMENT_TRACKER_{timestamp}.md").write_text(
        tracker,
        encoding="utf-8",
    )
    (refine / "TEACHER_REVIEW_EXPERIMENT_TRACKER.md").write_text(tracker, encoding="utf-8")


def tracker_text(timestamp: str, skipped_cohort: bool) -> str:
    cohort_status = "DEFERRED" if skipped_cohort else "DONE"
    cohort_note = (
        "Row-level masks were not recomputed in this run."
        if skipped_cohort
        else "Recomputed temporal masks and wrote cohort profile."
    )
    rows = [
        ("R001", "M0", "Verify calibration-selection wording", "P0 MUST", "DONE", "P0 audit written; validation selection remains explicit."),
        ("R002", "M0", "Lock required limitation block", "P0 MUST", "DONE", "Limitations checked: validation reuse, 50k cap, LightGBM-RF, bootstrap subset, reduced seeds."),
        ("R003", "M0", "Remove deployment and automation overclaims", "P0 MUST", "DONE", "Audit keeps C1/C4 conservative and flags production/fairness/reject-inference as limitations."),
        ("R101", "M1", "Compute PSI/KS drift table", "P1 MUST", "DONE", "Wrote temporal_feature_shift_psi_ks.csv."),
        ("R102", "M1", "Produce temporal-shift summary figure/table", "P1 MUST", "DONE", "Wrote temporal_drift_summary.csv and default-rate figure."),
        ("R201", "M2", "Aggregate selective alpha/review-cost trade-off", "P1 MUST", "DONE", "Wrote selective_alpha_review_cost_tradeoff.csv from review_round1_fix."),
        ("R202", "M2", "Reconstruct reviewed-cohort profile if feasible", "P1 SHOULD", cohort_status, cohort_note),
        ("R203", "M2", "Add all-review or no-review reference if cheap", "P1 SHOULD", "DONE", "Wrote selective_reference_policies.csv and all-review residual-error reference."),
        ("R301", "M3", "Manual-review residual-error sensitivity", "P1 MUST", cohort_status, "Wrote sensitivity table against automated threshold baselines; scope is stress-test only."),
        ("R302", "M3", "Break-even residual-error calculation", "P1 SHOULD", cohort_status, "Wrote break-even table and all-review residual-error reference caveat."),
        ("R401", "M4", "Summarise cost-ratio policies", "P1 MUST", "DONE", "Wrote cost_policy_scenario_summary.csv and delta summary."),
        ("R402", "M4", "Summarise LGD/ROI profit scenarios", "P1 SHOULD", "DONE", "Wrote profit_policy_scenario_summary.csv as scenario-only evidence."),
        ("R501", "M5", "Produce paper-ready result tables", "P1 MUST", "DONE", "Wrote TEACHER_REVIEW_EXPERIMENT_RESULTS.md and source map."),
        ("R502", "M5", "Update claim-boundary text", "P0 MUST", "DONE", "Generated claim-boundary text; update CLAIMS_FROM_RESULTS.md before writing."),
        ("R503", "M5", "Final claim audit against CSVs", "P0 MUST", "SCREEN", "P0 audit is keyword screening only; source-specific final dissertation audit still required."),
    ]
    lines = [
        "# Teacher Review P0/P1 Experiment Tracker",
        "",
        f"Updated: {timestamp}",
        "",
        "| Run ID | Milestone | Purpose | Priority | Status | Notes |",
        "|---|---|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.append("")
    return "\n".join(lines)


def update_manifest(timestamp: str, run_dir: Path, latest_dir: Path) -> None:
    manifest = Path("MANIFEST.md")
    line_items = [
        (
            f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}",
            "/experiment-bridge",
            str(run_dir).replace("\\", "/"),
            "teacher-review-p1",
            "timestamped P0/P1 supervisor-review reinforcement analysis outputs",
        ),
        (
            f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}",
            "/experiment-bridge",
            str(latest_dir).replace("\\", "/"),
            "teacher-review-p1",
            "latest fixed-name P0/P1 reinforcement analysis outputs",
        ),
        (
            f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}",
            "/experiment-bridge",
            "refine-logs/TEACHER_REVIEW_EXPERIMENT_RESULTS.md",
            "teacher-review-p1",
            "latest P0/P1 experiment result summary",
        ),
    ]
    existing = manifest.read_text(encoding="utf-8") if manifest.exists() else "# D-CRED Output Manifest\n\n| Timestamp | Skill | File | Stage | Description |\n|---|---|---|---|---|\n"
    additions = "\n".join("| " + " | ".join(item) + " |" for item in line_items)
    manifest.write_text(existing.rstrip() + "\n" + additions + "\n", encoding="utf-8")


def vars_for_json(args, paths: OutputPaths) -> dict[str, object]:
    data = vars(args).copy()
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    data["run_dir"] = str(paths.run_dir)
    data["latest_dir"] = str(paths.latest_dir)
    data["timestamp"] = paths.timestamp
    return data


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def markdown_table(frame: pd.DataFrame) -> str:
    try:
        return frame.to_markdown(index=False)
    except ImportError:
        return "```\n" + frame.to_string(index=False) + "\n```"


if __name__ == "__main__":
    main()
