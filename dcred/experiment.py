from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import gc

import numpy as np
import pandas as pd

from .calibration import fit_calibrators
from .config import DEFAULT_ALPHAS, DEFAULT_COST_RATIOS, DEFAULT_LGDS, DEFAULT_ROIS
from .data import (
    DatasetBundle,
    dataset_summary,
    load_german_credit,
    load_lending_club,
    load_uci_default,
    summarize_splits,
)
from .decision import cost_metrics, cost_threshold, cost_values, decision_table, robust_cost_threshold
from .metrics import (
    bootstrap_ci,
    classification_metrics,
    metrics_row,
    paired_bootstrap_delta_ci,
)
from .modeling import (
    build_models,
    build_preprocessor,
    fit_with_gpu_fallback,
    make_pipeline,
    predict_default_proba,
)
from .reporting import default_rate_by_period, reliability_plot
from .selective import conformal_quantile, selective_table, split_conformal_review_mask
from .splits import DEFAULT_ROLE_SPLIT_SHARES, stratified_60_20_20, temporal_60_20_20, temporal_role_split
from .reject_option import (
    DEFAULT_CAPACITY_FRACTIONS,
    DEFAULT_HUMAN_RESIDUAL_RHOS,
    DEFAULT_REVIEW_COSTS,
    DEFAULT_UNCERTAINTY_BANDS,
    CostScenario,
    add_reference_savings,
    capacity_review_mask,
    cost_components,
    evaluate_all_review,
    evaluate_capacity_grid,
    evaluate_no_review,
    evaluate_reject_option,
    evaluate_review_mask_policy,
)
from .utils import describe_command, ensure_dir, log, now_stamp, set_seed, write_json, write_text


@dataclass
class RunConfig:
    output_dir: Path
    raw_dir: Path
    seed: int
    models: list[str]
    n_jobs: int
    rf_estimators: int
    xgb_estimators: int
    use_gpu_xgb: bool
    include_text: bool
    text_max_features: int
    bootstrap: int
    lending_max_rows: int | None = None
    tree_max_train_rows: int | None = None
    reduced_seeds: tuple[int, ...] = (42, 43, 44)


@dataclass
class PredictionRecord:
    dataset: str
    split: str
    model: str
    calibration: str
    y_val: np.ndarray
    probs_val: np.ndarray
    y_test: np.ndarray
    probs_test: np.ndarray
    exposure_val: np.ndarray | None
    exposure_test: np.ndarray | None
    score_for_selection: float


@dataclass
class RolePredictionCandidate:
    dataset: str
    model: str
    calibration: str
    probs_by_role: dict[str, np.ndarray]
    y_by_role: dict[str, np.ndarray]
    exposure_by_role: dict[str, np.ndarray | None]
    selection_metrics: dict[str, float]


def run_lending(config: RunConfig) -> dict[str, object]:
    set_seed(config.seed)
    output_dir = ensure_dir(config.output_dir)
    figures_dir = ensure_dir(output_dir / "figures")

    bundle = load_lending_club(
        raw_dir=config.raw_dir,
        max_rows=config.lending_max_rows,
        include_text=config.include_text,
    )
    log(f"Loaded Lending Club rows={len(bundle.frame)}")

    bundle.audit.to_csv(output_dir / "feature_audit_lending_club.csv", index=False)
    dataset_summary(bundle).to_csv(output_dir / "dataset_summary.csv", index=False)
    default_rate_by_period(
        bundle.timestamp,
        bundle.target,
        figures_dir / "lending_default_rate_by_quarter.png",
    )

    all_metric_rows: list[dict[str, object]] = []
    all_calibration_rows: list[dict[str, object]] = []
    all_decision_frames: list[pd.DataFrame] = []
    all_selective_frames: list[pd.DataFrame] = []
    split_summaries: list[pd.DataFrame] = []
    prediction_records: list[PredictionRecord] = []

    for split_name, indices in _lending_splits(bundle, config.seed):
        train_idx, val_idx, test_idx = indices
        split_summaries.append(
            summarize_splits(
                bundle.name,
                split_name,
                bundle.target.loc[train_idx],
                bundle.target.loc[val_idx],
                bundle.target.loc[test_idx],
                bundle.timestamp.loc[train_idx],
                bundle.timestamp.loc[val_idx],
                bundle.timestamp.loc[test_idx],
            )
        )
        records = _fit_evaluate_split(bundle, split_name, indices, config)
        prediction_records.extend(records)
        for record in records:
            all_calibration_rows.append(
                metrics_row(
                    record.dataset,
                    record.split,
                    record.model,
                    record.calibration,
                    "test",
                    record.y_test,
                    record.probs_test,
                )
            )
            if record.calibration == "raw":
                all_metric_rows.append(
                    metrics_row(
                        record.dataset,
                        record.split,
                        record.model,
                        "raw",
                        "test",
                        record.y_test,
                        record.probs_test,
                    )
                )

    split_summary_frame = pd.concat(split_summaries, ignore_index=True)
    split_summary_frame.to_csv(output_dir / "split_summary.csv", index=False)
    pd.DataFrame(all_metric_rows).to_csv(output_dir / "lending_random_vs_temporal.csv", index=False)
    pd.DataFrame(all_calibration_rows).to_csv(output_dir / "calibration_results.csv", index=False)

    temporal_records = [r for r in prediction_records if r.split == "temporal"]
    best_records = _best_records_by_model(temporal_records)
    log(f"Selected {len(best_records)} temporal records for decisioning")
    for record in best_records:
        log(f"Decisioning {record.dataset}/{record.model}/{record.calibration}")
        decisions = decision_table(
            record.dataset,
            record.split,
            record.model,
            record.calibration,
            record.y_val,
            record.probs_val,
            record.y_test,
            record.probs_test,
            record.exposure_val,
            record.exposure_test,
            DEFAULT_COST_RATIOS,
            DEFAULT_LGDS,
            DEFAULT_ROIS,
        )
        all_decision_frames.append(decisions)
        pd.concat(all_decision_frames, ignore_index=True).to_csv(
            output_dir / "decision_results.csv", index=False
        )

        threshold = robust_cost_threshold(record.y_val, record.probs_val, DEFAULT_COST_RATIOS)
        log(f"Selective decisioning {record.dataset}/{record.model}/{record.calibration}")
        selective = selective_table(
            record.dataset,
            record.split,
            record.model,
            record.calibration,
            record.y_val,
            record.probs_val,
            record.y_test,
            record.probs_test,
            threshold=threshold,
            alphas=DEFAULT_ALPHAS,
            false_negative_cost=5.0,
        )
        all_selective_frames.append(selective)
        pd.concat(all_selective_frames, ignore_index=True).to_csv(
            output_dir / "selective_results.csv", index=False
        )

    if all_decision_frames:
        pd.concat(all_decision_frames, ignore_index=True).to_csv(
            output_dir / "decision_results.csv", index=False
        )
    if all_selective_frames:
        pd.concat(all_selective_frames, ignore_index=True).to_csv(
            output_dir / "selective_results.csv", index=False
        )

    _write_bootstrap(output_dir, best_records, config.bootstrap, config.seed)
    _write_decision_delta_bootstrap(output_dir, best_records, config.bootstrap, config.seed)
    _write_reliability(figures_dir, best_records)

    summary = {
        "command": describe_command(),
        "lending_rows": int(len(bundle.frame)),
        "models": config.models,
        "splits": ["random", "temporal"],
        "best_temporal_records": [
            {
                "model": r.model,
                "calibration": r.calibration,
                "brier": r.score_for_selection,
                "roc_auc": classification_metrics(r.y_test, r.probs_test)["roc_auc"],
                "pr_auc": classification_metrics(r.y_test, r.probs_test)["pr_auc"],
            }
            for r in best_records
        ],
        "output_dir": str(output_dir),
    }
    write_json(output_dir / "experiment_results.json", summary)
    write_tracker(output_dir / "EXPERIMENT_TRACKER.md", summary, output_dir)
    return summary


def run_reject_option_capacity(
    config: RunConfig,
    primary_cost_ratio: float = 5.0,
    primary_review_cost: float = 0.10,
    primary_human_residual_rho: float = 0.10,
) -> dict[str, object]:
    set_seed(config.seed)
    output_dir = ensure_dir(config.output_dir)
    figures_dir = ensure_dir(output_dir / "figures")

    bundle = load_lending_club(
        raw_dir=config.raw_dir,
        max_rows=config.lending_max_rows,
        include_text=config.include_text,
    )
    log(f"Loaded Lending Club rows={len(bundle.frame)} for reject-option/capacity protocol")

    bundle.audit.to_csv(output_dir / "feature_audit_lending_club.csv", index=False)
    dataset_summary(bundle).to_csv(output_dir / "dataset_summary.csv", index=False)
    default_rate_by_period(
        bundle.timestamp,
        bundle.target,
        figures_dir / "lending_default_rate_by_quarter.png",
    )

    role_indices = temporal_role_split(bundle.frame, bundle.timestamp)
    split_summary = _role_split_summary(bundle, role_indices)
    split_summary.to_csv(output_dir / "split_role_summary.csv", index=False)
    _write_selection_protocol(
        output_dir / "selection_protocol.md",
        config,
        primary_cost_ratio,
        primary_review_cost,
        primary_human_residual_rho,
    )

    candidates, raw_rows, selection_rows, final_rows = _fit_role_candidates(
        bundle,
        role_indices,
        config,
    )
    pd.DataFrame(raw_rows).to_csv(output_dir / "model_raw_metrics.csv", index=False)
    selection_frame = pd.DataFrame(selection_rows)
    selection_frame.to_csv(output_dir / "calibration_selection_metrics.csv", index=False)
    pd.DataFrame(final_rows).to_csv(output_dir / "calibration_final_appendix.csv", index=False)

    selected = _select_primary_candidate(candidates)
    primary_source = {
        "dataset": selected.dataset,
        "model": selected.model,
        "calibration": selected.calibration,
        "selected_on": "calibration_select",
        "selection_rule": "lowest Brier; tie-break by ECE then NLL",
        "selection_metrics": selected.selection_metrics,
    }
    write_json(output_dir / "primary_calibrated_source.json", primary_source)
    _write_selected_predictions(
        output_dir / "selected_probability_predictions.csv",
        bundle,
        role_indices,
        selected,
    )
    reliability_plot(
        selected.y_by_role["final_test"],
        {f"{selected.model}-{selected.calibration}": selected.probs_by_role["final_test"]},
        figures_dir / f"reliability_selected_{selected.model}_{selected.calibration}.png",
    )

    interval_summary = _empirical_interval_summary(
        selected.y_by_role,
        selected.probs_by_role,
    )
    interval_summary.to_csv(output_dir / "venn_abers_interval_fallback_summary.csv", index=False)

    primary_scenario = CostScenario(
        false_negative_cost=primary_cost_ratio,
        false_positive_cost=1.0,
        review_cost=primary_review_cost,
        human_residual_rho=primary_human_residual_rho,
    )
    policy_tune = _decision_grid(
        selected.y_by_role["policy_tune"],
        selected.probs_by_role["policy_tune"],
        include_capacity=True,
    )
    policy_tune.insert(0, "partition", "policy_tune")
    policy_tune.to_csv(output_dir / "policy_tune_decision_grid.csv", index=False)

    final_decisions = _final_policy_report(
        selected.y_by_role["final_test"],
        selected.probs_by_role["final_test"],
        selected.y_by_role["risk_calibration"],
        selected.probs_by_role["risk_calibration"],
        primary_scenario,
    )
    final_decisions.insert(0, "partition", "final_test")
    final_decisions.insert(1, "dataset", selected.dataset)
    final_decisions.insert(2, "model", selected.model)
    final_decisions.insert(3, "calibration", selected.calibration)
    final_decisions.to_csv(output_dir / "final_decision_results.csv", index=False)

    capacity_frontier = final_decisions[
        final_decisions["policy"].isin(
            ["no_review_cost_sensitive", "all_review", "cost_aware_reject_option", "capacity_aware_deferral"]
        )
        & (final_decisions["scenario"] == primary_scenario.scenario_id)
    ].copy()
    capacity_frontier.to_csv(output_dir / "capacity_frontier.csv", index=False)
    _capacity_deferred_case_summary(
        selected.y_by_role["final_test"],
        selected.probs_by_role["final_test"],
        primary_scenario,
    ).to_csv(output_dir / "capacity_deferred_case_summary.csv", index=False)

    access_log = pd.DataFrame(
        [
            {
                "timestamp": now_stamp(),
                "partition": "final_test",
                "event": "locked_report_evaluation",
                "note": "Final test used only after model/calibrator/scenario/capacity grid were fixed.",
            }
        ]
    )
    access_log.to_csv(output_dir / "final_test_access_log.csv", index=False)

    summary = {
        "command": describe_command(),
        "lending_rows": int(len(bundle.frame)),
        "models": config.models,
        "tree_max_train_rows": config.tree_max_train_rows,
        "role_split_shares": dict(DEFAULT_ROLE_SPLIT_SHARES),
        "primary_calibrated_source": primary_source,
        "primary_scenario": {
            "false_negative_cost": primary_scenario.false_negative_cost,
            "false_positive_cost": primary_scenario.false_positive_cost,
            "review_cost": primary_scenario.review_cost,
            "human_residual_rho": primary_scenario.human_residual_rho,
        },
        "final_outputs": {
            "split_role_summary": str(output_dir / "split_role_summary.csv"),
            "calibration_selection_metrics": str(output_dir / "calibration_selection_metrics.csv"),
            "final_decision_results": str(output_dir / "final_decision_results.csv"),
            "capacity_frontier": str(output_dir / "capacity_frontier.csv"),
        },
        "output_dir": str(output_dir),
    }
    write_json(output_dir / "reject_capacity_results.json", summary)
    _write_reject_capacity_results_markdown(
        output_dir / "EXPERIMENT_RESULTS.md",
        summary,
        selection_frame,
        final_decisions,
        capacity_frontier,
    )
    _write_reject_capacity_tracker(output_dir / "EXPERIMENT_TRACKER.md", summary)
    return summary


def run_reduced(config: RunConfig) -> dict[str, object]:
    output_dir = ensure_dir(config.output_dir)
    frames: list[pd.DataFrame] = []
    selective_frames: list[pd.DataFrame] = []
    summaries: list[pd.DataFrame] = []

    for loader in [load_uci_default, load_german_credit]:
        bundle = loader(config.raw_dir)
        summaries.append(dataset_summary(bundle))
        for seed in config.reduced_seeds:
            train_idx, val_idx, test_idx = stratified_60_20_20(
                bundle.frame,
                bundle.target,
                seed=seed,
            )
            records = _fit_evaluate_split(
                bundle,
                split_name=f"random_seed_{seed}",
                indices=(train_idx, val_idx, test_idx),
                config=config,
            )
            best = _best_records_by_model(records)
            for record in records:
                row = metrics_row(
                    record.dataset,
                    record.split,
                    record.model,
                    record.calibration,
                    "test",
                    record.y_test,
                    record.probs_test,
                )
                frames.append(pd.DataFrame([row]))
            for record in best:
                threshold = robust_cost_threshold(
                    record.y_val, record.probs_val, DEFAULT_COST_RATIOS
                )
                selective_frames.append(
                    selective_table(
                        record.dataset,
                        record.split,
                        record.model,
                        record.calibration,
                        record.y_val,
                        record.probs_val,
                        record.y_test,
                        record.probs_test,
                        threshold=threshold,
                        alphas=(0.10,),
                        false_negative_cost=5.0,
                    )
                )

                decisions = decision_table(
                    record.dataset,
                    record.split,
                    record.model,
                    record.calibration,
                    record.y_val,
                    record.probs_val,
                    record.y_test,
                    record.probs_test,
                    record.exposure_val,
                    record.exposure_test,
                    DEFAULT_COST_RATIOS,
                    DEFAULT_LGDS,
                    DEFAULT_ROIS,
                )
                decisions["result_family"] = "decision"
                frames.append(decisions)

    if summaries:
        pd.concat(summaries, ignore_index=True).to_csv(
            output_dir / "reduced_dataset_summary.csv", index=False
        )
    result_frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    result_frame.to_csv(output_dir / "reduced_protocol_results.csv", index=False)
    if selective_frames:
        pd.concat(selective_frames, ignore_index=True).to_csv(
            output_dir / "reduced_selective_results.csv", index=False
        )
    summary = {
        "command": describe_command(),
        "datasets": ["uci_default", "german_credit"],
        "seeds": list(config.reduced_seeds),
        "models": config.models,
        "output_dir": str(output_dir),
    }
    write_json(output_dir / "reduced_experiment_results.json", summary)
    return summary


def run_all(config: RunConfig) -> dict[str, object]:
    lending = run_lending(config)
    reduced_output_dir = config.output_dir.with_name(f"{config.output_dir.name}_reduced")
    reduced_config = RunConfig(
        **{
            **config.__dict__,
            "output_dir": reduced_output_dir,
            "bootstrap": 0,
            "use_gpu_xgb": False,
        }
    )
    write_json(
        reduced_output_dir / "run_config.json",
        {
            "command": "run-reduced",
            "config": {
                "output_dir": str(reduced_config.output_dir),
                "raw_dir": str(reduced_config.raw_dir),
                "seed": reduced_config.seed,
                "models": reduced_config.models,
                "n_jobs": reduced_config.n_jobs,
                "rf_estimators": reduced_config.rf_estimators,
                "xgb_estimators": reduced_config.xgb_estimators,
                "use_gpu_xgb": reduced_config.use_gpu_xgb,
                "include_text": reduced_config.include_text,
                "text_max_features": reduced_config.text_max_features,
                "bootstrap": reduced_config.bootstrap,
                "lending_max_rows": reduced_config.lending_max_rows,
                "tree_max_train_rows": reduced_config.tree_max_train_rows,
                "reduced_seeds": list(reduced_config.reduced_seeds),
            },
        },
    )
    reduced = run_reduced(reduced_config)
    summary = {"lending": lending, "reduced": reduced}
    write_json(config.output_dir / "run_all_summary.json", summary)
    return summary


def _fit_role_candidates(
    bundle: DatasetBundle,
    role_indices: dict[str, pd.Index],
    config: RunConfig,
) -> tuple[
    list[RolePredictionCandidate],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    x_all = _feature_frame(bundle)
    y_all = bundle.target.astype(int)
    exposure = bundle.exposure

    x_by_role = {role: x_all.loc[idx] for role, idx in role_indices.items()}
    y_by_role = {role: y_all.loc[idx].to_numpy() for role, idx in role_indices.items()}
    exposure_by_role = {
        role: (exposure.loc[idx].to_numpy() if exposure is not None else None)
        for role, idx in role_indices.items()
    }

    candidates: list[RolePredictionCandidate] = []
    raw_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []

    for spec in build_models(
        config.models,
        seed=config.seed,
        n_jobs=config.n_jobs,
        rf_estimators=config.rf_estimators,
        xgb_estimators=config.xgb_estimators,
        use_gpu_xgb=config.use_gpu_xgb,
    ):
        log(f"Training role-split model lending_club/{spec.name}")
        preprocessor = build_preprocessor(
            bundle.numeric_features,
            bundle.categorical_features,
            bundle.text_feature,
            config.text_max_features,
        )
        pipeline = make_pipeline(preprocessor, spec.estimator)
        fit_x, fit_y = _fit_subset(
            x_by_role["model_train"],
            y_by_role["model_train"],
            spec.name,
            config.tree_max_train_rows,
            config.seed,
        )
        pipeline = fit_with_gpu_fallback(pipeline, fit_x, fit_y)
        raw_probs_by_role = {
            role: predict_default_proba(pipeline, x_role)
            for role, x_role in x_by_role.items()
            if role != "model_train"
        }

        for role in ["model_dev", "calibration_fit", "calibration_select"]:
            raw_rows.append(
                metrics_row(
                    bundle.name,
                    "chronological_role",
                    spec.name,
                    "raw",
                    role,
                    y_by_role[role],
                    raw_probs_by_role[role],
                )
            )

        calibrators = fit_calibrators(
            y_by_role["calibration_fit"],
            raw_probs_by_role["calibration_fit"],
        )
        for cal_name, calibrator in calibrators.items():
            probs_by_role = {
                role: calibrator.transform(raw_probs)
                for role, raw_probs in raw_probs_by_role.items()
            }
            select_metrics = classification_metrics(
                y_by_role["calibration_select"],
                probs_by_role["calibration_select"],
            )
            selection_row = metrics_row(
                bundle.name,
                "chronological_role",
                spec.name,
                cal_name,
                "calibration_select",
                y_by_role["calibration_select"],
                probs_by_role["calibration_select"],
            )
            selection_rows.append(selection_row)
            final_rows.append(
                metrics_row(
                    bundle.name,
                    "chronological_role",
                    spec.name,
                    cal_name,
                    "final_test",
                    y_by_role["final_test"],
                    probs_by_role["final_test"],
                )
            )
            candidates.append(
                RolePredictionCandidate(
                    dataset=bundle.name,
                    model=spec.name,
                    calibration=cal_name,
                    probs_by_role=probs_by_role,
                    y_by_role=y_by_role,
                    exposure_by_role=exposure_by_role,
                    selection_metrics=select_metrics,
                )
            )
        del pipeline, fit_x, fit_y, raw_probs_by_role
        gc.collect()
    return candidates, raw_rows, selection_rows, final_rows


def _select_primary_candidate(candidates: list[RolePredictionCandidate]) -> RolePredictionCandidate:
    if not candidates:
        raise ValueError("No calibrated candidates were produced.")

    def key(candidate: RolePredictionCandidate) -> tuple[float, float, float, str, str]:
        metrics = candidate.selection_metrics
        return (
            _finite_or_inf(metrics.get("brier", np.inf)),
            _finite_or_inf(metrics.get("ece", np.inf)),
            _finite_or_inf(metrics.get("nll", np.inf)),
            candidate.model,
            candidate.calibration,
        )

    selected = min(candidates, key=key)
    log(
        "Selected primary calibrated source "
        f"{selected.model}/{selected.calibration} on calibration_select "
        f"Brier={selected.selection_metrics.get('brier'):.6f}"
    )
    return selected


def _finite_or_inf(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("inf")
    return number if np.isfinite(number) else float("inf")


def _role_split_summary(bundle: DatasetBundle, role_indices: dict[str, pd.Index]) -> pd.DataFrame:
    rows = []
    for role, idx in role_indices.items():
        y = bundle.target.loc[idx].astype(int)
        timestamp = bundle.timestamp.loc[idx] if bundle.timestamp is not None else None
        row = {
            "dataset": bundle.name,
            "partition": role,
            "rows": int(len(idx)),
            "default_rate": float(np.mean(y)),
            "n_default": int(np.sum(y)),
            "n_non_default": int(len(y) - np.sum(y)),
            "allowed_uses": _role_allowed_use(role),
        }
        if timestamp is not None:
            row["start_date"] = str(pd.Series(timestamp).min().date())
            row["end_date"] = str(pd.Series(timestamp).max().date())
        rows.append(row)
    return pd.DataFrame(rows)


def _role_allowed_use(role: str) -> str:
    return {
        "model_train": "model fitting only",
        "model_dev": "early stopping and model hyperparameter sanity only",
        "calibration_fit": "calibration fitting only",
        "calibration_select": "primary calibrated source selection only",
        "policy_tune": "policy scenario diagnostics and non-conformal policy tuning only",
        "risk_calibration": "split conformal and risk-control calibration only",
        "final_test": "one-shot locked final report only",
    }.get(role, "")


def _write_selection_protocol(
    path: Path,
    config: RunConfig,
    primary_cost_ratio: float,
    primary_review_cost: float,
    primary_human_residual_rho: float,
) -> None:
    cap_note = (
        "No tree training row cap is configured."
        if config.tree_max_train_rows is None
        else (
            f"Tree training cap is configured at {config.tree_max_train_rows}; "
            "outputs must be labelled as sanity or appendix-only, not final main-table evidence."
        )
    )
    text = f"""# Reject-Option Capacity Selection Protocol

Date: {now_stamp()}

## Frozen Role Split

Chronological non-overlapping partitions use these shares: {dict(DEFAULT_ROLE_SPLIT_SHARES)}.

## Pre-Registered Model And Calibration Rule

- Candidate models: {config.models}
- Calibrators: raw, sigmoid/Platt, isotonic.
- Primary calibrated probability source is selected on `calibration_select`.
- Selection objective: lowest Brier score, with ECE then NLL as tie-breakers.
- `final_test` is not used for model, calibrator, threshold, scenario, or capacity selection.
- {cap_note}

## Pre-Registered Decision Settings

- Cost ratios FN:FP: {DEFAULT_COST_RATIOS}:1
- Review costs: {DEFAULT_REVIEW_COSTS}
- Human residual rho values: {DEFAULT_HUMAN_RESIDUAL_RHOS}
- Capacity fractions: {DEFAULT_CAPACITY_FRACTIONS}
- Primary scenario: FN:FP={primary_cost_ratio:g}:1, c_R={primary_review_cost:g}, rho={primary_human_residual_rho:g}

## Final-Test Gate

The locked final report may read `final_test` once after the primary calibrated source and primary scenario are fixed. Any post-test method change needs a new frozen run label.
"""
    write_text(path, text)


def _write_selected_predictions(
    path: Path,
    bundle: DatasetBundle,
    role_indices: dict[str, pd.Index],
    selected: RolePredictionCandidate,
) -> None:
    frames = []
    for role, probs in selected.probs_by_role.items():
        idx = role_indices[role]
        frame = pd.DataFrame(
            {
                "row_id": idx.to_numpy(),
                "partition": role,
                "y_true": selected.y_by_role[role],
                "prob_default": probs,
                "model": selected.model,
                "calibration": selected.calibration,
                "selection_status": "primary_selected",
            }
        )
        if bundle.timestamp is not None:
            frame["issue_d"] = bundle.timestamp.loc[idx].to_numpy()
        frames.append(frame)
    pd.concat(frames, ignore_index=True).to_csv(path, index=False)


def _empirical_interval_summary(
    y_by_role: dict[str, np.ndarray],
    probs_by_role: dict[str, np.ndarray],
    n_bins: int = 20,
) -> pd.DataFrame:
    y_fit = np.asarray(y_by_role["calibration_fit"], dtype=int)
    probs_fit = np.asarray(probs_by_role["calibration_fit"], dtype=float)
    edges = np.unique(np.quantile(probs_fit, np.linspace(0.0, 1.0, n_bins + 1)))
    if len(edges) < 3:
        edges = np.linspace(0.0, 1.0, min(n_bins, 5) + 1)
    edges[0] = 0.0
    edges[-1] = 1.0
    fit_bins = np.searchsorted(edges[1:-1], probs_fit, side="right")
    bin_stats = {}
    z = 1.96
    for bin_id in range(len(edges) - 1):
        mask = fit_bins == bin_id
        n = int(np.sum(mask))
        if n == 0:
            rate = float(np.mean(y_fit))
            lower = 0.0
            upper = 1.0
        else:
            rate = float(np.mean(y_fit[mask]))
            denom = 1.0 + z * z / n
            centre = rate + z * z / (2.0 * n)
            margin = z * np.sqrt((rate * (1.0 - rate) + z * z / (4.0 * n)) / n)
            lower = max(0.0, (centre - margin) / denom)
            upper = min(1.0, (centre + margin) / denom)
        bin_stats[bin_id] = (rate, lower, upper)

    rows = []
    for role in ["calibration_select", "policy_tune", "risk_calibration", "final_test"]:
        probs = np.asarray(probs_by_role[role], dtype=float)
        bins = np.searchsorted(edges[1:-1], probs, side="right")
        mids = np.asarray([bin_stats[int(b)][0] for b in bins])
        lowers = np.asarray([bin_stats[int(b)][1] for b in bins])
        uppers = np.asarray([bin_stats[int(b)][2] for b in bins])
        row = metrics_row(
            "lending_club",
            "chronological_role",
            "selected",
            "empirical_interval_midpoint",
            role,
            y_by_role[role],
            mids,
        )
        row.update(
            {
                "requested_method": "venn_abers",
                "implemented_method": "empirical_binomial_interval_fallback",
                "interval_width_mean": float(np.mean(uppers - lowers)),
                "interval_lower_mean": float(np.mean(lowers)),
                "interval_upper_mean": float(np.mean(uppers)),
                "note": "Fallback interval summary; install a Venn-Abers implementation before claiming formal Venn-Abers guarantees.",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _decision_grid(
    y_true: np.ndarray,
    probs: np.ndarray,
    include_capacity: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for ratio in DEFAULT_COST_RATIOS:
        for review_cost in DEFAULT_REVIEW_COSTS:
            for rho in DEFAULT_HUMAN_RESIDUAL_RHOS:
                scenario = CostScenario(
                    false_negative_cost=ratio,
                    false_positive_cost=1.0,
                    review_cost=review_cost,
                    human_residual_rho=rho,
                )
                rows.append(evaluate_no_review(y_true, probs, scenario))
                rows.append(evaluate_all_review(y_true, probs, scenario))
                rows.append(evaluate_reject_option(y_true, probs, scenario))
                if include_capacity:
                    rows.extend(evaluate_capacity_grid(y_true, probs, scenario))
    return add_reference_savings(pd.DataFrame(rows))


def _final_policy_report(
    y_final: np.ndarray,
    probs_final: np.ndarray,
    y_risk_cal: np.ndarray,
    probs_risk_cal: np.ndarray,
    primary_scenario: CostScenario,
) -> pd.DataFrame:
    base = _decision_grid(y_final, probs_final, include_capacity=True)
    baseline_rows: list[dict[str, object]] = []
    threshold = primary_scenario.false_positive_cost / (
        primary_scenario.false_negative_cost + primary_scenario.false_positive_cost
    )

    for band in DEFAULT_UNCERTAINTY_BANDS:
        review_mask = np.abs(probs_final - threshold) <= band
        baseline_rows.append(
            evaluate_review_mask_policy(
                y_final,
                probs_final,
                primary_scenario,
                "uncertainty_band",
                review_mask,
                extra={"band": band},
            )
        )

    for alpha in DEFAULT_ALPHAS:
        q_hat = conformal_quantile(y_risk_cal, probs_risk_cal, alpha)
        review_mask, include_non_default, include_default = split_conformal_review_mask(
            probs_final,
            q_hat,
            threshold,
        )
        true_in_set = ((y_final == 0) & include_non_default) | (
            (y_final == 1) & include_default
        )
        baseline_rows.append(
            evaluate_review_mask_policy(
                y_final,
                probs_final,
                primary_scenario,
                "split_conformal",
                review_mask,
                extra={
                    "alpha": alpha,
                    "q_hat": q_hat,
                    "coverage": float(np.mean(true_in_set)),
                },
            )
        )

    for target in (primary_scenario.review_cost, primary_scenario.review_cost * 2.0):
        review_mask, tau = _empirical_risk_control_review_mask(
            probs_risk_cal,
            probs_final,
            primary_scenario,
            target,
        )
        baseline_rows.append(
            evaluate_review_mask_policy(
                y_final,
                probs_final,
                primary_scenario,
                "empirical_conformal_risk_control",
                review_mask,
                extra={"target_auto_expected_cost": target, "risk_threshold": tau},
            )
        )

    if baseline_rows:
        combined = pd.concat([base, pd.DataFrame(baseline_rows)], ignore_index=True)
        return add_reference_savings(combined)
    return base


def _empirical_risk_control_review_mask(
    probs_cal: np.ndarray,
    probs_eval: np.ndarray,
    scenario: CostScenario,
    target_mean_auto_cost: float,
) -> tuple[np.ndarray, float]:
    approve_cal, deny_cal, _ = cost_components(probs_cal, scenario)
    auto_cost_cal = np.minimum(approve_cal, deny_cal)
    thresholds = np.unique(np.quantile(auto_cost_cal, np.linspace(0.05, 1.0, 96)))
    chosen = float(np.min(thresholds))
    for tau in thresholds:
        automated = auto_cost_cal <= tau
        if np.any(automated) and float(np.mean(auto_cost_cal[automated])) <= target_mean_auto_cost:
            chosen = float(tau)
    approve_eval, deny_eval, _ = cost_components(probs_eval, scenario)
    auto_cost_eval = np.minimum(approve_eval, deny_eval)
    return auto_cost_eval > chosen, chosen


def _capacity_deferred_case_summary(
    y_true: np.ndarray,
    probs: np.ndarray,
    scenario: CostScenario,
) -> pd.DataFrame:
    rows = []
    approve_cost, deny_cost, manual_cost = cost_components(probs, scenario)
    benefit = np.minimum(approve_cost, deny_cost) - manual_cost
    for fraction in DEFAULT_CAPACITY_FRACTIONS:
        review_mask = capacity_review_mask(probs, scenario, fraction)
        rows.append(
            {
                "capacity_fraction": fraction,
                "review_rate": float(np.mean(review_mask)),
                "mean_review_benefit": _safe_mean(benefit[review_mask]),
                "mean_prob_default_reviewed": _safe_mean(probs[review_mask]),
                "default_rate_reviewed": _safe_mean(y_true[review_mask]),
                "mean_prob_default_not_reviewed": _safe_mean(probs[~review_mask]),
                "default_rate_not_reviewed": _safe_mean(y_true[~review_mask]),
            }
        )
    return pd.DataFrame(rows)


def _safe_mean(values: np.ndarray) -> float:
    if len(values) == 0:
        return float("nan")
    return float(np.mean(values))


def _write_reject_capacity_results_markdown(
    path: Path,
    summary: dict[str, object],
    selection_frame: pd.DataFrame,
    final_decisions: pd.DataFrame,
    capacity_frontier: pd.DataFrame,
) -> None:
    primary = summary["primary_calibrated_source"]
    selected_rows = selection_frame.sort_values(["brier", "ece", "nll"]).head(5)
    primary_scenario = summary["primary_scenario"]
    scenario_id = CostScenario(
        primary_scenario["false_negative_cost"],
        primary_scenario["false_positive_cost"],
        primary_scenario["review_cost"],
        primary_scenario["human_residual_rho"],
    ).scenario_id
    main_rows = final_decisions[final_decisions["scenario"] == scenario_id].copy()
    text = [
        "# Initial Reject-Option Capacity Results",
        "",
        f"Date: {now_stamp()}",
        f"Output directory: `{summary['output_dir']}`",
        "",
        "## Primary Calibrated Source",
        "",
        f"- Model: `{primary['model']}`",
        f"- Calibration: `{primary['calibration']}`",
        "- Selected on: `calibration_select` by Brier, ECE, then NLL.",
        "",
        "## Top Calibration Candidates On Calibration-Select",
        "",
        _frame_to_markdown(selected_rows[
            ["model", "calibration", "brier", "ece", "nll", "roc_auc", "pr_auc"]
        ]),
        "",
        "## Primary Scenario Final-Test Policies",
        "",
        _frame_to_markdown(main_rows[
            [
                "policy",
                "capacity_fraction",
                "expected_cost",
                "realized_cost",
                "review_rate",
                "automation_rate",
                "savings_vs_no_review",
                "savings_vs_all_review",
            ]
        ]),
        "",
        "## Capacity Frontier",
        "",
        _frame_to_markdown(capacity_frontier[
            [
                "policy",
                "capacity_fraction",
                "expected_cost",
                "review_rate",
                "savings_vs_no_review",
            ]
        ]),
        "",
        "## Status",
        "",
        "- M0 protocol split and selection protocol: DONE.",
        "- M1/M2 calibrated PD source: DONE for configured models.",
        "- M3/M4 reject-option and capacity-aware deferral: DONE for selected source.",
        "- M5 conformal risk-control: empirical variant only; do not claim formal finite-sample guarantee.",
    ]
    write_text(path, "\n".join(text))


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


def _write_reject_capacity_tracker(path: Path, summary: dict[str, object]) -> None:
    models = {str(model).lower() for model in summary.get("models", [])}
    full_model_set = {"lr", "lgbm", "xgb"}.issubset(models)
    no_tree_cap = summary.get("tree_max_train_rows") is None
    model_status = "DONE" if full_model_set and no_tree_cap else "PARTIAL"
    model_note = (
        "Full-row LR, LightGBM, and XGBoost completed without tree training caps."
        if model_status == "DONE"
        else "Completed for configured models; final main evidence still needs LR, LightGBM, and XGBoost without row caps."
    )
    lines = [
        "# Reject-Option And Capacity-Aware Experiment Tracker",
        "",
        f"Updated: {now_stamp()}",
        f"Output directory: `{summary['output_dir']}`",
        "",
        "| Run ID | Milestone | Status | Notes |",
        "|---|---|---|---|",
        "| R001 | M0 | DONE | `split_role_summary.csv` written with chronological role partitions. |",
        "| R002 | M0 | DONE | `selection_protocol.md` pre-registers source selection, costs, capacity grid, and final-test gate. |",
        "| R003 | M0 | DONE | `selection_protocol.md` records whether tree training caps are absent or appendix-only. |",
        "| R004 | M0 | DONE | `final_test_access_log.csv` records locked final-test evaluation. |",
        f"| R101-R103 | M1 | {model_status} | {model_note} |",
        "| R201-R204 | M2 | DONE | Calibration fit/select/final appendix outputs written. |",
        "| R301-R305 | M3 | DONE | No-review, all-review, reject-option, uncertainty, conformal, and scenario-grid outputs written. |",
        "| R401-R405 | M4 | DONE | Capacity grid, frontier, and deferred-case diagnostics written. |",
        "| R501-R504 | M5 | PARTIAL | Split conformal baseline and empirical risk-control variant written; formal conformal guarantee not claimed. |",
        "| R601-R604 | M6 | PENDING | Requires claim audit and dissertation writing handoff after full no-cap run. |",
    ]
    write_text(path, "\n".join(lines))


def _lending_splits(
    bundle: DatasetBundle,
    seed: int,
) -> Iterable[tuple[str, tuple[pd.Index, pd.Index, pd.Index]]]:
    yield "random", stratified_60_20_20(bundle.frame, bundle.target, seed)
    yield "temporal", temporal_60_20_20(bundle.frame, bundle.timestamp)


def _feature_frame(bundle: DatasetBundle) -> pd.DataFrame:
    columns = [*bundle.numeric_features, *bundle.categorical_features]
    if bundle.text_feature:
        columns.append(bundle.text_feature)
    return bundle.frame.loc[:, columns].copy()


def _fit_evaluate_split(
    bundle: DatasetBundle,
    split_name: str,
    indices: tuple[pd.Index, pd.Index, pd.Index],
    config: RunConfig,
) -> list[PredictionRecord]:
    train_idx, val_idx, test_idx = indices
    x_all = _feature_frame(bundle)
    y_all = bundle.target.astype(int)
    exposure = bundle.exposure

    x_train = x_all.loc[train_idx]
    x_val = x_all.loc[val_idx]
    x_test = x_all.loc[test_idx]
    y_train = y_all.loc[train_idx].to_numpy()
    y_val = y_all.loc[val_idx].to_numpy()
    y_test = y_all.loc[test_idx].to_numpy()
    exposure_val = exposure.loc[val_idx].to_numpy() if exposure is not None else None
    exposure_test = exposure.loc[test_idx].to_numpy() if exposure is not None else None

    records: list[PredictionRecord] = []
    for spec in build_models(
        config.models,
        seed=config.seed,
        n_jobs=config.n_jobs,
        rf_estimators=config.rf_estimators,
        xgb_estimators=config.xgb_estimators,
        use_gpu_xgb=config.use_gpu_xgb,
    ):
        log(f"Training {bundle.name}/{split_name}/{spec.name}")
        preprocessor = build_preprocessor(
            bundle.numeric_features,
            bundle.categorical_features,
            bundle.text_feature,
            config.text_max_features,
        )
        pipeline = make_pipeline(preprocessor, spec.estimator)
        fit_x, fit_y = _fit_subset(
            x_train,
            y_train,
            spec.name,
            config.tree_max_train_rows,
            config.seed,
        )
        pipeline = fit_with_gpu_fallback(pipeline, fit_x, fit_y)
        probs_val_raw = predict_default_proba(pipeline, x_val)
        probs_test_raw = predict_default_proba(pipeline, x_test)
        calibrators = fit_calibrators(y_val, probs_val_raw)
        for cal_name, calibrator in calibrators.items():
            probs_val = calibrator.transform(probs_val_raw)
            probs_test = calibrator.transform(probs_test_raw)
            brier = classification_metrics(y_val, probs_val)["brier"]
            records.append(
                PredictionRecord(
                    dataset=bundle.name,
                    split=split_name,
                    model=spec.name,
                    calibration=cal_name,
                    y_val=y_val,
                    probs_val=probs_val,
                    y_test=y_test,
                    probs_test=probs_test,
                    exposure_val=exposure_val,
                    exposure_test=exposure_test,
                    score_for_selection=brier,
                )
            )
        del pipeline, fit_x, fit_y, probs_val_raw, probs_test_raw
        gc.collect()
    return records


def _fit_subset(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    model_name: str,
    max_rows: int | None,
    seed: int,
) -> tuple[pd.DataFrame, np.ndarray]:
    if max_rows is None or model_name not in {"rf", "xgb", "lgbm"}:
        return x_train, y_train
    if len(x_train) <= max_rows:
        return x_train, y_train
    from sklearn.model_selection import train_test_split

    sampled_idx, _ = train_test_split(
        np.arange(len(y_train)),
        train_size=max_rows,
        random_state=seed,
        stratify=y_train,
    )
    sampled_idx = np.sort(sampled_idx)
    log(f"Using stratified fit subset for {model_name}: {len(sampled_idx)}/{len(y_train)} rows")
    return x_train.iloc[sampled_idx], y_train[sampled_idx]


def _best_records_by_model(records: list[PredictionRecord]) -> list[PredictionRecord]:
    best: dict[str, PredictionRecord] = {}
    for record in records:
        current = best.get(record.model)
        if current is None or record.score_for_selection < current.score_for_selection:
            best[record.model] = record
    return list(best.values())


def _write_bootstrap(
    output_dir: Path,
    records: list[PredictionRecord],
    n_bootstrap: int,
    seed: int,
) -> None:
    if n_bootstrap <= 0:
        return
    rows = []
    for record in records:
        y_boot, probs_boot = _bootstrap_subset(record.y_test, record.probs_test, max_rows=50_000)
        log(f"Bootstrap CI {record.dataset}/{record.model}/{record.calibration} rows={len(y_boot)}")
        for metric_name, metric_func in [
            ("roc_auc", lambda y, p: classification_metrics(y, p)["roc_auc"]),
            ("brier", lambda y, p: classification_metrics(y, p)["brier"]),
            (
                "expected_cost_5_to_1_fixed_0.5",
                lambda y, p: cost_metrics(y, p, 0.5, 5.0)["expected_cost"],
            ),
        ]:
            row = bootstrap_ci(
                y_boot,
                probs_boot,
                metric_name,
                metric_func,
                n_bootstrap=n_bootstrap,
                seed=seed,
            )
            row.update(
                {
                    "dataset": record.dataset,
                    "split": record.split,
                    "model": record.model,
                    "calibration": record.calibration,
                    "n_bootstrap": n_bootstrap,
                }
            )
            rows.append(row)
    pd.DataFrame(rows).to_csv(output_dir / "bootstrap_ci.csv", index=False)


def _write_decision_delta_bootstrap(
    output_dir: Path,
    records: list[PredictionRecord],
    n_bootstrap: int,
    seed: int,
) -> None:
    if n_bootstrap <= 0:
        return
    rows = []
    for record in records:
        idx = _bootstrap_subset_indices(len(record.y_test), max_rows=50_000)
        y_test = record.y_test[idx]
        probs_test = record.probs_test[idx]

        fixed_costs = cost_values(y_test, probs_test, 0.5, false_negative_cost=5.0)
        cost5_threshold = cost_threshold(5.0)
        cost5_costs = cost_values(
            y_test,
            probs_test,
            cost5_threshold,
            false_negative_cost=5.0,
        )
        robust_threshold = robust_cost_threshold(
            record.y_val,
            record.probs_val,
            DEFAULT_COST_RATIOS,
        )
        robust_costs = cost_values(
            y_test,
            probs_test,
            robust_threshold,
            false_negative_cost=5.0,
        )

        q_hat = conformal_quantile(record.y_val, record.probs_val, alpha=0.10)
        full_review_mask, _, _ = split_conformal_review_mask(
            record.probs_test,
            q_hat,
            robust_threshold,
        )
        review_mask = full_review_mask[idx]
        conformal_costs = cost_values(
            y_test,
            probs_test,
            robust_threshold,
            false_negative_cost=5.0,
            review_mask=review_mask,
            review_cost=0.10,
        )

        comparisons = [
            ("cost_5_to_1_minus_fixed_0.5", fixed_costs, cost5_costs, cost5_threshold),
            (
                "split_conformal_alpha_0.10_review_0.10_minus_robust_cost",
                robust_costs,
                conformal_costs,
                robust_threshold,
            ),
            (
                "split_conformal_alpha_0.10_review_0.10_minus_cost_5_to_1",
                cost5_costs,
                conformal_costs,
                robust_threshold,
            ),
        ]
        for metric_name, baseline, candidate, threshold in comparisons:
            row = paired_bootstrap_delta_ci(
                baseline,
                candidate,
                metric_name,
                n_bootstrap=n_bootstrap,
                seed=seed,
            )
            row.update(
                {
                    "dataset": record.dataset,
                    "split": record.split,
                    "model": record.model,
                    "calibration": record.calibration,
                    "n_bootstrap": n_bootstrap,
                    "rows": len(y_test),
                    "threshold": threshold,
                    "delta_direction": "candidate_minus_baseline; negative means lower expected cost",
                }
            )
            rows.append(row)
    pd.DataFrame(rows).to_csv(output_dir / "decision_delta_ci.csv", index=False)


def _bootstrap_subset(
    y_test: np.ndarray,
    probs_test: np.ndarray,
    max_rows: int,
) -> tuple[np.ndarray, np.ndarray]:
    if len(y_test) <= max_rows:
        return y_test, probs_test
    idx = _bootstrap_subset_indices(len(y_test), max_rows)
    return y_test[idx], probs_test[idx]


def _bootstrap_subset_indices(n_rows: int, max_rows: int) -> np.ndarray:
    if n_rows <= max_rows:
        return np.arange(n_rows)
    rng = np.random.default_rng(1)
    idx = rng.choice(n_rows, size=max_rows, replace=False)
    idx.sort()
    return idx


def _write_reliability(figures_dir: Path, records: list[PredictionRecord]) -> None:
    for record in records:
        reliability_plot(
            record.y_test,
            {f"{record.model}-{record.calibration}": record.probs_test},
            figures_dir / f"reliability_{record.model}_{record.calibration}.png",
        )


def write_tracker(path: Path, summary: dict[str, object], output_dir: Path) -> None:
    best_rows = summary.get("best_temporal_records", [])
    lines = [
        "# Experiment Tracker",
        "",
        f"Updated: {now_stamp()}",
        f"Output directory: `{output_dir}`",
        "",
        "| Block | Status | Notes |",
        "|---|---|---|",
        "| B0 Dataset audit | DONE | `feature_audit_lending_club.csv`, `dataset_summary.csv`, `split_summary.csv` written. |",
        "| B1 Random vs temporal | DONE | `lending_random_vs_temporal.csv` written for configured models. |",
        "| B2 Calibration | DONE | `calibration_results.csv` written. |",
        "| B3 Profit/cost decisioning | DONE | `decision_results.csv` written for temporal best calibrations. |",
        "| B4 Selective decisioning | DONE | `selective_results.csv` written for conformal and uncertainty-band review. |",
        "| B5 Reduced protocol | PENDING | Run `python -m dcred.cli run-reduced` or `run-all`. |",
        "| B6 Bootstrap CI | DONE | `bootstrap_ci.csv` written when `--bootstrap > 0`. |",
        "",
        "## Best Temporal Calibration Records",
        "",
        "```json",
        json.dumps(best_rows, indent=2),
        "```",
        "",
    ]
    write_text(path, "\n".join(lines))
