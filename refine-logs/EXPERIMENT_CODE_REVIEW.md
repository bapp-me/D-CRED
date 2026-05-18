# Experiment Code Review

Date: 2026-05-03

Mode: `[local-only]`

The experiment-bridge skill requests a secondary Codex reviewer when available. In this run, reviewer delegation was not used because the active tool policy only permits sub-agents when the user explicitly asks for sub-agent or parallel agent work. I applied the same checklist locally before full deployment.

## Scope Reviewed

- `dcred/data.py`: dataset download, target parsing, Lending Club feature audit, UCI/German loaders.
- `dcred/splits.py`: random 60/20/20 and temporal 60/20/20 splits.
- `dcred/modeling.py`: preprocessing, LR/RF/XGB/LightGBM estimators, XGBoost GPU fallback, Windows single-job fallback.
- `dcred/calibration.py`: raw, sigmoid/Platt-style, and isotonic calibration fitted on validation only.
- `dcred/decision.py`: fixed, F1, cost, profit, and robust thresholds.
- `dcred/selective.py`: uncertainty-band and split-conformal selective decisioning.
- `dcred/experiment.py`: orchestration, outputs, bootstrap CIs, tracker.

## Blocking Checks

- Ground-truth evaluation: PASS. Metrics, calibration losses, decision costs, conformal coverage, and bootstrap intervals all compare predictions against dataset labels `y_val` or `y_test`, never another model output.
- Temporal leakage: PASS. `issue_d` is used for sorting/splitting and summaries only, not as a model feature.
- Identifier leakage: PASS. `id` and UCI `ID` are excluded from feature matrices.
- Calibration leakage: PASS. Calibrators are fitted on validation probabilities and labels, then applied to test probabilities.
- Test tuning leakage: PASS. F1, robust cost, and robust profit thresholds are selected on validation data; test is only used for final reporting.
- Parseable outputs: PASS. Main outputs are CSV and JSON under `outputs/<run-name>/`.
- Reproducibility: PASS. CLI exposes seed, model list, estimator counts, bootstrap count, max rows, text feature option, GPU XGBoost flag, and output paths.

## Fixes Applied During Sanity

- Added a single-job fallback in `fit_with_gpu_fallback` after Windows sandbox rejected joblib parallel pipe creation.
- Updated sanity script to run with `--n-jobs 1`.
- Fixed `_safe_metric` so keyword arguments such as `labels=[0, 1]` are passed to `log_loss`.
- Updated PowerShell launch scripts to exit with the Python process exit code.
- Switched the `lr` baseline from batch `LogisticRegression(saga)` to `SGDClassifier(loss="log_loss")` after the full 1.35M-row sparse design matrix caused hard process exits without Python traceback. This remains a linear logistic-regression baseline and is more appropriate for the full Lending Club scale.
- Added `--tree-max-train-rows` for RF/XGB/LightGBM. This applies only to model fitting for memory-heavy tree baselines; validation, calibration, temporal testing, decision metrics, and bootstrap CIs still use the full split data.
- Set the full-run script to a conservative 50k tree-model training cap with 100 RF trees and 300 XGB trees after sklearn RF still hard-exited at a 200k sparse one-hot fit subset. This is a local stability guard; the output config records the cap.
- Replaced the `rf` implementation with LightGBM `boosting_type="rf"` after sklearn RF still hard-exited on a second full-split fit with a 50k cap. The experiment label remains `rf`, but the README and this review record document that it is a Random Forest-style LightGBM RF baseline.
- Bootstrap CIs now use a deterministic 50k test-observation subset when the full test split is larger. This keeps the uncertainty estimate tied to test labels while avoiding repeated 269k-row scans in the local background process.
- Reduced-protocol UCI/German experiments were completed in a separate CPU-XGBoost run (`outputs/full_reduced`) because GPU XGBoost interrupted the small-data reduced stage after Lending Club results were already written.

## Non-Blocking Notes

- Text fields are excluded from the default tabular benchmark and documented in the feature audit. The CLI supports `--include-text` for a text-augmented variant.
- Full Lending Club XGBoost with sparse one-hot features may exceed 8GB GPU memory. The implementation tries CUDA when `--use-gpu-xgb` is set and falls back to CPU XGBoost if the GPU build or memory path fails.
- The full run can be time-consuming; `outputs/sanity/` confirms the complete pipeline works before deployment.

## Teacher Review P0/P1 Supplement Review

Date: 2026-05-18

Mode: `[local-only]`

The experiment-bridge skill requests a secondary reviewer when available. The active tool policy still permits sub-agents only when explicitly requested, so I applied the review checklist locally for `scripts/teacher_review_p1_analysis.py` before the full P1 run.

### Blocking Checks

- Ground-truth evaluation: PASS. The new drift and sensitivity analyses use `bundle.target`, existing result CSV labels/metrics, or recomputed temporal test labels; they do not compare against another model's output as ground truth.
- No test-set tuning: PASS. The recomputed selective diagnostics choose calibration and robust thresholds from validation records, then report on test records.
- Scope control: PASS. The script implements the teacher-review P0/P1 blocks only: protocol audit, temporal drift, selective tradeoffs, manual-review stress, and cost/profit consolidation. It does not add new datasets or production-bank claims.
- Parseable outputs: PASS. Every analysis table is written as CSV, with Markdown summaries and fixed/latest output paths for dissertation handoff.
- Claim control: PASS. The generated summary explicitly keeps C1 as a bounded temporal-setting claim, C3 as the strongest cost-threshold claim, and C4 as review-heavy risk-control evidence.

## Reject-Option Capacity Protocol Review

Date: 2026-05-19

Mode: `[local-only]`

The new experiment plan requires a cleaner empirical protocol: full-row model training, non-overlapping chronological partitions, pre-test calibrator selection, and a cost/capacity decision layer. Reviewer delegation was not used because the active tool policy only permits sub-agents when the user explicitly asks for sub-agent or parallel agent work, so I applied the experiment-bridge checklist locally.

### Scope Reviewed

- `dcred/splits.py`: seven-way chronological role split.
- `dcred/reject_option.py`: no-review, all-review, cost-aware reject option, top-B capacity deferral, and savings calculations.
- `dcred/experiment.py`: `run_reject_option_capacity`, calibration selection, final-test gate outputs, capacity frontier reporting, and empirical risk-control baseline.
- `dcred/cli.py`: `run-reject-capacity` command and primary scenario arguments.
- `scripts/run_reject_capacity_sanity.ps1`: small sanity-stage launch command.

### Blocking Checks

- Ground-truth evaluation: PASS. Calibration metrics, policy rates, realized costs, conformal coverage, and deferred-cohort diagnostics compare against Lending Club labels. Capacity ranking itself uses only calibrated probabilities and cost assumptions.
- Role separation: PASS. `model_train`, `model_dev`, `calibration_fit`, `calibration_select`, `policy_tune`, `risk_calibration`, and `final_test` are non-overlapping chronological partitions.
- Calibration selection: PASS. The primary calibrated source is selected only on `calibration_select` using Brier with ECE/NLL tie-breaks.
- Final-test tuning leakage: PASS. Final-test outputs are generated after model/calibrator/scenario/capacity settings are fixed and an access log is written.
- No capped main evidence: PASS for `outputs/reject_capacity_full`; LR, LightGBM, and XGBoost were run without `--tree-max-train-rows`.
- Parseable outputs: PASS. Split summaries, calibration metrics, policy grids, capacity frontier, selected probabilities, JSON summary, and Markdown results are written under `outputs/reject_capacity_full`.

### Non-Blocking Notes

- Venn-Abers is not a formal implementation in this patch. The output `venn_abers_interval_fallback_summary.csv` is explicitly labelled as an empirical binomial interval fallback and must not be claimed as a formal Venn-Abers guarantee.
- The conformal risk-control variant is empirical. The generated report keeps it as a baseline/risk diagnostic and does not claim finite-sample control.
- XGBoost CUDA completed, but prediction emitted the known device-mismatch warning and fell back to DMatrix prediction. This affects prediction path efficiency, not the label-based evaluation logic.
