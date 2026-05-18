# D-CRED

Deployment-Ready Credit Risk Evaluation and Decisioning.

This repository implements the experiment plan in
`D:\code\diss_codex\refine-logs\EXPERIMENT_PLAN.md`.

## What It Runs

- Lending Club feature audit and leakage-free application-time protocol.
- Random 60/20/20 versus temporal 60/20/20 Lending Club evaluation.
- Logistic Regression, Random Forest-style LightGBM RF, and XGBoost/LightGBM tabular baselines.
- Raw, sigmoid/Platt, and isotonic probability calibration.
- Fixed, F1, cost-sensitive, profit-sensitive, and robust thresholds.
- Split-conformal and uncertainty-band selective credit decisioning.
- Reduced-protocol UCI Default and German Credit experiments.
- Bootstrap confidence intervals for key metrics and decision-cost deltas.

## Data Sources

- Lending Club granting dataset: Zenodo record `10.5281/zenodo.11295916`.
- UCI Default of Credit Card Clients: UCI dataset id `350`.
- Statlog German Credit Data: UCI dataset id `144`.

Raw files are downloaded into `data/raw/`, which is intentionally ignored by git.

## Quick Sanity Run

```powershell
.\scripts\run_sanity.ps1
```

This runs LR only on a 5k-row Lending Club subset and writes outputs to
`outputs/sanity/`.

## Full Run

```powershell
.\scripts\run_full_experiment.ps1
```

The full run uses all Lending Club rows and then runs reduced-protocol datasets
in a sibling `_reduced` output directory. XGBoost is launched with `--use-gpu-xgb`
for Lending Club so it uses CUDA when the installed build supports GPU training.
The reduced UCI/German stage runs with CPU XGBoost for stability on the local
Windows laptop setup.

For memory-heavy tree baselines, `--tree-max-train-rows` can fit RF/XGB on a
stratified subset while still evaluating on the full validation and test splits.
The provided full-run script uses a conservative 50k cap for local stability on
the 8GB 4060 laptop setup.

The `rf` model name uses LightGBM's random-forest boosting mode because sklearn's
RandomForest hard-exited on the full sparse Lending Club design matrix in this
Windows environment.

## Review-Round Outputs

The latest auto-review fix run is `outputs/review_round1_fix/`. It keeps the
original Lending protocol but corrects selective review cost to use the planned
false-positive-cost basis and writes `decision_delta_ci.csv`.

Aggregated review artifacts are under `review-stage/`, including reduced-protocol
summary tables and `ROUND1_FIX_SUMMARY.md`.

## Scope Limits

- Temporal results show a changed deployment environment, not uniformly worse
  AUC than random splits.
- Split-conformal decisioning is currently a conservative, review-heavy risk
  control layer rather than a high-automation deployment win.
- Reviewed cases are modeled as incurring review cost only; residual manual-review
  error is not estimated in the current experiments.
- On Lending Club, split conformal at the reported operating point behaves mostly
  as approve-or-review: about 91% review, about 8-9% automatic approval, and near
  zero automatic rejection.
- RF/XGB use a stratified 50k fit cap for local stability; evaluation still uses
  the full validation/test splits.
- Validation data are reused for calibration, threshold selection, and conformal
  quantile estimation, so final writing should state this protocol limitation.
