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
