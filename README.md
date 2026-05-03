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
- Bootstrap confidence intervals for key metrics.

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

The full run uses all Lending Club rows and reduced-protocol datasets. XGBoost is
launched with `--use-gpu-xgb` so it uses CUDA when the installed build supports
GPU training. If GPU training is unavailable, the implementation falls back to
CPU XGBoost and records the warning in the log.

For memory-heavy tree baselines, `--tree-max-train-rows` can fit RF/XGB on a
stratified subset while still evaluating on the full validation and test splits.
The provided full-run script uses a conservative 50k cap for local stability on
the 8GB 4060 laptop setup.

The `rf` model name uses LightGBM's random-forest boosting mode because sklearn's
RandomForest hard-exited on the full sparse Lending Club design matrix in this
Windows environment.
