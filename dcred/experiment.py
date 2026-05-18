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
from .splits import stratified_60_20_20, temporal_60_20_20
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
