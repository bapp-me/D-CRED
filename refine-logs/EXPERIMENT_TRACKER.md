# Experiment Tracker

Date: 2026-05-04

Plan: `D:\code\diss_codex\refine-logs\EXPERIMENT_PLAN.md`

## Deployment

- Local GPU detected: NVIDIA GeForce RTX 4060 Laptop GPU.
- Data downloaded:
  - Lending Club granting dataset from Zenodo.
  - UCI Default of Credit Card Clients.
  - Statlog German Credit.
- Main Lending run:
  - Output: `D:\code\diss_codex\D-CRED\outputs\full`
  - Log: `D:\code\diss_codex\D-CRED\logs\full-20260504-002800.out.log`
  - Command used XGBoost CUDA: `--use-gpu-xgb`
- Reduced protocol run:
  - Output: `D:\code\diss_codex\D-CRED\outputs\full_reduced`
  - Reduced datasets were run with CPU XGBoost after GPU XGBoost interrupted the small-data reduced stage.

## Block Status

| Block | Status | Artifact |
|---|---:|---|
| B0 Dataset audit | DONE | `outputs/full/feature_audit_lending_club.csv`, `dataset_summary.csv`, `split_summary.csv` |
| B1 Random vs temporal benchmark | DONE | `outputs/full/lending_random_vs_temporal.csv` |
| B2 Calibration | DONE | `outputs/full/calibration_results.csv` |
| B3 Profit/cost decision layer | DONE | `outputs/full/decision_results.csv` |
| B4 Selective decisioning | DONE | `outputs/full/selective_results.csv` |
| B5 UCI/German reduced protocol | DONE | `outputs/full_reduced/reduced_protocol_results.csv`, `reduced_selective_results.csv` |
| B6 Bootstrap CIs | DONE | `outputs/full/bootstrap_ci.csv` |

## Key Lending Results

Temporal raw metrics:

| Model | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| LR | 0.6725 | 0.3445 | 0.2221 |
| RF-style LightGBM | 0.6620 | 0.3387 | 0.2207 |
| XGB | 0.6720 | 0.3491 | 0.1621 |

Best temporal calibration by Brier:

| Model | Calibration | ROC-AUC | PR-AUC | Brier | ECE |
|---|---|---:|---:|---:|---:|
| LR | isotonic | 0.6724 | 0.3429 | 0.1598 | 0.0044 |
| RF-style LightGBM | isotonic | 0.6619 | 0.3355 | 0.1610 | 0.0050 |
| XGB | isotonic | 0.6719 | 0.3457 | 0.1597 | 0.0038 |

Cost-sensitive decisioning at FN:FP = 5:1:

| Model | Fixed 0.5 Cost | Cost Threshold Cost | Robust Cost Policy Cost |
|---|---:|---:|---:|
| LR | 1.0656 | 0.6645 | 0.7249 |
| RF-style LightGBM | 1.0797 | 0.6767 | 0.7328 |
| XGB | 1.0753 | 0.6656 | 0.7112 |

Split conformal at alpha=0.10 and review cost multiplier=0.10:

| Model | Coverage | Automation | Review | Approved Default Rate | Expected Cost |
|---|---:|---:|---:|---:|---:|
| LR | 0.8984 | 0.0934 | 0.9066 | 0.0647 | 0.4835 |
| RF-style LightGBM | 0.9006 | 0.0779 | 0.9221 | 0.0614 | 0.4850 |
| XGB | 0.8974 | 0.0904 | 0.9096 | 0.0603 | 0.4821 |

## Implementation Notes

- The default `lr` baseline is `SGDClassifier(loss="log_loss")`, a scalable linear logistic model for the full 1.35M-row sparse design matrix.
- The `rf` label uses LightGBM random-forest mode because sklearn RandomForest hard-exited on the full sparse Lending Club setup.
- RF/XGB fitting uses a stratified 50k training cap for local stability; validation, calibration, testing, decisions, selective review, and CIs use the full split data unless explicitly noted.
- Bootstrap CIs use a deterministic 50k test-observation subset to keep the full run stable in the local background process.
